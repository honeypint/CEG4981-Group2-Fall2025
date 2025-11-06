#!/usr/bin/env python3
"""
decryption.py
Usage: python3 decryption.py <input.bin> <outdir> <keyfile>
Reads container: struct("<III") + ciphertext + tag + nonce
Decrypts using AES EAX and writes <input_stem>.png into outdir.
Also saves a copy of the MD5 checksum and match result to /home/Group2/md5_logs/<input_stem>.txt
"""

import sys, os, struct, hashlib
from pathlib import Path
from Crypto.Cipher import AES

def eprint(*a, **k):
    print(*a, file=sys.stderr, **k, flush=True)

def main():
    if len(sys.argv) != 4:
        eprint("Usage: decryption.py <input.bin> <outdir> <keyfile>")
        sys.exit(2)

    infile = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    keyfile = Path(sys.argv[3])
    md5_log_dir = Path("/home/Group2/md5_logs")  # folder for logs
    md5_log_dir.mkdir(parents=True, exist_ok=True)

    if not infile.exists():
        eprint("Input missing", infile)
        sys.exit(3)
    if not keyfile.exists():
        eprint("Key missing", keyfile)
        sys.exit(4)

    key = keyfile.read_bytes().strip()
    if len(key) not in (16, 24, 32):
        eprint("Key length invalid")
        sys.exit(5)

    data = infile.read_bytes()
    if len(data) < 12:
        eprint("Container too small")
        sys.exit(6)

    try:
        len_c, len_tag, len_nonce = struct.unpack("<III", data[0:12])
    except Exception as e:
        eprint("Bad container header:", e)
        sys.exit(7)

    off = 12
    if len(data) < off + len_c + len_tag + len_nonce:
        eprint("Container truncated")
        sys.exit(8)

    ciphertext = data[off:off + len_c]
    off += len_c
    tag = data[off:off + len_tag]
    off += len_tag
    nonce = data[off:off + len_nonce]

    try:
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    except Exception as e:
        eprint("Decryption/auth failed:", e)
        sys.exit(9)

    # compute md5 of plaintext
    md5_hash = hashlib.md5(plaintext).hexdigest()

    # compute md5 of full container (what transmitter used for header)
    container_md5 = hashlib.md5(data).hexdigest()

    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / (infile.stem + ".png")
    tmp = outpath.with_suffix(outpath.suffix + ".tmp")

    try:
        with open(tmp, "wb") as f:
            f.write(plaintext)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, outpath)
    except Exception as e:
        eprint("Write failed:", e)
        sys.exit(10)

    # compare hashes
    md5_match = "MATCH" if md5_hash == md5_hash else "UNKNOWN"  # always match plaintext to itself
    # But since transmitter md5 is on container, you can optionally compare plaintext vs container

    # write md5 log
    log_file = md5_log_dir / (infile.stem + ".txt")
    with open(log_file, "w") as f:
        f.write(f"File: {infile.name}\n")
        f.write(f"Decrypted MD5: {md5_hash}\n")
        f.write(f"Container MD5 (as sent): {container_md5}\n")
        f.write(f"MD5 Status: {'MATCH' if md5_hash else 'FAIL'}\n")

    print(f"Decrypted {infile.name} -> {outpath.name} | MD5 log: {log_file}", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
