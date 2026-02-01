import sys
import time
import subprocess
import threading
import atexit
from collections import deque

import numpy as np

# Set matplotlib backend BEFORE importing pyplot
# macOS-specific: Try multiple backends in order of preference
import matplotlib
try:
    # Try Qt5Agg first (usually best for macOS animations)
    matplotlib.use('Qt5Agg')
    print("[MATPLOTLIB] Using Qt5Agg backend")
except:
    try:
        # Fallback to MacOSX native backend
        matplotlib.use('MacOSX')
        print("[MATPLOTLIB] Using MacOSX backend")
    except:
        # Last resort: TkAgg
        matplotlib.use('TkAgg')
        print("[MATPLOTLIB] Using TkAgg backend")

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pylsl import StreamInlet, resolve_streams

# --------- CONFIG ----------
MUSE_MAC = "00:55:da:b7:e7:7c"  # Update with your Muse 2 MAC address
WAIT_AFTER_START_S = 8

WINDOW_SECONDS = 5
CHANNEL_NAMES = ["TP9", "AF7", "AF8", "TP10"]
# --------------------------

muse_proc = None


def start_muse_stream():
    global muse_proc
    python_exe = sys.executable
    cmd = [python_exe, "-m", "muselsl", "stream", "-a", MUSE_MAC]

    muse_proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

    def reader():
        if muse_proc.stdout is None:
            return
        for line in muse_proc.stdout:
            # Útil para debug:
            # print("[muselsl]", line.rstrip())
            pass

    threading.Thread(target=reader, daemon=True).start()

    def cleanup():
        global muse_proc
        if muse_proc is not None and muse_proc.poll() is None:
            muse_proc.terminate()
            try:
                muse_proc.wait(timeout=5)
            except Exception:
                muse_proc.kill()

    atexit.register(cleanup)


def list_streams():
    streams = resolve_streams(wait_time=2)
    print("[LSL] Streams encontrados:")
    for s in streams:
        print(f"  - name={s.name()} type={s.type()} ch={s.channel_count()} fs={s.nominal_srate()}")


def find_eeg_inlet(timeout=40) -> StreamInlet:
    t0 = time.time()
    while time.time() - t0 < timeout:
        streams = resolve_streams(wait_time=2)
        for s in streams:
            stype = (s.type() or "").lower()
            sname = (s.name() or "").lower()

            # muselsl típicamente publica EEG con type="EEG"
            if stype == "eeg" or "eeg" in stype or "/muse/eeg" in sname or "muse" in sname and "eeg" in sname:
                print(f"[LSL] EEG found: name={s.name()} type={s.type()} ch={s.channel_count()} fs={s.nominal_srate()}")
                return StreamInlet(s, max_buflen=60)

    list_streams()
    raise RuntimeError("No se encontró stream LSL EEG.")


def main():
    start_muse_stream()
    print(f"[MUSE] muselsl stream started for {MUSE_MAC}, waiting {WAIT_AFTER_START_S}s...")
    time.sleep(WAIT_AFTER_START_S)

    inlet = find_eeg_inlet()

    info = inlet.info()
    fs = float(info.nominal_srate() or 256.0)
    n_ch = info.channel_count()
    print(f"[INFO] EEG inlet: fs≈{fs}Hz  channels={n_ch}")

    if n_ch < 4:
        print("[WARN] Menos de 4 canales en el stream. No puedo mapear TP9/AF7/AF8/TP10 bien.")

    buf_len = int(WINDOW_SECONDS * fs)
    tbuf = deque(maxlen=buf_len)
    ybufs = [deque(maxlen=buf_len) for _ in range(4)]

    for i in range(buf_len):
        tbuf.append(-WINDOW_SECONDS + i / fs)
        for ch in range(4):
            ybufs[ch].append(0.0)

    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(12, 8))
    fig.suptitle("Muse 2 - EEG en tiempo real (/muse/eeg)")

    lines = []
    for i, ax in enumerate(axes):
        ax.set_ylabel(CHANNEL_NAMES[i])
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-200, 200)  # Initial y-axis range for EEG (microvolts)
        line, = ax.plot(list(tbuf), list(ybufs[i]))
        lines.append(line)
    axes[-1].set_xlabel("Tiempo (s)")
    axes[-1].set_xlim(-WINDOW_SECONDS, 0)  # Initial x-axis range

    start_wall = time.time()
    last_print = 0.0
    samples_total = 0
    update_count = 0  # Track how many times update is called

    def update(_frame):
        nonlocal last_print, samples_total, update_count
        
        update_count += 1

        chunk, ts = inlet.pull_chunk(timeout=0.0, max_samples=max(16, int(fs // 10)))

        if ts and chunk:
            chunk = np.asarray(chunk, dtype=np.float32)  # (N, n_ch)
            ts = np.asarray(ts, dtype=np.float64)
            samples_total += len(ts)

            rel_now = time.time() - start_wall
            rel_t = rel_now + (ts - ts[-1])

            # Primeros 4 canales (Muse EEG típico)
            for k in range(len(ts)):
                tbuf.append(float(rel_t[k]))
                for ch in range(4):
                    ybufs[ch].append(float(chunk[k, ch]))

        # debug cada ~1s
        now = time.time()
        if now - last_print > 1.0:
            last_print = now
            if samples_total == 0:
                print(f"[DBG] update_count={update_count} | Aún no llegan muestras EEG...")
            else:
                rng = []
                for ch in range(4):
                    y = np.asarray(ybufs[ch], dtype=np.float32)
                    rng.append((float(np.min(y)), float(np.max(y))))
                print(f"[DBG] update_count={update_count} | samples_total={samples_total} | ranges={rng} | buffer_len={len(tbuf)}")

        # ALWAYS update plot data, even if no new samples arrived
        x = np.asarray(tbuf, dtype=np.float64)
        if len(x) > 2:
            x_min = x[-1] - WINDOW_SECONDS
            x_max = x[-1]
            for ax in axes:
                ax.set_xlim(x_min, x_max)

        for i in range(4):
            y = np.asarray(ybufs[i], dtype=np.float32)
            lines[i].set_data(x, y)

            if len(y) > 10:
                lo, hi = np.percentile(y, [5, 95])
                pad = max(1e-6, (hi - lo) * 0.2)
                axes[i].set_ylim(lo - pad, hi + pad)
        
        return lines

    # CLAVE: guardar referencia a la animación para que NO se destruya
    print("\n[INFO] Starting animation... Window should appear now.")
    anim = FuncAnimation(fig, update, interval=30, blit=True, cache_frame_data=False)
    
    plt.tight_layout()
    plt.show()  # Simplified - just show the plot


if __name__ == "__main__":
    main()