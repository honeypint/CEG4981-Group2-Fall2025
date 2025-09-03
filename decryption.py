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
    print(key_line)
    key = bytes.fromhex(key_line)
    print(key)