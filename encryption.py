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
key = get_random_bytes(16) # TODO: make one permanent key that is on both sides. keep with ciphertext, nonce, tag
cipher = AES.new(key, AES.MODE_CBC)
for image_entry in image_md5s:
    image_byte_array = io.BytesIO()
    image_entry[1].save(image_byte_array, format=image_entry[1].format)
    image_bytes = image_byte_array.getvalue()
    ciphertext = cipher.encrypt = (pad(image_bytes, AES.block_size))
    iv = b64encode(cipher.iv).decode('utf-8')
    ciphertext = b64encode(ciphertext).decode('utf-8')
    #ciphertext, tag = cipher.encrypt_and_digest(image_entry[1]) # TODO: use a specific encryption for images
    result = json.dumps({ "iv": iv, "ciphertext": ciphertext })
    image_hashes.append([image_entry[0], result, image_entry[2]])