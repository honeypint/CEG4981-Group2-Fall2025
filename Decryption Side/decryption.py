import hashlib # hashlib for MD5
import os # used for file creation/iteration
import io # Used for converting image to bytes
import sys # Used to exit code on fail

from base64 import b64decode # b64decode function
from PIL import Image # Python Imaging Library
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Util.Padding import pad # pad function
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import threading

SOURCE_DIR = "./Encrypted_Images" # TODO: file path should change depending on other files!
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
        continue
    
# -- Decryption process fully completed, open and send to Flask server
app = Flask(__name__)
CORS(app)

FOLDER_PATH = os.path.abspath(RESULT_DIR)

@app.route("/files", methods=["GET"])
def list_files():
    return jsonify(os.listdir(FOLDER_PATH))

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    return send_from_directory(FOLDER_PATH, filename)

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
