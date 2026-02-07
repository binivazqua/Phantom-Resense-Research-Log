"""
Captura de Artefactos Faciales para Adultos Mayores
========================================================
Interfaz simple y clara para recopilar datos EEG durante:
- Parpadeo ojo derecho
- Parpadeo ojo izquierdo
- Levantar cejas
- Períodos de reposo

Características:
- Retroalimentación visual GRANDE y clara
- Señales de audio para cada acción
- Controles de teclado para marcado manual
- Auto-guardado continuo de datos
"""

import sys
import time
import json
import threading
import subprocess
import atexit
from pathlib import Path
from collections import deque
from dataclasses import dataclass

import numpy as np
from pylsl import StreamInlet, resolve_streams
import dearpygui.dearpygui as dpg

try:
    import pyttsx3
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️  pyttsx3 not available. Install with: pip install pyttsx3")

# =========================
# CONFIG
# =========================
MUSE_MAC = "00:55:da:b5:b3:1e"
WAIT_AFTER_START_S = 8
STREAM_SEARCH_TIMEOUT_S = 40

CHANNEL_NAMES = ["TP9", "AF7", "AF8", "TP10"]
N_CH = 4

# Trial configuration
ACTION_DURATION_S = 3.0      # How long to perform each action
REST_DURATION_S = 4.0         # Rest between actions
COUNTDOWN_DURATION_S = 2.0    # Countdown before starting action

# Actions to cycle through
ACTIONS = [
    ("REPOSO", "Relájese y respire normalmente"),
    ("PARPADEO_DERECHO", "Parpadee con el ojo DERECHO varias veces"),
    ("PARPADEO_IZQUIERDO", "Parpadee con el ojo IZQUIERDO varias veces"),
    ("LEVANTAR_CEJAS", "Levante las cejas hacia arriba y abajo"),
]

# Keyboard shortcuts
KEYS_MAP = {
    dpg.mvKey_D: "PARPADEO_DERECHO",
    dpg.mvKey_I: "PARPADEO_IZQUIERDO", 
    dpg.mvKey_C: "LEVANTAR_CEJAS",
    dpg.mvKey_Spacebar: "REPOSO",
}

# Data storage
DATA_DIR = Path("./facial_artifact_datasets")
FLUSH_EVERY_S = 2.0

# Ring buffer
RING_BUFFER_SECONDS = 10.0

# =========================
# Helpers
# =========================
def now_str():
    return time.strftime("%Y%m%d_%H%M%S")

def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def resolve_eeg_inlet(timeout_s=STREAM_SEARCH_TIMEOUT_S) -> StreamInlet:
    """Find and connect to Muse EEG stream"""
    print(f"🔍 Buscando stream EEG (timeout: {timeout_s}s)...")
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        streams = resolve_streams(wait_time=2)
        for s in streams:
            stype = (s.type() or "").lower()
            sname = (s.name() or "").lower()
            if "eeg" in stype or "muse" in sname:
                print(f"✅ Stream encontrado: {s.name()}")
                return StreamInlet(s, max_buflen=60)
    raise RuntimeError("❌ No se encontró stream LSL EEG.")

# =========================
# Audio Cue Manager
# =========================
class AudioCueManager:
    """Handles text-to-speech audio cues"""
    
    def __init__(self):
        self.enabled = AUDIO_AVAILABLE
        self.engine = None
        self.lock = threading.Lock()
        
        if self.enabled:
            try:
                self.engine = pyttsx3.init()
                # Configure voice (slower rate for elderly)
                self.engine.setProperty('rate', 130)  # Slower speech for elderly
                self.engine.setProperty('volume', 1.0)
                
                # Try to use a Spanish or clear voice
                voices = self.engine.getProperty('voices')
                if voices:
                    # Prefer Spanish voice, then female voice (often clearer)
                    spanish_voice = None
                    female_voice = None
                    
                    for voice in voices:
                        voice_name = voice.name.lower()
                        voice_lang = getattr(voice, 'languages', [])
                        
                        # Check for Spanish
                        if 'spanish' in voice_name or 'es' in str(voice_lang) or 'español' in voice_name:
                            spanish_voice = voice.id
                            break
                        # Check for clear female voices
                        elif 'female' in voice_name or 'samantha' in voice_name or 'monica' in voice_name:
                            female_voice = voice.id
                    
                    # Set Spanish voice if found, otherwise female, otherwise default
                    if spanish_voice:
                        self.engine.setProperty('voice', spanish_voice)
                        print("🔊 Voz en español encontrada")
                    elif female_voice:
                        self.engine.setProperty('voice', female_voice)
                        print("🔊 Voz clara seleccionada")
                        
            except Exception as e:
                print(f"⚠️  Error de inicialización de audio: {e}")
                self.enabled = False
    
    def speak(self, text: str):
        """Speak text asynchronously"""
        if not self.enabled:
            return
        
        def _speak():
            with self.lock:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"⚠️  Audio error: {e}")
        
        threading.Thread(target=_speak, daemon=True).start()
    
    def speak_action(self, action: str):
        """Speak action instruction"""
        messages = {
            "REPOSO": "Reposo. Relájese y respire normalmente.",
            "PARPADEO_DERECHO": "Parpadeo ojo derecho. Parpadee con el ojo derecho varias veces.",
            "PARPADEO_IZQUIERDO": "Parpadeo ojo izquierdo. Parpadee con el ojo izquierdo varias veces.",
            "LEVANTAR_CEJAS": "Levantar cejas. Levante las cejas hacia arriba y abajo.",
        }
        
        msg = messages.get(action, action)
        self.speak(msg)
    
    def speak_countdown(self, seconds: int):
        """Speak countdown number"""
        self.speak(str(seconds))
    
    def speak_ready(self):
        """Speak 'get ready' message"""
        self.speak("Prepárese")

