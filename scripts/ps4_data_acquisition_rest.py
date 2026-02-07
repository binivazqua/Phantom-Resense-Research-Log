import sys
import time
import json
import atexit
import threading
import subprocess
from collections import deque
from pathlib import Path
from dataclasses import dataclass

import numpy as np
from pylsl import StreamInlet, resolve_streams

import pygame
import dearpygui.dearpygui as dpg

# =========================
# CONFIG
# =========================
GESTURE_WINDOW_S = 1.0   # duración del estado UP/LEFT/RIGHT
MUSE_MAC = "00:55:da:b5:b3:1e"
WAIT_AFTER_START_S = 8
STREAM_SEARCH_TIMEOUT_S = 40

CHANNEL_NAMES = ["TP9", "AF7", "AF8", "TP10"]
N_CH_EXPECTED = 4

# Buffer (en segundos) para poder recortar ventanas alrededor del evento
RING_BUFFER_SECONDS = 20.0

# Ventana de evento: toma muestras de [t_event - PRE, t_event + POST]
EVENT_PRE_S = 0.25
EVENT_POST_S = 0.85

# Autosave continuo: cada cuánto flush a disco
FLUSH_EVERY_S = 1.0

# Dataset root
DATA_DIR = Path("./eeg_rest_datasets")

# PS4 button mapping (pygame joystick button indices)
# Nota: estos índices pueden variar según SO/driver. Si no coincide, te digo cómo calibrarlo.
BTN_CROSS = 0     # ✕
BTN_CIRCLE = 1    # ○
BTN_SQUARE = 2    # □
BTN_TRIANGLE = 3  # △
BTN_OPTIONS = 9   # Options

LABEL_MAP = {
    BTN_TRIANGLE: "UP_i",
    BTN_SQUARE: "LEFT_i",
    BTN_CIRCLE: "RIGHT_i",
    BTN_CROSS: "REST_i",
}

# UI refresh
UI_FPS = 30
PLOT_WINDOW_S = 5.0  # ventana visible del plot

# =========================
# Helpers
# =========================
def now_str():
    return time.strftime("%Y%m%d_%H%M%S")

def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def resolve_eeg_inlet(timeout_s=STREAM_SEARCH_TIMEOUT_S) -> StreamInlet:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        streams = resolve_streams(wait_time=2)
        for s in streams:
            stype = (s.type() or "").lower()
            sname = (s.name() or "").lower()
            if (stype == "eeg") or ("eeg" in stype) or ("/muse/eeg" in sname) or (("muse" in sname) and ("eeg" in sname)):
                return StreamInlet(s, max_buflen=60)
    raise RuntimeError("No se encontró stream LSL EEG.")

# =========================
# MuseLSL process manager
# =========================
class MuseStreamer:
    def __init__(self, mac: str):
        self.mac = mac
        self.proc = None

    def start(self):
        if self.proc is not None and self.proc.poll() is None:
            return
        python_exe = sys.executable
        cmd = [python_exe, "-m", "muselsl", "stream", "-a", self.mac]
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

        def _reader():
            if self.proc.stdout is None:
                return
            for _line in self.proc.stdout:
                # Si quieres debug, descomenta:
                # print("[muselsl]", _line.rstrip())
                pass

        threading.Thread(target=_reader, daemon=True).start()

    def stop(self):
        if self.proc is None:
            return
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()

# =========================
# Data model
# =========================
@dataclass
class EventRecord:
    event_id: int
    label: str
    t_event_lsl: float
    n_samples: int

