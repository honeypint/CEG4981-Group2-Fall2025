import hashlib # hashlib for MD5
import os # used for file creation/iteration
import io # Used for converting image to bytes
import sys # Used to exit code on fail

from base64 import b64encode # b64encode function
from PIL import Image # Python Imaging Library
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Util.Padding import pad # pad function

# TODO: EDIT TO WHAT IS NEEDED
SOURCE_DIR = "./sample-images" # where the images are to be found
KEY_FILE = "./key.txt" # where the key is stored
RESULT_DIR = "./Encrypted_Images" # where the results are stored, list of strings [md5, ciphertext, tag, nonce]
os.makedirs(RESULT_DIR, exist_ok=True)

# -- Check if the above files exist; if not, end program immediately
if not os.path.exists(SOURCE_DIR) or not os.path.exists(KEY_FILE):
    print("ERROR: Required file not detected, ending encryption program!")
    sys.exit()

# -- Fetch key from file
with open(KEY_FILE, 'r') as file:
    key_line = file.readline().strip()
    key = bytes.fromhex(key_line)

# -- Iterate through each file in the source directory.
# -- Check if file is image to confirm it is an expected png image file.
#    -- If verified, preform the md5 generation + encryption
for file in os.listdir(SOURCE_DIR):
    if file.endswith('.png'):
        filename = os.path.basename(file).replace(".png", "")

        # -- Create md5 hashes for every image and pair them together in a list by [filename, md5]
        image = Image.open(f"{SOURCE_DIR}/{file}")
        md5hash = hashlib.md5(image.tobytes())
        md5hash = md5hash.hexdigest()

        # -- for each image, encrypt it, and add to image_hashes list WITH the previously generated md5
        #    -- AES-128 EAX encryption was made with reference to pycryptodome documentation: 
        #    -- https://pycryptodome.readthedocs.io/en/latest/src/cipher/aes.html
        cipher = AES.new(key, AES.MODE_EAX)
        nonce = cipher.nonce
        # turn image into bytes string, encrypt
        image_byte_array = io.BytesIO()
        image.save(image_byte_array, format=image.format)
        image_bytes = image_byte_array.getvalue()
        image_bytes_string = b64encode(image_bytes)
        ciphertext, tag = cipher.encrypt_and_digest(image_bytes_string)
        # store result as strings in a file individually for transmission, append that list to the md5
        result = [b64encode(ciphertext).decode('utf-8'), b64encode(tag).decode('utf-8'), b64encode(nonce).decode('utf-8')]
        with open(f"{RESULT_DIR}/{filename}.bin", 'w') as file_wr:
            file_wr.write(md5hash+" ")
            for item in result:
                file_wr.write(item+" ")
        print(f"Image {filename}.png encrypted correctly.")
        continue
    else:
        # the file to encrypt was not the expected format
        print(f"File {filename} is not a .png")
        continue