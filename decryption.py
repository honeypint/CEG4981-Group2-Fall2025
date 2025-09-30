import hashlib # hashlib for MD5
import os # used for file creation/iteration
import io # Used for converting image to bytes
import sys # Used to exit code on fail

from base64 import b64decode # b64decode function
from PIL import Image # Python Imaging Library
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Util.Padding import pad # pad function

SOURCE_DIR = "./Encrypted_Images"
KEY_FILE = "./key.txt"
RESULT_DIR = "./Decrypted_Images"
os.makedirs(RESULT_DIR, exist_ok=True)

# -- Check if the above files exist; if not, end program immediately
if not os.path.exists(SOURCE_DIR) or not os.path.exists(KEY_FILE):
    print("ERROR: Required file not detected, ending decryption program!")
    sys.exit()

# -- Fetch key from a file; the same key used for encryption
with open(KEY_FILE, 'r') as file:
    key_line = file.readline().strip()
    key = bytes.fromhex(key_line)

# TODO: change file name as needed further down the process
# -- Iterate through the hashes file, process each image individually
i = 0
for file in os.listdir(SOURCE_DIR):
    filename = os.path.basename(file).replace(".bin", "")

    # -- Fetch data needed for encryption from each file. Format per line is md5hash, ciphertext, tag, nonce
    with open(f"{SOURCE_DIR}/{file}") as readfile:
        image_entry = readfile.read().split()
    ciphertext = b64decode(image_entry[1])
    tag = b64decode(image_entry[2])
    nonce = b64decode(image_entry[3])
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    # -- Decrypt ciphertext & convert image to proper format. Verify if the ciphertext is legitimate.
    image_data = b64decode(cipher.decrypt(ciphertext))
    try:
        cipher.verify(tag)
    except ValueError:
        print("**ERROR**: Incorrect key or corrupted message!")
        continue # TODO: send over transmission error

    # -- Create new md5 checksum, compare the two to ensure no data loss occurred.
    #    -- If success: add the image to the Decrypted Images folder
    #    -- If fail: send a transmission error for resending
    decrypted_image = Image.open(io.BytesIO(image_data))
    md5hash = hashlib.md5(decrypted_image.tobytes())
    md5hash = md5hash.hexdigest()
    if md5hash == image_entry[0]:
        print(f"Image {filename}.bin decrypted correctly.") # md5's match
        ext = decrypted_image.format.lower() if decrypted_image.format else "png"
        output_path = f"{RESULT_DIR}/{filename}.{ext}"
        decrypted_image.save(output_path, format=decrypted_image.format)
    else:
        print(f"**ERROR**: Checksums do not match for {filename}.{ext}") # md5's do not match
        continue # TODO: send over transmission error
    
# -- Decryption process fully completed, send over to cropping program IF program file exists
CROPPING_PROGRAM = "./Image-Cropping.py"
if os.path.exists(CROPPING_PROGRAM):
    os.system(f'python3 {CROPPING_PROGRAM}')
else:
    print(f'ERROR: {CROPPING_PROGRAM} does not exist! Stopping after Decryption step.')