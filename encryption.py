from PIL import Image # Python Imaging Library
import hashlib # hashlib for MD5
import os # used for file iteration
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Random import get_random_bytes # random bytes

filepath = "./sample-images" # TODO: EDIT TO WHAT IS NEEDED
image_md5s = []
# -- Create md5 hashes for every image and pair them together in a list by [filename, md5]
for file in os.listdir(filepath):
    if file.endswith('.png'):
        image = Image.open(filepath+'/'+file)
        md5hash = hashlib.md5(image.tobytes())
        md5hash = md5hash.hexdigest()
        image_md5s.append([file, image, md5hash])
        continue
    else:
        print("File "+file+" is not a .png")
        continue
for img in image_md5s: # temp
    print(img[0]+": hash "+img[2])

# -- Encrypt these images using AES, making sure they remained paired with their MD5 checksums
image_hashes = []
key = get_random_bytes(32) # TODO: make one permanent key that is on both sides. keep with ciphertext, nonce, tag
cipher = AES.new(key, AES.MODE_EAX)
nonce = cipher.nonce
for image_entry in image_md5s:
    ciphertext, tag = cipher.encrypt_and_digest(image_entry[1])
    image_hashes.append(image_entry[0], [nonce, ciphertext, tag], image_entry[2])

for test in image_hashes:
    print(test)