import hashlib # hashlib for MD5
import os # used for file iteration
import io # Used for converting image to bytes

from base64 import b64encode # b64encode function
from PIL import Image # Python Imaging Library
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Random import get_random_bytes # random bytes
from Crypto.Util.Padding import pad # pad function

# TODO: EDIT TO WHAT IS NEEDED
SOURCE_DIR = "./sample-images" # where the images are to be found
KEY_FILE = "./key.txt" # where the key is stored
RESULT_FILE = "./image_hashes.txt" # where the results are stored, list of strings [md5, ciphertext, tag, nonce]
image_hashes = []

# -- Fetch key from file
with open(KEY_FILE, 'r') as file:
    key_line = file.readline().strip()
    key = bytes.fromhex(key_line)

# -- Iterate through each file in the source directory.
# -- Check if file is image to confirm it is an expected png image file.
#    -- If verified, preform the md5 generation + encryption
for file in os.listdir(SOURCE_DIR):
    if file.endswith('.png'):
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
        # store result as strings for transmission, append that list to the md5
        result = [b64encode(ciphertext).decode('utf-8'), b64encode(tag).decode('utf-8'), b64encode(nonce).decode('utf-8')]
        image_hashes.append([md5hash, result]) # [md5hash, ciphertext, tag, nonce]
        continue
    else:
        # the file to encrypt was not the expected format
        print("File "+file+" is not a .png")
        continue

# -- Add md5hash & the result triad to a separate text file which will be worked with for the data transfer
with open(RESULT_FILE, 'w') as file:
    for image in image_hashes:
        file.write(image[0]+" ")
        for item in image[1]:
            file.write(item+" ")
        file.write("\n")