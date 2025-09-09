import hashlib
import io # Used for converting image to bytes
from PIL import Image # Python Imaging Library
from Crypto.Cipher import AES # pycrypto AES-128
from Crypto.Random import get_random_bytes # random bytes
from base64 import b64decode # b64decode function
from Crypto.Util.Padding import pad # pad function

# -- Fetch key from a file; the same key used for encryption
with open("./key.txt", 'r') as file:
    key_line = file.readline().strip()
    key = bytes.fromhex(key_line)

# TODO: change file name as needed further down the process
# -- Iterate through the hashes file, process each image individually
with open('image_hashes.txt', 'r') as file:
    i = 0
    for line in file:
        i = i+1
        # -- Fetch data needed for encryption from each file. Format per line is md5hash, ciphertext, tag, nonce
        image_entry = line.split()
        ciphertext = b64decode(image_entry[1])
        tag = b64decode(image_entry[2])
        nonce = b64decode(image_entry[3])
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        # -- Decrypt ciphertext & convert image to proper format. Verify if the ciphertext is legitimate.
        image_data = b64decode(cipher.decrypt(ciphertext))
        try:
            cipher.verify(tag)
            print("Ciphertext decrypted correctly.")
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
            ext = decrypted_image.format.lower() if decrypted_image.format else "png"
            output_path = f"./Decrypted Images/image{i}.{ext}"
            decrypted_image.save(output_path, format=decrypted_image.format)
        else:
            continue # TODO: send over transmission error