#!/usr/bin/env python3
"""
receiver.py — Phase 2 reliable ARQ with selective retransmit
Usage: python3 receiver.py --mode fast|robust
"""

import time, struct, argparse, subprocess, hashlib
from pathlib import Path
from RF24 import RF24, RF24_PA_HIGH, RF24_1MBPS
try:
    from RF24 import RF24_PA_MAX, RF24_2MBPS
except Exception:
    RF24_PA_MAX=None; RF24_2MBPS=None

BASE=Path("/home/Group2")
RECV_DIR=BASE/"received_txt"
DECRYPT_DIR=BASE/"decrypted_images"
KEY_FILE=BASE/"key.txt"
DECRYPT_SCRIPT=BASE/"decryption.py"
VENV_PY=BASE/"rf24env/bin/python3"

CE_PIN,CSN_PIN=17,0
CHANNEL=90
PIPE_RX,PIPE_TX=0xF0F0F0F0E1,0xF0F0F0F0D2

PT_HEADER=b'\x01'; PT_DATA=b'\x02'; PT_EOF=b'\x03'; PT_STATUS=b'\x04'

MAX_PAYLOAD = 32
CHUNK_PAYLOAD_SIZE = MAX_PAYLOAD - (1 + 4 + 2)  # type + seq + len
EOF_GRACE=2.0  # stop if no chunks for 2s after EOF
MAX_NACK_ROUNDS = 3  # mirror transmitter


def init_radio(mode):
    r=RF24(CE_PIN,CSN_PIN)
    if not r.begin(): raise SystemExit("radio.begin failed")
    r.enableDynamicPayloads()
    if mode=="fast" and RF24_2MBPS: r.setDataRate(RF24_2MBPS)
    else: r.setDataRate(RF24_1MBPS)
    if mode=="fast" and RF24_PA_MAX: r.setPALevel(RF24_PA_MAX)
    else: r.setPALevel(RF24_PA_HIGH)
    r.setChannel(CHANNEL); r.setAutoAck(True)
    r.setRetries(3 if mode=="fast" else 10, 5 if mode=="fast" else 15)
    r.openWritingPipe(PIPE_TX); r.openReadingPipe(1,PIPE_RX)
    r.startListening(); return r


def wait_pkt(radio, timeout=None):
    t0=time.time()
    while True:
        if radio.available():
            size=radio.getDynamicPayloadSize()
            return radio.read(size)
        if timeout and time.time()-t0>timeout:
            return None
        time.sleep(0.001)


