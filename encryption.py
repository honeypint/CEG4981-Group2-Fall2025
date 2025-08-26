from PIL import Image # Python Imaging Library
import hashlib # hashlib for MD5
#from Crypto.Cipher import AES # pycrypto AES-128
#from Crypto.Random import get_random_bytes # random bytes

# TODO: make iterate through an entire image file
image = Image.open('./sample-images/image13.png')
md5hash = hashlib.md5(image.tobytes())
print(md5hash)