# Privacy-Preserving Fall Detection Camera System

This project processes live security camera feeds (or video files) to completely censor (black out) human bodies for privacy compliance while simultaneously detecting if a person falls down or is crouching in an emergency using YOLOv8 instance segmentation and pose tracking.

## Features
- **Real-Time Patient Censorship**: Uses YOLOv8 Segmentation to precisely map and draw a customized black polygon over any person in the frame, avoiding blocky bounding boxes.
- **Fall & Crouch Detection**: Automatically tracks individuals and calculates their body aspect ratio. If they switch to a horizontal state (or heavily crouched position) for over 1 second, a flashing emergency alert triggers on the output feed.
- **Edge-Ready**: Can be run on local centralized servers with NVIDIA GPUs for multiple concurrent camera streams, or on edge AI devices.

## Installation & Setup

You can install the dependencies using either traditional Python `pip` or using `conda`.

### Method 1: Using Standard PIP (Recommended)
1. Ensure Python 3.9+ is installed and added to PATH. 
2. Open a terminal/command prompt in the folder.
3. Create a python virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - **Windows (PowerShell)**: `.\venv\Scripts\activate`
   - **Windows (Command Prompt)**: `.\venv\Scripts\activate.bat`
   - **Mac/Linux**: `source venv/bin/activate`
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Method 2: Using Conda (Anaconda / Miniconda)
If you prefer Conda, simply run:
```bash
conda env create -f environment.yml
conda activate livecam-human-censor
```

## Usage Guide

1. Place your input video file into the project folder. Ensure it is named `test.mp4`.
2. Run the script from your terminal:
   ```bash
   python demo.py
   ```
3. The script will automatically download the required YOLOv8 segmentation model (`yolov8n-seg.pt`) on its first run and process the video frame-by-frame.
4. Once complete, you will find a generated file named `censored_output.mp4` in the project directory featuring the blacked-out privacy masks and flashing fall alerts.

## Troubleshooting
- **False Positives in Bed**: The model currently treats `width > height * 0.8` as a fall/crouching position. If the camera angle shows beds, you can easily increase the `conf` threshold in `demo.py` or modify the aspect ratio multiplier to tweak sensitivity.
- **Doesn't see people**: The AI model's confidence threshold `conf=0.08` allows it to see nearly everything resembling a human. You can raise this if it draws black boxes over objects that aren't humans.
- **Slow Performance**: Running AI models without a dedicated GPU is intensive and slow. If you want this to run instantly on live feeds, consider using a computer with an NVIDIA RTX graphics card or Jetson device.
