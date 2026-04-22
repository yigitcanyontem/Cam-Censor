# 🛡️ Cam-Censor: Privacy-Preserving Fall Detection

Cam-Censor is a professional-grade security application designed to monitor live camera feeds while maintaining strict individual privacy. It uses **YOLOv8 AI** to detect people and completely censor their bodies with black silhouettes in real-time, while simultaneously monitoring for falls or emergencies.

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![AI](https://img.shields.io/badge/AI-YOLOv8-orange.svg)

---

## 🌟 Key Features

- **Privacy-First Censorship**: Unlike standard systems that use blocky boxes, Cam-Censor uses pixel-perfect instance segmentation to draw custom black polygons over people.
- **Skeletal Backup**: Even if a person is partially obscured (e.g., under a blanket), the system uses pose-tracking to draw a "skeletal blob," ensuring identity is never compromised.
- **Fall Detection**: Automatically triggers a visual alert if a person falls or collapses, based on AI-analyzed body dynamics.
- **Modern GUI**: A sleek, dark-themed control center built with `customtkinter`.
- **Windows Executable Support**: Easily package the entire system into a single `.exe` file for distribution.

## 🚀 Quick Start

### 1. Installation
Ensure you have Python 3.9+ installed, then:

```bash
git clone https://github.com/your-repo/cam-censor.git
cd cam-censor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install customtkinter PyInstaller  # Additional GUI/Build tools
```

### 2. Running the App
Launch the main monitoring console:
```bash
python app_gui.py
```

---

## 📦 Create a Windows Executable (.exe)

To send this app to someone who doesn't have Python, you can package it into a standalone `.exe`.

> [!IMPORTANT]
> Because PyInstaller packages the local OS environment, you **must** run these steps on a **Windows** machine to generate a `.exe`.

1. Open a terminal in the project folder.
2. Run the packaging script:
   ```bash
   python package_pyinstaller.py
   ```
3. Your standalone app will be created in the `dist/CamCensor.exe` folder.

---

## 🏢 Scaling for Security Systems

For "a lot of cameras" (hospital wings, large facilities, etc.), this system can be scaled horizontally:

- **GPU Acceleration**: Use an NVIDIA GPU with CUDA enabled for seamless multi-stream processing.
- **Nano Models**: The system defaults to **YOLOv8n** (Nano) for the best performance-to-accuracy ratio.
- **Distributed Architecture**: See the [Scaling Guide](file:///Users/yigitcanyontem/.gemini/antigravity/brain/fe2942ee-1f42-4c1c-bbac-77a4291fc266/scaling_guide.md) for details on handling 20+ concurrent streams.

---

## 🛠️ Troubleshooting

- **Models not loading?**: Ensure `yolov8n.pt` and `yolov8n-seg.pt` are in the root directory. If missing, they will auto-download on the first run.
- **Slow Performance?**: If you don't have a dedicated GPU, consider lowering the "Floor Sensitivity" in the GUI or using a lower-resolution camera source.
