import os # folder checking/management
import shutil # file copying
import time # for waiting

# To think about:
# /etc/udev/rules.d
# ACTION=="add", SUBSYSTEM=="usb", RUN+="/home/Group2/usb-detection.py"
# ACTION=="remove", SUBSYSTEM=="usb", PROGRAM="<full_path_here>/on_usb_out.sh"

# -- Code that runs on a USB file input, checks every folder, and grabs JPG files.
USERNAME = "Group2"
IMAGES_FOLDER = "./runImages"
os.makedirs(IMAGES_FOLDER, exist_ok=True)

def copy_usb():
    result = False # start as false
    if os.path.isdir(f'/media/{USERNAME}'): # check if media folder exists first
        for filename in os.listdir(f'/media/{USERNAME}'): # get every file/folder in user's media folder
            file_path = f'/media/{USERNAME}/{filename}'
            if os.access(file_path, os.R_OK) and os.path.isdir(file_path): # if directory for usb - search it, grab all jpg files
                for file in os.listdir(file_path): 
                    if file.endswith(".png"):
                        shutil.copy(os.path.join(file_path, file), f'{IMAGES_FOLDER}') # copy to sample-images folder .
                        print(f'File {file} copied successfully!')
                        result = True # adjust to true if a png is successfully found & copied!
    return result # only returns a result once every file is looped through, to ensure obtainment of all files

# -- Loops above function until files are copied
loop = True
while loop:
    if copy_usb():
        loop = False
    else:
        print("Searching for a USB entry with PNG files in them...")
    time.sleep(5)
# -- Decryption process fully completed, send over to cropping program IF program file exists
ENCRYPTION_PROGRAM = "./encryption.py"
if os.path.exists(ENCRYPTION_PROGRAM):
    os.system(f'python {ENCRYPTION_PROGRAM}')
else:
    print(f'ERROR: {ENCRYPTION_PROGRAM} does not exist! Stopping after USB Detection step.')
