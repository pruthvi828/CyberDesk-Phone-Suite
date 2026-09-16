# ⚡ CyberDesk: Low-Level Android Systems, Diagnostics & DSP Suite

An advanced hardware interfacing and diagnostic suite for Android devices over USB/ADB. Features **kernel-level display refresh rate pinning (120Hz continuous)**, **real-time optical photoplethysmography (PPG) biometric monitoring**, **high-speed 120 FPS audio FFT digital signal processing (DSP)**, **acoustic resonance speaker ejection (165Hz)**, and an **autonomous open-source contribution scout**.

---

## 🌟 Core Engineering Modules

### 1. 📱 Low-Level Android Internals & Display Overclocking
- **SurfaceFlinger Refresh Rate Pinning**: Uses shell-level `settings put system peak_refresh_rate 120.0` and `min_refresh_rate 120.0` to force maximum fluidity on dynamic-LTPO displays (Realme/ColorOS, OxygenOS, Pixel).
- **Subsystem Diagnostics**: Telemetry gathering for battery thermal curves, memory headroom, storage block allocation, and running background daemons.
- **Wireless Scrcpy Engine**: Low-latency H.264/H.265 screen mirroring and low-overhead control streams over ADB TCP/IP.

### 2. ❤️ Real-Time Optical Biometric Sensing (PPG)
- **Mathematical Photoplethysmography**: Extracts systolic arterial pulses directly through the rear camera sensor by illuminating capillaries with the LED flash.
- **Green/Luminance Channel Decomposition**: Captures optical absorption flux caused by hemoglobin pulsatile blood flow, applies moving-average smoothing and peak-to-peak interval (PPI) filtering to compute BPM and HRV in real-time.

### 3. 🔊 120 FPS Audio FFT Digital Signal Processing (DSP)
- **1024-Point Fast Fourier Transform**: Real-time spectral audio analysis via WebAudio API rendered onto HTML5 Canvas with dual neon cyber-glow shaders.
- **Acoustic Water Ejection**: Emits calibrated resonant sound waves (165Hz square/sine sweeps with duty-cycle pulses) to generate kinetic air displacement and dislodge moisture from the phone's speaker acoustic chamber.

### 4. 🖱️ Zero-Latency Phone-as-Trackpad
- Converts the mobile capacitive touchscreen into a high-precision PC trackpad and media control deck using WebSocket communication to the host machine.

### 5. 🛡️ Non-Destructive Storage Segregator
- Distinguishes user media from junk: preserves genuine camera photos, videos, and mission-critical documents (`.pdf`, `.docx`, `.xlsx`) while isolating ephemeral screenshots, `.cache`, `.thumbnails`, and orphaned `.apk` installers.

### 6. 📡 Autonomous Open-Source Contribution Radar
- Automated GitHub Actions scout that continuously indexes unassigned `good first issue` opportunities across high-star repositories with a zero-risk anti-spam policy.

---

## 🏗️ Architecture Overview

```
                          ┌────────────────────────┐
                          │   Android Device       │
                          │   (Realme P1 5G)       │
                          └──────────┬─────────────┘
                                     │  USB / ADB Shell
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        CyberDesk Backend Engine                        │
│                                                                        │
│   [ADB Bridge & Shell]    [Audio DSP & Ejection]   [PPG Biometrics]    │
│    · Refresh Rate Lock     · 165Hz Sonic Pulses     · Hemoglobin Flux  │
│    · Thermal Telemetry     · 1024-pt FFT Stream     · Camera2 Stream   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │  FastAPI / WebSockets
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    CyberDesk Real-Time HUD (Web)                       │
│                                                                        │
│   · 120 FPS Neon Audio Visualizer   · Interactive Hardware Console     │
│   · Real-Time Heart Rate Gauge      · Wireless Scrcpy Mirroring        │
└────────────────────────────────────┴───────────────────────────────────┘
```

---

## 🚀 Quickstart & Deployment

### 1. Prerequisites
- Python 3.10+
- Android SDK Platform-Tools (`adb`) on PATH
- Android device connected via USB with **USB Debugging** enabled

### 2. Installation
```bash
git clone https://github.com/pruthvi828/PHONE-CLEAN.git
cd PHONE-CLEAN
pip install -r requirements.txt
```

### 3. Launching CyberDesk Suite
```bash
# Double-click start_cleaner.bat or run:
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8484
```
Access the interactive HUD at **`http://localhost:8484`**.

---

## 🛠️ Technology Stack
- **Languages:** Python, JavaScript (ES6+), PowerShell, Bash
- **Frameworks:** FastAPI, Uvicorn, WebAudio API, HTML5 Canvas 2D
- **Hardware Protocol:** Android Debug Bridge (ADB), Camera2 API, SurfaceFlinger
- **Automation & CI/CD:** GitHub Actions, Python `urllib`/`requests`
