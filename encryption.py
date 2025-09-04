import hashlib # hashlib for MD5
import os # used for file iteration
import io # Used for converting image to bytes
import json # used for result structuring
from PIL import Image # Python Imaging Library
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Random import get_random_bytes # random bytes
from base64 import b64encode # b64encode function
from Crypto.Util.Padding import pad # pad function

filepath = "./sample-images" # TODO: EDIT TO WHAT IS NEEDED
image_md5s = []
# -- Create md5 hashes for every image and pair them together in a list by [filename, md5]
for file in os.listdir(filepath):
    if file.endswith('.png'):
        image = Image.open(filepath+'/'+file)
        md5hash = hashlib.md5(image.tobytes())
        md5hash = md5hash.hexdigest()
        image_md5s.append([file, image, md5hash]) # file path, image, md5hash
        continue
    else:
        print("File "+file+" is not a .png")
        continue

# -- INITIAL encryption of these images using AES, making sure they remained paired with their MD5 checksums
image_hashes = []
# Fetch key from file, set up cipher
with open("./key.txt", 'r') as file:
    key_line = file.readline().strip()
    key = bytes.fromhex(key_line)
# for each image, encrypt it, and add to image_hashes list WITH the previously generated md5
# AES-128 EAX encryption was made with reference to pycryptodome documentation: 
# https://pycryptodome.readthedocs.io/en/latest/src/cipher/aes.html
# TODO: clean this section up a bit
for image_entry in image_md5s:
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    image_byte_array = io.BytesIO()
    image_entry[1].save(image_byte_array, format=image_entry[1].format)
    image_bytes = image_byte_array.getvalue()
    image_bytes_string = b64encode(image_bytes)
    ciphertext, tag = cipher.encrypt_and_digest(image_bytes_string)
    
    result = [b64encode(ciphertext).decode('utf-8'), b64encode(tag).decode('utf-8'), b64encode(nonce).decode('utf-8')]
    image_hashes.append([image_entry[2], result]) # md5hash, ciphertext, tag, nonce

# -- Add md5hash+result triad to a separate text file which will be worked with for the data transfer
with open("./image_hashes.txt", 'w') as file:
    for image in image_hashes:
        file.write(image[0]+" ")
        for item in image[1]:
            file.write(item+" ")
        file.write("\n")