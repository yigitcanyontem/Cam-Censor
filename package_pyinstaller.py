import PyInstaller.__main__
import os
import sys
import customtkinter
import platform

print(f"OS Detected: {platform.system()} {platform.release()}")
if platform.system() == "Darwin":
    print("!!! WARNING: You are building on macOS. This will create a Mac app, NOT a Windows .exe !!!")
    print("To create a Windows .exe, you must run this script on a Windows machine.")
elif platform.system() == "Linux":
    print("!!! WARNING: You are building on Linux. This will create a Linux binary !!!")

# Get customtkinter path
ctk_path = os.path.dirname(customtkinter.__file__)

# Define data files to include
# format: (source_path, destination_folder)
data_files = [
    ('yolov8n.pt', '.'),
    ('yolov8n-seg.pt', '.'),
    (os.path.join(ctk_path, 'assets'), 'customtkinter/assets'),  # Correct CTk assets folder
]

# Build data arguments for PyInstaller
# For Windows: "source;dest"
# For POSIX: "source:dest"
separator = ';' if os.name == 'nt' else ':'
data_args = []
for src, dst in data_files:
    data_args.append(f'--add-data={src}{separator}{dst}')

# Command line arguments for PyInstaller
args = [
    'app_gui.py',  # Main script
    '--name=CamCensor',
    '--onefile',   # Bundle into a single executable
    '--windowed',  # Don't open a console window
    '--clean',     # Clean PyInstaller cache
] + data_args

print(f"Building with arguments: {' '.join(args)}")

if __name__ == "__main__":
    # Note: This tool call only creates the script. 
    # To actually run it, the user would need pyinstaller installed.
    # I will provide instructions on how to run this.
    PyInstaller.__main__.run(args)
