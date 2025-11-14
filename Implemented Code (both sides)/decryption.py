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

    # compute md5 of plaintext (informational — only useful if you had a pre-transmit md5)
    plaintext_md5 = hashlib.md5(plaintext).hexdigest()

    # compute md5 of full container (what transmitter used for header)
    container_md5 = hashlib.md5(data).hexdigest()

    # optional expected container md5 passed by receiver.py (hex string)
    expected_md5 = None
    if len(sys.argv) == 5:
        expected_md5 = sys.argv[4].strip().lower()

    # Decide MD5 status:
    # - If expected_md5 provided: compare it to container_md5 -> authoritative result
    # - Else: we cannot verify against header; mark as UNKNOWN but still log md5s
    if expected_md5:
        md5_status = "MATCH" if container_md5 == expected_md5 else "MISMATCH"
    else:
        md5_status = "UNKNOWN"  # decryption invoked without header md5 to compare to

    # write md5 log
    log_file = md5_log_dir / (infile.stem + ".txt")
    with open(log_file, "w") as f:
        f.write(f"File: {infile.name}\n")
        f.write(f"Container MD5 (computed): {container_md5}\n")
        if expected_md5:
            f.write(f"Container MD5 (expected): {expected_md5}\n")
        f.write(f"Plaintext MD5 (informational): {plaintext_md5}\n")
        f.write(f"MD5 Status: {md5_status}\n")
    

    print(f"Decrypted {infile.name} -> {outpath.name} | MD5 log: {log_file}", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
