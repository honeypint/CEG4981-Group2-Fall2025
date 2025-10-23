#!/usr/bin/env python3
import os
import shutil
import time
import subprocess

USERNAME = "Group2"
BASE = f"/home/{USERNAME}"
IMAGES_FOLDER = f"{BASE}/runImages"
YOLO_PROGRAM = f"{BASE}/yolorun.py"
PYTHON_PATH = f"{BASE}/rf24env/bin/python3"  # path to your venv's python

os.makedirs(IMAGES_FOLDER, exist_ok=True)

def copy_usb():
    result = False
    usb_base = f"/media/{USERNAME}"
    if os.path.isdir(usb_base):
        for filename in os.listdir(usb_base):
            file_path = os.path.join(usb_base, filename)
            if os.access(file_path, os.R_OK) and os.path.isdir(file_path):
                for file in os.listdir(file_path):
                    if file.lower().endswith(".png"):
                        shutil.copy(os.path.join(file_path, file), IMAGES_FOLDER)
                        print(f"File {file} copied successfully!")
                        result = True
    return result

# Loop until USB images are detected
while True:
    if copy_usb():
        print("All images copied. Proceeding to YOLO recognition...")
        break
    else:
        print("Searching for a USB entry with PNG files in them...")
    time.sleep(5)

# Run YOLO program inside venv
if os.path.exists(YOLO_PROGRAM):
    print("Running yolorun.py...")
    try:
        subprocess.run([PYTHON_PATH, YOLO_PROGRAM], check=True)
        print("YOLO run completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running yolorun.py: {e}")
else:
    print(f"ERROR: {YOLO_PROGRAM} does not exist! Stopping after USB detection step.")
