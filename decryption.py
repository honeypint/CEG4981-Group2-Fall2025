import os # used for file iteration
import io # Used for converting image to bytes
import json # used for result structuring
from PIL import Image # Python Imaging Library
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Random import get_random_bytes # random bytes
from base64 import b64encode # b64encode function
from Crypto.Util.Padding import pad # pad function

# Fetch key from a file; the same key used for encryption
with open("./key.txt", 'r') as file:
    key_line = file.readline().strip()
    key = bytes.fromhex(key_line)

# TODO: change file name as needed further down the process
with open('image_hashes.txt', 'r') as file:
    for line in file:
        # -- Fetch data needed for encryption from each file. Format per line is md5hash, ciphertext, tag, nonce
        image_entry = line.split()
        ciphertext = image_entry[1]
        tag = image_entry[2]
        nonce = image_entry[3]
        cipher = AES.new(key, AES.MODE_EAX, nonce=image_entry[3])
        # -- Decrypt ciphertext & convert image to proper format.
        image_data = cipher.decrypt(ciphertext)
        try:
            cipher.verify(tag)
            print("Ciphertext decrypted correctly.")
        except ValueError:
            print("**ERROR**: Incorrect key or corrupted message!")
        decrypted_image = Image.open(io.BytesIO(image_data))
        decrypted_image.save("./Decrypted Images/"+decrypted_image.filename, format=decrypted_image.format) # TODO: find reason for errors
        # -- Create new md5 checksum, compare the two to ensure no data loss occurred