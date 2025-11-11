# 🧠 Tkinter Fix & Streaming Setup for Muse 2 (macOS)

## 🎯 Objective

Ensure **real-time EEG visualization** with `muselsl view` works correctly on macOS by properly linking the **Tcl/Tk framework** used by Matplotlib.

This guide documents how to configure **Tkinter** within a Python 3.13 environment (installed via Homebrew) for use with the **Muse 2 + muselsl** pipeline.

---

## 🧩 1️⃣ Problem

When running:

```bash
muselsl view
```

you may encounter:

```
import _tkinter # If this fails your Python may not be configured for Tk
```

This happens because macOS Python (installed via Homebrew) does **not include the Tcl/Tk GUI framework** by default.

---

## ⚙️ 2️⃣ Install Tkinter via Homebrew

Run this outside your virtual environment:

```bash
brew install python-tk@3.13
```

> If you are using Python 3.11 or 3.12:
>
> ```bash
> brew install python-tk@3.11
> ```
>
> or
>
> ```bash
> brew install python-tk@3.12
> ```

Check the installation path:

```bash
brew info python-tk@3.13
```

Expected output:

```
/opt/homebrew/Cellar/python-tk@3.13/3.13.9
```

---

## 🔗 3️⃣ Link Tkinter to Your Virtual Environment

Activate your venv:

```bash
source muse_venv/bin/activate
```

Then export the library path (temporary for this session):

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/python-tk@3.13/lib:${DYLD_LIBRARY_PATH}"
export TK_SILENCE_DEPRECATION=1
```

> Use the **Cellar path** if you prefer, e.g.  
> `/opt/homebrew/Cellar/python-tk@3.13/3.13.9/lib`

---

## 🧪 4️⃣ Verify Tkinter Works

Run:

```bash
python -m tkinter
```

✅ A small empty “Tk” window should appear.  
Alternatively:

```bash
python -c "import tkinter as tk; print('Tk version:', tk.TkVersion)"
```

---

## 🧰 5️⃣ (Optional) Reinstall Matplotlib

If the backend was compiled before Tk was installed:

```bash
pip install --force-reinstall matplotlib
```

Force TkAgg as backend if needed:

```python
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
```

---

## 📡 6️⃣ Test Real-Time Streaming

Ensure your Muse 2 is connected via BLE:

```bash
muselsl stream
```

Then, in another terminal:

```bash
muselsl view
```

✅ You should now see 4 EEG traces (TP9, AF7, AF8, TP10) in a live window.

---

## 🧘‍♀️ 7️⃣ Make the Fix Permanent

Edit your environment activator file:

```bash
nano muse_venv/bin/activate
```

Add these lines at the end:

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/python-tk@3.13/lib:${DYLD_LIBRARY_PATH}"
export TK_SILENCE_DEPRECATION=1
```

Save and close.  
Now every time you run:

```bash
source muse_venv/bin/activate
```

your Tkinter setup will load automatically.

---

## Record a Session

```bash
muselsl record --duration <duration> --filename data/<name.csv>
```

## Record without duration

Press q + Enter.

## Kill the Stream

```bash
pkill -f muselsl

```

## Deactivate venv

```bash
deactivate
```

## 🧭 Summary

| Step        | Command                                    | Purpose                      |
| ----------- | ------------------------------------------ | ---------------------------- |
| Install Tk  | `brew install python-tk@3.13`              | Add missing Tcl/Tk framework |
| Export path | `export DYLD_LIBRARY_PATH=...`             | Let Python find Tk libs      |
| Verify      | `python -m tkinter`                        | Confirm GUI works            |
| Reinstall   | `pip install --force-reinstall matplotlib` | Ensure backend detection     |
| Stream      | `muselsl view`                             | Real-time EEG visualization  |

---

✨ _Documented fix for macOS + Python 3.13 (Homebrew build)._