# =========================
# Muse Streamer
# =========================
class MuseStreamer:
    """Manages muselsl stream process"""
    
    def __init__(self, mac: str):
        self.mac = mac
        self.proc = None
    
    def start(self):
        """Start muselsl stream subprocess"""
        if self.proc is not None and self.proc.poll() is None:
            return
        
        python_exe = sys.executable
        cmd = [python_exe, "-m", "muselsl", "stream", "-a", self.mac]
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, bufsize=1
        )
        
        def _reader():
            if self.proc.stdout is None:
                return
            for _line in self.proc.stdout:
                pass  # Silent output
        
        threading.Thread(target=_reader, daemon=True).start()
    
    def stop(self):
        """Stop the stream process"""
        if self.proc is None:
            return
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()

# =========================
# EEG Recorder
# =========================
class EEGRecorder:
    """Handles EEG data acquisition and storage"""
    
    def __init__(self):
        self.inlet: StreamInlet | None = None
        self.fs: float = 256.0
        
        # Ring buffer for recent data
        self.buffer_lock = threading.Lock()
        self.t_lsl = deque()
        self.y = [deque() for _ in range(N_CH)]
        
        # Current state
        self.current_label = "REPOSO"
        self.label_lock = threading.Lock()
        
        # Recording state
        self.is_running = False
        self.is_recording = False
        
        # Session info
        self.session_id = None
        self.session_dir: Path | None = None
        self.data_file = None
        self.data_path: Path | None = None
        self.meta_path: Path | None = None
        
        # Stats
        self.samples_total = 0
        self.dropouts = 0
        self.last_flush_time = 0.0
        
        # Event tracking
        self.event_counts = {
            "REPOSO": 0,
            "PARPADEO_DERECHO": 0,
            "PARPADEO_IZQUIERDO": 0,
            "LEVANTAR_CEJAS": 0
        }
    
    def connect(self):
        """Connect to EEG stream"""
        inlet = resolve_eeg_inlet()
        info = inlet.info()
        fs = float(info.nominal_srate() or 256.0)
        
        self.inlet = inlet
        self.fs = fs
        
        # Initialize ring buffer
        maxlen = int(RING_BUFFER_SECONDS * self.fs)
        with self.buffer_lock:
            self.t_lsl = deque(maxlen=maxlen)
            self.y = [deque(maxlen=maxlen) for _ in range(N_CH)]
            
            # Prefill with zeros
            for _ in range(int(self.fs)):
                self.t_lsl.append(0.0)
                for ch in range(N_CH):
                    self.y[ch].append(0.0)
        
        print(f"✅ EEG conectado: fs={fs:.1f} Hz")
        return fs
    
    def start_stream_loop(self):
        """Start background acquisition loop"""
        if self.is_running:
            return
        self.is_running = True
        threading.Thread(target=self._acq_loop, daemon=True).start()
    
    def _acq_loop(self):
        """Background loop to continuously pull EEG data"""
        while self.is_running:
            try:
                chunk, ts = self.inlet.pull_chunk(
                    timeout=1, 
                    max_samples=max(512, int(self.fs // 10))
                )
            except Exception:
                self.dropouts += 1
                continue
            
            if ts and chunk:
                chunk = np.asarray(chunk, dtype=np.float32)
                ts = np.asarray(ts, dtype=np.float64)
                
                if chunk.shape[1] < N_CH:
                    self.dropouts += 1
                    continue
                
                # Add to ring buffer
                with self.buffer_lock:
                    for k in range(len(ts)):
                        self.t_lsl.append(float(ts[k]))
                        for ch in range(N_CH):
                            self.y[ch].append(float(chunk[k, ch]))
                
                self.samples_total += len(ts)
                
                # Write to file if recording
                if self.is_recording:
                    self._write_data(ts, chunk[:, :N_CH])
    
    def start_recording(self):
        """Start recording session"""
        if self.is_recording:
            return
        
        # Create session directory
        safe_mkdir(DATA_DIR)
        self.session_id = f"FACIAL_{now_str()}"
        self.session_dir = DATA_DIR / self.session_id
        safe_mkdir(self.session_dir)
        
        # Open data file
        self.data_path = self.session_dir / "labeled_data.csv"
        self.data_file = open(self.data_path, "w", encoding="utf-8")
        self.data_file.write("label,t_lsl,TP9,AF7,AF8,TP10\n")
        self.data_file.flush()
        
        # Save metadata
        self.meta_path = self.session_dir / "meta.json"
        meta = {
            "session_id": self.session_id,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "muse_mac": MUSE_MAC,
            "fs_nominal": self.fs,
            "channels": CHANNEL_NAMES,
            "actions": [a[0] for a in ACTIONS],
            "action_duration_s": ACTION_DURATION_S,
            "rest_duration_s": REST_DURATION_S,
        }
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        
        self.is_recording = True
        self.last_flush_time = time.time()
        print(f"✅ Recording started: {self.session_dir}")
    
    def stop_recording(self):
        """Stop recording session"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Close data file
        if self.data_file:
            try:
                self.data_file.flush()
                self.data_file.close()
            except Exception:
                pass
            self.data_file = None
        
        # Update metadata
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
        
        print(f"✅ Recording stopped: {self.samples_total} samples")
    
    def _write_data(self, ts: np.ndarray, data_4ch: np.ndarray):
        """Write data to file"""
        with self.label_lock:
            label = self.current_label
        
        for i in range(len(ts)):
            row = [
                label,
                f"{float(ts[i]):.6f}",
                f"{float(data_4ch[i, 0]):.6f}",
                f"{float(data_4ch[i, 1]):.6f}",
                f"{float(data_4ch[i, 2]):.6f}",
                f"{float(data_4ch[i, 3]):.6f}",
            ]
            self.data_file.write(",".join(row) + "\n")
        
        # Periodic flush
        now = time.time()
        if now - self.last_flush_time >= FLUSH_EVERY_S:
            self.last_flush_time = now
            try:
                self.data_file.flush()
            except Exception:
                pass
    
    def set_label(self, label: str):
        """Change current label"""
        with self.label_lock:
            old_label = self.current_label
            self.current_label = label
            
            if label != old_label:
                self.event_counts[label] = self.event_counts.get(label, 0) + 1
    
    def get_plot_data(self, channel_idx: int = 1):
        """Get recent data for plotting (AF7 by default - frontal)"""
        with self.buffer_lock:
            t = np.asarray(self.t_lsl, dtype=np.float64)
            y = np.asarray(self.y[channel_idx], dtype=np.float32)
        
        if len(t) < 2:
            return np.array([0.0, 1.0]), np.array([0.0, 0.0])
        
        # Last 5 seconds
        t_end = t[-1]
        t_start = t_end - 5.0
        m = t >= t_start
        tt = t[m]
        yy = y[m]
        
        # Make relative
        if len(tt) > 0:
            tt = tt - tt[-1]
        
        return tt, yy
    
    def shutdown(self):
        """Clean shutdown"""
        self.is_running = False
        self.stop_recording()

# =========================
# Trial Manager
# =========================
class TrialManager:
    """Manages the sequence of trials with audio cues"""
    
    def __init__(self, recorder: EEGRecorder, audio: AudioCueManager):
        self.recorder = recorder
        self.audio = audio
        
        self.running = False
        self.paused = False
        
        self.current_action = "REPOSO"
        self.current_instruction = "Listo para comenzar"
        self.time_remaining = 0.0
        self.trial_count = 0
        
        self.state_lock = threading.Lock()
    
    def get_state(self):
        """Get current trial state"""
        with self.state_lock:
            return {
                "action": self.current_action,
                "instruction": self.current_instruction,
                "time_remaining": self.time_remaining,
                "trial_count": self.trial_count,
                "running": self.running,
                "paused": self.paused,
            }
    
    def start(self):
        """Start trial sequence"""
        if self.running:
            return
        
        self.running = True
        self.paused = False
        self.trial_count = 0
        
        threading.Thread(target=self._trial_loop, daemon=True).start()
    
    def pause(self):
        """Toggle pause"""
        self.paused = not self.paused
    
    def stop(self):
        """Stop trial sequence"""
        self.running = False
    
    def _update_state(self, action: str, instruction: str, time_remaining: float):
        """Update current state"""
        with self.state_lock:
            self.current_action = action
            self.current_instruction = instruction
            self.time_remaining = time_remaining
    
    def _trial_loop(self):
        """Main trial loop"""
        
        # Initial rest
        self._update_state("REPOSO", "Póngase cómodo. Comenzando pronto...", 3.0)
        self.recorder.set_label("REPOSO")
        time.sleep(3)
        
        while self.running:
            # Check pause
            while self.paused and self.running:
                self._update_state("PAUSADO", "Pausado - Presione Continuar", 0.0)
                time.sleep(0.5)
            
            if not self.running:
                break
            
            # Cycle through actions
            for action_name, action_desc in ACTIONS:
                if not self.running:
                    break
                
                self.trial_count += 1
                
                # Countdown phase
                self.audio.speak_ready()
                for countdown in range(int(COUNTDOWN_DURATION_S), 0, -1):
                    if not self.running:
                        break
                    self._update_state(
                        "PREPÁRESE",
                        f"Siguiente: {action_name}",
                        float(countdown)
                    )
                    if countdown <= 3:
                        self.audio.speak_countdown(countdown)
                    time.sleep(1)
                
                if not self.running:
                    break
                
                # Action phase
                self.audio.speak_action(action_name)
                self.recorder.set_label(action_name)
                
                t_start = time.time()
                while time.time() - t_start < ACTION_DURATION_S:
                    if not self.running:
                        break
                    elapsed = time.time() - t_start
                    remaining = ACTION_DURATION_S - elapsed
                    self._update_state(action_name, action_desc, remaining)
                    time.sleep(0.1)
                
                if not self.running:
                    break
                
                # Rest phase
                self.audio.speak("Reposo")
                self.recorder.set_label("REPOSO")
                
                t_start = time.time()
                while time.time() - t_start < REST_DURATION_S:
                    if not self.running:
                        break
                    elapsed = time.time() - t_start
                    remaining = REST_DURATION_S - elapsed
                    self._update_state("REPOSO", "Relájese y respire normalmente", remaining)
                    time.sleep(0.1)
        
        # End
        self._update_state("TERMINADO", "¡Sesión completa! ¡Excelente trabajo!", 0.0)
        self.audio.speak("Sesión completa. Muchas gracias.")

# =========================
# Main UI
# =========================
def run_ui():
    """Main UI application"""
    
    # Initialize components
    streamer = MuseStreamer(MUSE_MAC)
    recorder = EEGRecorder()
    audio = AudioCueManager()
    trial_manager = TrialManager(recorder, audio)
    
    ui_state = {
        "connected": False,
        "status": "Listo para conectar",
    }
    
    def set_status(msg: str):
        ui_state["status"] = msg
        if dpg.does_item_exist("status_text"):
            dpg.set_value("status_text", msg)
    
    def on_connect():
        """Connect to EEG"""
        try:
            set_status("Iniciando transmisión Muse...")
            streamer.start()
            time.sleep(WAIT_AFTER_START_S)
            
            set_status("Conectando a transmisión EEG...")
            fs = recorder.connect()
            recorder.start_stream_loop()
            
            ui_state["connected"] = True
            set_status(f"✅ ¡Conectado! fs={fs:.1f} Hz")
            
        except Exception as e:
            set_status(f"❌ Error: {e}")
    
    def on_start_session():
        """Start recording session"""
        if not ui_state["connected"]:
            set_status("⚠️  ¡Conecte el EEG primero!")
            return
        
        recorder.start_recording()
        trial_manager.start()
        set_status("✅ ¡Sesión iniciada!")
    
    def on_stop_session():
        """Stop recording session"""
        trial_manager.stop()
        recorder.stop_recording()
        set_status("Sesión detenida.")
    
    def on_pause():
        """Pause/resume session"""
        trial_manager.pause()
    
    def on_manual_mark(label: str):
        """Manually mark an event"""
        recorder.set_label(label)
        # Speak in Spanish
        label_spanish = {
            "PARPADEO_DERECHO": "Parpadeo derecho",
            "PARPADEO_IZQUIERDO": "Parpadeo izquierdo",
            "LEVANTAR_CEJAS": "Levantar cejas",
            "REPOSO": "Reposo"
        }
        audio.speak(label_spanish.get(label, label))
        set_status(f"Marcado manual: {label}")
    
    def ui_tick():
        """Update UI elements"""
        
        # Get trial state
        state = trial_manager.get_state()
        
        # Update main display - Make text BIGGER by spacing
        if dpg.does_item_exist("action_text"):
            action_display = "    " + "   ".join(state["action"]) + "    "
            dpg.set_value("action_text", action_display)
        
        if dpg.does_item_exist("instruction_text"):
            dpg.set_value("instruction_text", state["instruction"])
        
        if dpg.does_item_exist("timer_text"):
            dpg.set_value("timer_text", f"{state['time_remaining']:.1f}s")
        
        if dpg.does_item_exist("trial_count_text"):
            dpg.set_value("trial_count_text", f"Prueba: {state['trial_count']}")
        
        # Update stats
        if dpg.does_item_exist("stats_text"):
            c = recorder.event_counts
            stats = (
                f"Muestras: {recorder.samples_total}  |  "
                f"Pérdidas: {recorder.dropouts}  |  "
                f"Grabando: {recorder.is_recording}\n"
                f"REPOSO: {c.get('REPOSO', 0)}  |  "
                f"PARPADEO_DER: {c.get('PARPADEO_DERECHO', 0)}  |  "
                f"PARPADEO_IZQ: {c.get('PARPADEO_IZQUIERDO', 0)}  |  "
                f"LEVANTAR_CEJAS: {c.get('LEVANTAR_CEJAS', 0)}"
            )
            dpg.set_value("stats_text", stats)
        
        # Update plot
        tt, yy = recorder.get_plot_data(channel_idx=1)  # AF7
        if dpg.does_item_exist("series"):
            dpg.set_value("series", [tt.tolist(), yy.tolist()])
    
    def key_handler(sender, key):
        """Handle keyboard shortcuts"""
        if key in KEYS_MAP:
            label = KEYS_MAP[key]
            on_manual_mark(label)
    
    # Build UI
    dpg.create_context()
    
    # Create LARGE font for elderly users
    with dpg.font_registry():
        # Default font but MUCH larger
        large_font = dpg.add_font("./fonts/default.ttf", 32, default_font=False) if Path("./fonts/default.ttf").exists() else None
        huge_font = dpg.add_font("./fonts/default.ttf", 48, default_font=False) if Path("./fonts/default.ttf").exists() else None
    
    # Large, clear theme for elderly users
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 24, 24)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 16, 12)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 16, 16)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 16)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 12)
    
    dpg.bind_theme(global_theme)
    
    # Main window
    with dpg.window(tag="primary", label="Captura de Artefactos Faciales", width=1200, height=850):
        
        # Header
        dpg.add_text("Captura de Artefactos Faciales", color=(255, 255, 255))
        dpg.add_text("Investigación sobre Artefactos EEG en Adultos Mayores", color=(180, 180, 180))
        dpg.add_spacer(height=12)
        
        # Control buttons
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="1. CONECTAR EEG", 
                width=220, 
                height=60,
                callback=lambda: threading.Thread(target=on_connect, daemon=True).start()
            )
            dpg.add_button(
                label="2. INICIAR SESIÓN", 
                width=220, 
                height=60,
                callback=on_start_session
            )
            dpg.add_button(
                label="PAUSAR/CONTINUAR", 
                width=220, 
                height=60,
                callback=on_pause
            )
            dpg.add_button(
                label="DETENER SESIÓN", 
                width=220, 
                height=60,
                callback=on_stop_session
            )
        
        dpg.add_spacer(height=8)
        dpg.add_text(ui_state["status"], tag="status_text", color=(200, 220, 255))
        dpg.add_spacer(height=16)
        
        # === MAIN DISPLAY (LARGE) ===
        with dpg.child_window(height=320, border=True):
            dpg.add_spacer(height=30)
            
            # Current action (HUGE text) - Simulated with multiple spaces
            with dpg.group(horizontal=False):
                dpg.add_text(
                    "    R E P O S O    ",
                    tag="action_text",
                    color=(100, 255, 150)
                )
                dpg.add_spacer(height=8)
                dpg.add_text(
                    "════════════════════════════",
                    color=(100, 255, 150)
                )
                dpg.add_spacer(height=18)
                
                dpg.add_text(
                    "Listo para comenzar",
                    tag="instruction_text",
                    color=(220, 220, 220)
                )
                dpg.add_spacer(height=25)
                
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        "Tiempo: ",
                        color=(200, 200, 200)
                    )
                    dpg.add_text(
                        "0.0s",
                        tag="timer_text",
                        color=(255, 255, 100)
                    )
                    dpg.add_spacer(width=50)
                    dpg.add_text(
                        "Prueba: 0",
                        tag="trial_count_text",
                        color=(200, 200, 200)
                    )
        
        dpg.add_spacer(height=16)
        
        # Manual controls
        with dpg.child_window(height=150, border=True):
            dpg.add_text("Controles Manuales de Teclado (Anular Automático):", color=(200, 200, 200))
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="[D] Parpadeo Derecho",
                    width=240,
                    height=50,
                    callback=lambda: on_manual_mark("PARPADEO_DERECHO")
                )
                dpg.add_button(
                    label="[I] Parpadeo Izquierdo",
                    width=240,
                    height=50,
                    callback=lambda: on_manual_mark("PARPADEO_IZQUIERDO")
                )
                dpg.add_button(
                    label="[C] Levantar Cejas",
                    width=240,
                    height=50,
                    callback=lambda: on_manual_mark("LEVANTAR_CEJAS")
                )
                dpg.add_button(
                    label="[Espacio] Reposo",
                    width=240,
                    height=50,
                    callback=lambda: on_manual_mark("REPOSO")
                )
        
        dpg.add_spacer(height=12)
        
        # Stats
        with dpg.child_window(height=90, border=True):
            dpg.add_text("Estadísticas de la Sesión:", color=(200, 200, 200))
            dpg.add_spacer(height=5)
            dpg.add_text(
                "Muestras: 0  |  Pérdidas: 0  |  Grabando: False",
                tag="stats_text",
                color=(220, 220, 220)
            )
        
        dpg.add_spacer(height=12)
        
        # EEG Plot (smaller, less prominent)
        with dpg.child_window(height=200, border=True):
            dpg.add_text("EEG en Vivo - AF7 (Frontal) - Últimos 5s", color=(180, 180, 180))
            with dpg.plot(height=150, width=-1, anti_aliased=True):
                xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="")
                yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="µV")
                dpg.add_line_series([0, 1], [0, 0], parent=yaxis, tag="series")
        
        dpg.add_spacer(height=10)
        dpg.add_text(
            f"💾 Datos: {DATA_DIR.absolute()}/FACIAL_YYYYMMDD_HHMMSS/",
            color=(160, 160, 160)
        )
    
    # Setup viewport
    dpg.create_viewport(
        title="Captura de Artefactos Faciales - Adultos Mayores", 
        width=1250, 
        height=900
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary", True)
    
    # Register keyboard handler
    with dpg.handler_registry():
        dpg.add_key_press_handler(callback=key_handler)
    
    # Cleanup
    def cleanup():
        trial_manager.stop()
        recorder.shutdown()
        streamer.stop()
    
    atexit.register(cleanup)
    
    # Main render loop
    UI_FPS = 20
    last_ui = time.time()
    
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
        
        now = time.time()
        if now - last_ui >= (1.0 / UI_FPS):
            last_ui = now
            ui_tick()
    
    cleanup()
    dpg.destroy_context()

# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    print("=" * 70)
    print("Captura de Artefactos Faciales para Adultos Mayores")
    print("=" * 70)
    print()
    print("Este programa hará lo siguiente:")
    print("  • Conectarse al auricular EEG Muse 2")
    print("  • Usar señales de audio para cada acción")
    print("  • Mostrar instrucciones GRANDES y claras")
    print("  • Guardar automáticamente todos los datos")
    print()
    print("Acciones registradas:")
    print("  - Parpadeo ojo derecho")
    print("  - Parpadeo ojo izquierdo")
    print("  - Levantar cejas")
    print("  - Períodos de reposo")
    print()
    print("Atajos de teclado: D, I, C, Espacio")
    print("=" * 70)
    print()
    
    if not AUDIO_AVAILABLE:
        print("⚠️  Audio no disponible. Instalar con:")
        print("    pip install pyttsx3")
        print()
    
    try:
        run_ui()
    except KeyboardInterrupt:
        print("\n\n✅ Apagado completo.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
