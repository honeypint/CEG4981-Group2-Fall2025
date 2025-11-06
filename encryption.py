#!/usr/bin/env python3
"""
encryption.py
Usage: python3 encryption.py <input.png> <keyfile> <output.bin>
Writes a container:
  struct("<III") -> len_ciphertext, len_tag, len_nonce (12 bytes)
  then ciphertext, tag, nonce
(Transmitter computes md5(container) and includes it in the radio header.)
"""
import sys, os, struct, hashlib
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def eprint(*a, **k):
    print(*a, file=sys.stderr, **k, flush=True)

def main():
    if len(sys.argv) != 4:
        eprint("Usage: encryption.py <input.png> <keyfile> <output.bin>")
        sys.exit(2)
    infile = Path(sys.argv[1])
    keyfile = Path(sys.argv[2])
    outfile = Path(sys.argv[3])

    if not infile.exists():
        eprint("Input not found:", infile); sys.exit(3)
    if not keyfile.exists():
        eprint("Key not found:", keyfile); sys.exit(4)

    key = keyfile.read_bytes().strip()
    if len(key) not in (16,24,32):
        eprint("Key must be 16/24/32 bytes (AES-128/192/256)"); sys.exit(5)

    data = infile.read_bytes()
    if len(data) == 0:
        eprint("Input file empty"); sys.exit(6)

    try:
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        nonce = cipher.nonce
    except Exception as e:
        eprint("Encryption failed:", e); sys.exit(7)

    len_c = len(ciphertext); len_tag = len(tag); len_nonce = len(nonce)
    container = struct.pack("<III", len_c, len_tag, len_nonce) + ciphertext + tag + nonce

    # atomic write
    tmp = outfile.with_suffix(outfile.suffix + ".tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(container); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, outfile)
    except Exception as e:
        eprint("Write failed:", e)
        try:
            tmp.unlink()
        except Exception:
            pass
        sys.exit(8)

    print(f"Encrypted {infile.name} -> {outfile} ({outfile.stat().st_size} bytes)", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