class EEGRecorder:
    def __init__(self):
        self.label_lock = threading.Lock()
        self.current_label = "REST_i"
        self.label_until_lsl = None  # cuando expira el gesto (tiempo LSL)
        self.labeled_stream_path = None

        self.inlet: StreamInlet | None = None
        self.fs: float = 256.0
        self.n_ch: int = N_CH_EXPECTED

        # ring buffer
        self.t_lsl = deque()
        self.y = [deque() for _ in range(N_CH_EXPECTED)]

        self.buffer_lock = threading.Lock()

        # runtime state
        self.is_running = False
        self.is_recording = False
        self.session_id = None
        self.session_dir: Path | None = None

        self.cont_files = {}   # channel -> file handle
        self.cont_paths = {}   # channel -> path
        self.events_path: Path | None = None
        self.markers_path: Path | None = None
        self.meta_path: Path | None = None

        self.samples_total = 0
        self.dropouts = 0

        self.event_id = 0
        self.event_counts = {"REST_i": 0, "UP_i": 0, "LEFT_i": 0, "RIGHT_i": 0}

        self.last_flush_time = 0.0
        self.last_event_time_wall = 0.0
        self.event_cooldown_s = 0.6

        # UI
        self.focus_channel = 3  # TP10 default

    def trigger_gesture_window(self, label: str):
        if not self.is_recording:
            return
        with self.buffer_lock:
            if len(self.t_lsl) < 2:
                return
            t_now = float(self.t_lsl[-1])  # tiempo LSL más reciente

        with self.label_lock:
            self.current_label = label
            self.label_until_lsl = t_now + GESTURE_WINDOW_S


    def connect(self):
        inlet = resolve_eeg_inlet()
        info = inlet.info()
        fs = float(info.nominal_srate() or 256.0)
        n_ch = int(info.channel_count() or N_CH_EXPECTED)

        self.inlet = inlet
        self.fs = fs
        self.n_ch = n_ch

        # size ring buffer
        maxlen = int(RING_BUFFER_SECONDS * self.fs)

        with self.buffer_lock:
            self.t_lsl = deque(maxlen=maxlen)
            self.y = [deque(maxlen=maxlen) for _ in range(N_CH_EXPECTED)]
            # prefill deques to avoid empty plot
            for _ in range(int(self.fs * 1.0)):
                self.t_lsl.append(0.0)
                for ch in range(N_CH_EXPECTED):
                    self.y[ch].append(0.0)

        return fs, n_ch

    def start_stream_loop(self):
        if self.inlet is None:
            raise RuntimeError("Primero conecta inlet.")
        if self.is_running:
            return
        self.is_running = True
        threading.Thread(target=self._acq_loop, daemon=True).start()

    def _acq_loop(self):
        # Pull chunks continuously
        while self.is_running:
            try:
                chunk, ts = self.inlet.pull_chunk(timeout=1, max_samples=max(512, int(self.fs // 10)))
            except Exception:
                self.dropouts += 1
                continue

            if ts and chunk:
                chunk = np.asarray(chunk, dtype=np.float32)
                ts = np.asarray(ts, dtype=np.float64)
                # safety: ensure we have at least 4 channels
                if chunk.shape[1] < N_CH_EXPECTED:
                    # count dropout-like
                    self.dropouts += 1
                    continue

                with self.buffer_lock:
                    for k in range(len(ts)):
                        self.t_lsl.append(float(ts[k]))
                        for ch in range(N_CH_EXPECTED):
                            self.y[ch].append(float(chunk[k, ch]))

                self.samples_total += len(ts)

                # Auto-return a REST_i cuando expire la ventana del gesto
                with self.label_lock:
                    if self.label_until_lsl is not None:
                        t_now = float(ts[-1])
                        if t_now >= self.label_until_lsl:
                            self.current_label = "REST_i"
                            self.label_until_lsl = None


                # continuous write
                if self.is_recording:
                    self._continuous_write(ts, chunk[:, :N_CH_EXPECTED])

            else:
                # no data
                pass

    def _open_session_files(self):
        
        safe_mkdir(DATA_DIR)
        self.session_id = f"REST_{now_str()}"
        self.session_dir = DATA_DIR / self.session_id
        safe_mkdir(self.session_dir)
        self.labeled_stream_path = self.session_dir / "labeled_stream.csv"
        if not self.labeled_stream_path.exists():
            with open(self.labeled_stream_path, "w", encoding="utf-8") as f:
                f.write("label,t_lsl,TP9,AF7,AF8,TP10\n")

        # Continuous per-channel CSV: t_lsl,value
        self.cont_files = {}
        self.cont_paths = {}
        for idx, name in enumerate(CHANNEL_NAMES):
            p = self.session_dir / f"continuous_{name}.csv"
            f = open(p, "a", encoding="utf-8")
            if p.stat().st_size == 0:
                f.write("t_lsl,value\n")
                f.flush()
            self.cont_files[idx] = f
            self.cont_paths[idx] = p

        # Events CSV (one row per sample, includes label + event_id)
        self.events_path = self.session_dir / "events_samples.csv"
        if not self.events_path.exists():
            with open(self.events_path, "w", encoding="utf-8") as f:
                f.write("event_id,label,t_event_lsl,t_lsl,TP9,AF7,AF8,TP10\n")

        # Markers: one row per event (summary)
        self.markers_path = self.session_dir / "markers.csv"
        if not self.markers_path.exists():
            with open(self.markers_path, "w", encoding="utf-8") as f:
                f.write("event_id,label,t_event_lsl,n_samples\n")

        # Meta
        self.meta_path = self.session_dir / "meta.json"
        meta = {
            "session_id": self.session_id,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "muse_mac": MUSE_MAC,
            "fs_nominal": self.fs,
            "channels_expected": CHANNEL_NAMES,
            "event_window_pre_s": EVENT_PRE_S,
            "event_window_post_s": EVENT_POST_S,
            "ring_buffer_seconds": RING_BUFFER_SECONDS,
        }
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def start_recording(self):
        if self.is_recording:
            return
        self._open_session_files()
        self.is_recording = True
        self.last_flush_time = time.time()

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        # close files
        for f in self.cont_files.values():
            try:
                f.flush()
                f.close()
            except Exception:
                pass
        self.cont_files = {}
        self.cont_paths = {}

        # Update meta with stats
        if self.meta_path:
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                meta = {}
            meta.update({
                "stopped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "samples_total": self.samples_total,
                "dropouts": self.dropouts,
                "event_counts": self.event_counts,
            })
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

    def shutdown(self):
        self.is_running = False
        self.stop_recording()

    def _continuous_write(self, ts: np.ndarray, data_4ch: np.ndarray):
        # write per channel; flush periodically
        for i in range(len(ts)):
            t = float(ts[i])
            for ch in range(N_CH_EXPECTED):
                f = self.cont_files.get(ch)
                if f is not None:
                    f.write(f"{t:.6f},{float(data_4ch[i, ch]):.6f}\n")
        # Continuous labeled stream (REST por defecto + ventanas de gesto)
        with self.label_lock:
            label = self.current_label

        with open(self.labeled_stream_path, "a", encoding="utf-8") as f:
            for i in range(len(ts)):
                f.write(
                    f"{label},{float(ts[i]):.6f},"
                    f"{float(data_4ch[i,0]):.6f},{float(data_4ch[i,1]):.6f},"
                    f"{float(data_4ch[i,2]):.6f},{float(data_4ch[i,3]):.6f}\n"
                )


        now = time.time()
        if now - self.last_flush_time >= FLUSH_EVERY_S:
            self.last_flush_time = now
            for f in self.cont_files.values():
                try:
                    f.flush()
                except Exception:
                    pass

    def mark_event(self, label: str):
        # cooldown to avoid double marks
        noww = time.time()
        if noww - self.last_event_time_wall < self.event_cooldown_s:
            return
        self.last_event_time_wall = noww

        if not self.is_recording:
            return

        # get t_event from last sample in buffer
        with self.buffer_lock:
            if len(self.t_lsl) < 5:
                return
            t_event = float(self.t_lsl[-1])
            t0 = t_event - EVENT_PRE_S
            t1 = t_event + EVENT_POST_S

            # extract window indices from ring buffer
            t_arr = np.asarray(self.t_lsl, dtype=np.float64)
            # indices within [t0, t1]
            mask = (t_arr >= t0) & (t_arr <= t1)
            if not np.any(mask):
                return

            idxs = np.where(mask)[0]
            # extract per channel
            y_arr = [np.asarray(self.y[ch], dtype=np.float32) for ch in range(N_CH_EXPECTED)]

        # Write samples to events_samples.csv
        self.event_id += 1
        eid = self.event_id

        with open(self.events_path, "a", encoding="utf-8") as f:
            for j in idxs:
                row = [
                    str(eid),
                    label,
                    f"{t_event:.6f}",
                    f"{float(t_arr[j]):.6f}",
                    f"{float(y_arr[0][j]):.6f}",
                    f"{float(y_arr[1][j]):.6f}",
                    f"{float(y_arr[2][j]):.6f}",
                    f"{float(y_arr[3][j]):.6f}",
                ]
                f.write(",".join(row) + "\n")

        # Marker summary
        with open(self.markers_path, "a", encoding="utf-8") as f:
            f.write(f"{eid},{label},{t_event:.6f},{len(idxs)}\n")

        # counters
        if label in self.event_counts:
            self.event_counts[label] += 1

    def get_plot_data(self):
        # Return last PLOT_WINDOW_S seconds of focus channel
        with self.buffer_lock:
            t = np.asarray(self.t_lsl, dtype=np.float64)
            y = np.asarray(self.y[self.focus_channel], dtype=np.float32)

        if len(t) < 5:
            return np.array([0.0, 1.0]), np.array([0.0, 0.0])

        t_end = t[-1]
        t_start = t_end - PLOT_WINDOW_S
        m = t >= t_start
        tt = t[m]
        yy = y[m]

        # convert to relative (0..window)
        if len(tt) > 0:
            tt = tt - tt[-1]
        return tt, yy

# =========================
# PS4 Controller Thread
# =========================
class PS4Controller:
    def __init__(self, recorder: EEGRecorder, status_cb):
        self.recorder = recorder
        self.status_cb = status_cb
        self.running = False
        self.joy = None

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        pygame.init()
        pygame.joystick.init()

        # Try attach first joystick
        while self.running and self.joy is None:
            try:
                if pygame.joystick.get_count() > 0:
                    self.joy = pygame.joystick.Joystick(0)
                    self.joy.init()
                    self.status_cb(f"PS4 conectado: {self.joy.get_name()}")
                else:
                    self.status_cb("Conecta el control PS4 (USB/Bluetooth)...")
            except Exception:
                self.status_cb("Error inicializando joystick.")
            time.sleep(0.5)

        while self.running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        b = int(event.button)

                        if b == BTN_OPTIONS:
                            # toggle recording
                            if self.recorder.is_recording:
                                self.recorder.stop_recording()
                                self.status_cb("Recording: OFF")
                            else:
                                self.recorder.start_recording()
                                self.status_cb("Recording: ON")
                            continue

                        if b in LABEL_MAP:
                            label = LABEL_MAP[b]
                            if b in LABEL_MAP:
                                label = LABEL_MAP[b]
                                if label == "REST_i":
                                    # fuerza REST inmediato
                                    with self.recorder.label_lock:
                                        self.recorder.current_label = "REST_i"
                                        self.recorder.label_until_lsl = None
                                    self.status_cb("Estado actual: REST_i")
                                else:
                                    self.recorder.trigger_gesture_window(label)
                                    self.status_cb(f"Gesto: {label} ({GESTURE_WINDOW_S:.1f}s) -> REST_i")

                            self.status_cb(f"Evento marcado: {label}")
            except Exception:
                # keep running
                pass

            time.sleep(0.01)

# =========================
# UI (Dear PyGui)
# =========================
def run_ui():
    streamer = MuseStreamer(MUSE_MAC)
    rec = EEGRecorder()

    ui_state = {
        "status": "Listo.",
        "connected": False,
        "fs": None,
        "nch": None,
    }

    def set_status(msg: str):
        ui_state["status"] = msg
        if dpg.does_item_exist("status_text"):
            dpg.set_value("status_text", msg)

    def on_connect():
        try:
            streamer.start()
            set_status(f"muselsl stream started, esperando {WAIT_AFTER_START_S}s...")
            time.sleep(WAIT_AFTER_START_S)

            fs, nch = rec.connect()
            rec.start_stream_loop()

            ui_state["connected"] = True
            ui_state["fs"] = fs
            ui_state["nch"] = nch

            set_status(f"EEG conectado: fs≈{fs:.1f}Hz, ch={nch}.")
        except Exception as e:
            set_status(f"Error conectando: {e}")

    def on_start_rec():
        if not ui_state["connected"]:
            set_status("Primero conecta EEG.")
            return
        rec.start_recording()
        set_status("Recording: ON (Options para toggle).")

    def on_stop_rec():
        rec.stop_recording()
        set_status("Recording: OFF.")

    def on_channel_change(sender, app_data):
        # app_data is selected string
        name = app_data
        idx = CHANNEL_NAMES.index(name)
        rec.focus_channel = idx
        set_status(f"Canal foco: {name}")

    def ui_tick():
        # Update plot
        tt, yy = rec.get_plot_data()
        if dpg.does_item_exist("series"):
            dpg.set_value("series", [tt.tolist(), yy.tolist()])

        # Update counters + stats
        if dpg.does_item_exist("counters"):
            c = rec.event_counts
            txt = (
                f"REST_i: {c['REST_i']}   "
                f"UP_i: {c['UP_i']}   "
                f"LEFT_i: {c['LEFT_i']}   "
                f"RIGHT_i: {c['RIGHT_i']}"
            )
            dpg.set_value("counters", txt)

        if dpg.does_item_exist("stats"):
            dpg.set_value(
                "stats",
                f"samples: {rec.samples_total}   dropouts: {rec.dropouts}   recording: {rec.is_recording}"
            )

    # Build UI
    dpg.create_context()

    # Apple-ish minimal theme (soft dark)
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 16)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 14)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 10)

    dpg.bind_theme(global_theme)

    with dpg.window(tag="primary", label="X-Chair • EEG Rest Capture", width=980, height=620):
        dpg.add_text("EEG Rest Capture", color=(230, 230, 230))
        dpg.add_text("Muse 2 • LSL • PS4 Markers • Autosave por canal", color=(160, 160, 160))
        dpg.add_spacer(height=8)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Conectar EEG", width=140, callback=lambda: threading.Thread(target=on_connect, daemon=True).start())
            dpg.add_button(label="Start Recording", width=160, callback=on_start_rec)
            dpg.add_button(label="Stop Recording", width=160, callback=on_stop_rec)

            dpg.add_spacer(width=10)
            dpg.add_text("Canal foco:", color=(160, 160, 160))
            dpg.add_combo(CHANNEL_NAMES, default_value="TP10", width=120, callback=on_channel_change)

        dpg.add_spacer(height=10)
        dpg.add_text(ui_state["status"],tag="status_text",color=(200, 200, 200))

        dpg.add_spacer(height=10)

        with dpg.child_window(height=120, border=True):
            dpg.add_text("Marcaje PS4 (JOYBUTTONDOWN):", color=(160, 160, 160))
            dpg.add_text("△ = UP_i   □ = LEFT_i   ○ = RIGHT_i   ✕ = REST_i   Options = Toggle Recording", color=(220, 220, 220))
            dpg.add_spacer(height=6)
            dpg.add_text("REST_i: 0   UP_i: 0   LEFT_i: 0   RIGHT_i: 0",tag="counters",color=(220, 220, 220))
            dpg.add_text("samples: 0   dropouts: 0   recording: False", tag="stats",color=(160, 160, 160))


        dpg.add_spacer(height=10)

        with dpg.child_window(border=True):
            dpg.add_text("Señal en vivo (canal foco, últimos 5s)", color=(160, 160, 160))
            with dpg.plot(height=300, width=-1, anti_aliased=True):
                dpg.add_plot_legend()
                xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="t (rel)")
                yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="uV (raw)")
                dpg.add_line_series([0, 1], [0, 0], label="EEG", parent=yaxis, tag="series")

        dpg.add_spacer(height=8)
        dpg.add_text("Datos se guardan en ./eeg_rest_datasets/REST_YYYYMMDD_HHMMSS/", color=(140, 140, 140))

    dpg.create_viewport(title="EEG Rest Capture", width=1000, height=680)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary", True)

    # PS4 controller background
    controller = PS4Controller(recorder=rec, status_cb=set_status)
    controller.start()

    # Cleanup
    def cleanup():
        controller.stop()
        rec.shutdown()
        streamer.stop()

    atexit.register(cleanup)

    # Main loop
    last_ui = time.time()
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
        now = time.time()
        if now - last_ui >= (1.0 / UI_FPS):
            last_ui = now
            ui_tick()

    cleanup()
    dpg.destroy_context()

if __name__ == "__main__":
    run_ui()
