from PIL import Image # Python Imaging Library
import hashlib # hashlib for MD5
import os # used for file iteration
#from Crypto.Cipher import AES # pycrypto AES-128
#from Crypto.Random import get_random_bytes # random bytes

filepath = "./sample-images" # TODO: EDIT TO WHAT IS NEEDED
imagehashes = []
# Create md5 hashes for every image and pair them together in a list by [filename, md5]
for file in os.listdir(filepath):
    if file.endswith('.png'):
        image = Image.open(filepath+'/'+file)
        md5hash = hashlib.md5(image.tobytes())
        md5hash = md5hash.hexdigest()
        imagehashes.append([file, md5hash])
        continue
    else:
        print("File "+file+" is not a .png")
        continue
for img in imagehashes:
    print(img[0]+": hash "+img[1])