def send_status(radio, msg):
    pkt = PT_STATUS + msg.encode()
    try:
        sent = radio.write(pkt)
        print(f"[receiver] send_status attempt 1 msg='{msg}' success={sent}", flush=True)
    except Exception as e:
        print("[receiver] Status send failed:", e, flush=True)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=["fast","robust"],default="robust")
    args=ap.parse_args(); radio=init_radio(args.mode)
    RECV_DIR.mkdir(exist_ok=True); DECRYPT_DIR.mkdir(exist_ok=True)

    # track received hashes to avoid duplicates
    hashes_file = RECV_DIR / "received_hashes.txt"
    seen = set()
    if hashes_file.exists():
        seen.update(hashes_file.read_text().splitlines())

    last_hdr_msg = 0
    while True:
        now = time.time()
        if now - last_hdr_msg > 10:
            print("[receiver] waiting for header...", flush=True)
            last_hdr_msg = now

        hdr = wait_pkt(radio, timeout=2)
        if not hdr or hdr[0:1] != PT_HEADER:
            continue

        # parse header
        try:
            total_bytes, total_chunks = struct.unpack("<II", hdr[1:9])
            md5_expect = hdr[9:25].hex()
        except Exception as e:
            print("[receiver] Malformed header, skipping:", e, flush=True)
            continue

        print(f"[receiver] Receiving {total_chunks} chunks ({total_bytes} bytes) md5={md5_expect}", flush=True)

        chunks = {}        # seq -> bytes
        last_rx = time.time()
        got_eof = False
        nack_round = 0

        while True:
            pkt = wait_pkt(radio, timeout=1)
            if pkt:
                last_rx = time.time()
                if pkt[0:1] == PT_DATA:
                    if len(pkt) >= 7:
                        seq = struct.unpack("<I", pkt[1:5])[0]
                        clen = struct.unpack("<H", pkt[5:7])[0]
                        payload = pkt[7:7+clen]
                        if len(payload) == clen:
                            chunks[seq] = payload
                        else:
                            print(f"[receiver] chunk length mismatch seq={seq}", flush=True)
                    else:
                        print("[receiver] Malformed DATA pkt, ignoring", flush=True)
                elif pkt[0:1] == PT_EOF:
                    got_eof = True

            # if all chunks collected
            if len(chunks) >= total_chunks:
                assembled = b''.join(chunks.get(i, b'') for i in range(total_chunks))
                data = assembled[:total_bytes]
                calc = hashlib.md5(data).hexdigest()
                if calc == md5_expect:
                    if calc in seen:
                        print("[receiver] duplicate file detected, skipping save/decrypt", flush=True)
                        send_status(radio, "OK")
                    else:
                        ts = int(time.time())
                        out = RECV_DIR / f"received_{ts}.bin"
                        out.write_bytes(data)
                        with open(hashes_file, "a") as hf:
                            hf.write(calc + "\n")
                        seen.add(calc)
                        print(f"[receiver] MD5 OK: {out.name}", flush=True)
                        send_status(radio, "OK")
                        try:
                            subprocess.run([str(VENV_PY), str(DECRYPT_SCRIPT), str(out), str(DECRYPT_DIR), str(KEY_FILE)], check=False)
                            print(f"[receiver] attempted decrypt -> {DECRYPT_DIR}", flush=True)
                        except Exception as e:
                            print("[receiver] decrypt error:", e, flush=True)
                    break
                else:
                    print("[receiver] all chunks present but MD5 mismatch; request full retransmit", flush=True)
                    missing = list(range(total_chunks))
                    seqs = ",".join(str(i) for i in missing[:200])
                    send_status(radio, "NACK," + seqs)
                    nack_round += 1
                    got_eof = False
                    last_rx = time.time()
                    if nack_round > MAX_NACK_ROUNDS:
                        print("[receiver] max nack rounds exceeded, dropping", flush=True)
                        send_status(radio, "FAIL")
                        break
                    continue

            if got_eof and (time.time() - last_rx) > EOF_GRACE:
                missing = [i for i in range(total_chunks) if i not in chunks]
                assembled = b''.join(chunks.get(i, b'') for i in range(total_chunks))
                data = assembled[:total_bytes]
                calc = hashlib.md5(data).hexdigest()
                if not missing and calc == md5_expect:
                    if calc in seen:
                        print("[receiver] duplicate file detected, skipping save/decrypt", flush=True)
                        send_status(radio, "OK")
                    else:
                        ts = int(time.time())
                        out = RECV_DIR / f"received_{ts}.bin"
                        out.write_bytes(data)
                        with open(hashes_file, "a") as hf:
                            hf.write(calc + "\n")
                        seen.add(calc)
                        print(f"[receiver] MD5 OK: {out.name}", flush=True)
                        send_status(radio, "OK")
                        try:
                            subprocess.run([str(VENV_PY), str(DECRYPT_SCRIPT), str(out), str(DECRYPT_DIR), str(KEY_FILE)], check=False)
                            print(f"[receiver] attempted decrypt -> {DECRYPT_DIR}", flush=True)
                        except Exception as e:
                            print("[receiver] decrypt error:", e, flush=True)
                    break
                elif missing:
                    seqs = ",".join(str(i) for i in missing[:200])
                    print(f"[receiver] missing {len(missing)} chunks; requesting retransmit", flush=True)
                    send_status(radio, "NACK," + seqs)
                    nack_round += 1
                    got_eof = False
                    last_rx = time.time()
                    if nack_round > MAX_NACK_ROUNDS:
                        print("[receiver] max nack rounds exceeded, dropping", flush=True)
                        send_status(radio, "FAIL")
                        break
                else:
                    print("[receiver] no missing chunks but MD5 mismatch — requesting full retransmit", flush=True)
                    missing_all = list(range(total_chunks))
                    seqs = ",".join(str(i) for i in missing_all[:200])
                    send_status(radio, "NACK," + seqs)
                    nack_round += 1
                    got_eof = False
                    last_rx = time.time()
                    if nack_round > MAX_NACK_ROUNDS:
                        print("[receiver] max nack rounds exceeded on MD5 mismatch, dropping", flush=True)
                        send_status(radio, "FAIL")
                        break
        time.sleep(0.01)
        radio.startListening()


if __name__=="__main__":
    main()
