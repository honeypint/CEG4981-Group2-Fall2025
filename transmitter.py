#!/usr/bin/env python3
"""
transmitter.py
Sends .bin container files from ENCRYPTED_DIR reliably with selective retransmit.
Usage: python3 transmitter.py --mode fast|robust
"""
import os, time, struct, argparse, subprocess, hashlib
from pathlib import Path
from RF24 import RF24, RF24_1MBPS, RF24_PA_LOW
try:
    from RF24 import RF24_2MBPS, RF24_PA_MAX
except Exception:
    RF24_2MBPS = None; RF24_PA_MAX = None

BASE = Path("/home/Group2")
SAMPLE_DIR = BASE/"sample-images"
ENCRYPTED_DIR = BASE/"encrypted_txt"
SENT_HASHES_FILE = ENCRYPTED_DIR/"sent_hashes.txt"
KEY_FILE = BASE/"key.txt"
ENCRYPT_SCRIPT = BASE/"encryption.py"
VENV_PY = BASE/"rf24env/bin/python3"

CE_PIN, CSN_PIN = 17, 0
CHANNEL = 90
PIPE_TX = 0xF0F0F0F0E1  # transmitter writes here
PIPE_RX = 0xF0F0F0F0D2  # transmitter listens here (status)

PT_HEADER = b'\x01'; PT_DATA = b'\x02'; PT_EOF = b'\x03'; PT_STATUS = b'\x04'

MAX_PAYLOAD = 32
CHUNK_PAYLOAD_SIZE = MAX_PAYLOAD - (1 + 4 + 2)  # type + seq + len

HEADER_REPEATS = 3
CHUNK_RETRY_LIMIT = 6
INTER_CHUNK_PAUSE_FAST = 0.0005
INTER_CHUNK_PAUSE_ROBUST = 0.002
STATUS_TIMEOUT = 3.0
STATUS_LISTEN_STARTUP = 0.02
MAX_NACK_ROUNDS = 10
RETRANSMIT_PER_CHUNK = 4
HEARTBEAT_INTERVAL = 30.0

def init_radio(mode):
    r = RF24(CE_PIN, CSN_PIN)
    if not r.begin(): raise SystemExit("radio.begin failed")
    r.enableDynamicPayloads()
    if mode == "fast" and RF24_2MBPS:
        r.setDataRate(RF24_2MBPS)
    else:
        r.setDataRate(RF24_1MBPS)
    if mode == "fast" and RF24_PA_MAX:
        r.setPALevel(RF24_PA_MAX)
    else:
        r.setPALevel(RF24_PA_LOW)
    r.setChannel(CHANNEL)
    r.setAutoAck(True)
    r.setRetries(15,15)
    r.openWritingPipe(PIPE_TX)
    r.openReadingPipe(1, PIPE_RX)
    r.stopListening()
    print("[transmitter] radio init", flush=True)
    return r

def load_sent_hashes():
    ENCRYPTED_DIR.mkdir(exist_ok=True)
    sent = set()
    if SENT_HASHES_FILE.exists():
        try:
            with open(SENT_HASHES_FILE, "r") as fh:
                for line in fh:
                    h = line.strip()
                    if h:
                        sent.add(h)
        except Exception as e:
            print("[transmitter] could not read sent_hashes:", e, flush=True)
    # also add md5s of any .bin.sent files we find (defensive)
    for p in ENCRYPTED_DIR.glob("*.bin.sent"):
        try:
            data = p.read_bytes()
            md5hex = hashlib.md5(data).hexdigest()
            if md5hex not in sent:
                sent.add(md5hex)
        except Exception as e:
            print(f"[transmitter] could not hash {p}: {e}", flush=True)
    print(f"[transmitter] loaded {len(sent)} sent hashes", flush=True)
    return sent

def record_sent_hash(md5hex):
    try:
        with open(SENT_HASHES_FILE, "a") as fh:
            fh.write(md5hex + "\n")
    except Exception as e:
        print("[transmitter] failed to append sent hash:", e, flush=True)

def run_encrypt_if_needed(png):
    ENCRYPTED_DIR.mkdir(exist_ok=True)
    out = ENCRYPTED_DIR / (png.stem + ".bin")
    if out.exists() and out.stat().st_mtime >= png.stat().st_mtime:
        return out
    # call your encryption script which writes container to 'out'
    subprocess.run([str(VENV_PY), str(ENCRYPT_SCRIPT), str(png), str(KEY_FILE), str(out)], check=True)
    print(f"[transmitter] Encrypted {png.name} -> {out.name}", flush=True)
    return out

def send_chunks(radio, data, mode):
    total_bytes = len(data)
    total_chunks = (total_bytes + CHUNK_PAYLOAD_SIZE - 1) // CHUNK_PAYLOAD_SIZE
    md5 = hashlib.md5(data).digest()
    header = PT_HEADER + struct.pack("<II", total_bytes, total_chunks) + md5
    for i in range(HEADER_REPEATS):
        ok = radio.write(header)
        print(f"[transmitter] header write #{i+1} success={ok}", flush=True)
        time.sleep(0.01)
    for seq in range(total_chunks):
        off = seq * CHUNK_PAYLOAD_SIZE
        chunk = data[off:off+CHUNK_PAYLOAD_SIZE]
        pkt = PT_DATA + struct.pack("<IH", seq, len(chunk)) + chunk
        sent = False
        for attempt in range(CHUNK_RETRY_LIMIT):
            try:
                ok = radio.write(pkt)
            except Exception as e:
                ok = False
                print(f"[transmitter] chunk write exception seq={seq}: {e}", flush=True)
            if ok:
                sent = True
                break
            time.sleep(0.002*(1+attempt*0.5))
        if not sent:
            print(f"[transmitter] Chunk {seq} failed after retries", flush=True)
        if seq and seq % 1000 == 0:
            print(f"[transmitter] sent chunk {seq}/{total_chunks}", flush=True)
        time.sleep(INTER_CHUNK_PAUSE_FAST if mode=="fast" else INTER_CHUNK_PAUSE_ROBUST)
    ok = radio.write(PT_EOF)
    print(f"[transmitter] sent EOF (success={ok})", flush=True)
    return total_chunks, md5  # md5 is bytes

def listen_status(radio, timeout=STATUS_TIMEOUT):
    radio.startListening()
    time.sleep(STATUS_LISTEN_STARTUP)
    t0 = time.time(); pkt = None
    while time.time() - t0 < timeout:
        try:
            if radio.available():
                size = radio.getDynamicPayloadSize()
                pkt = radio.read(size)
                break
        except Exception as e:
            print("[transmitter] listen exception:", e, flush=True)
            break
        time.sleep(0.01)
    radio.stopListening()
    return pkt

def send_file(radio, path, mode, sent_hashes):
    data = path.read_bytes()
    total_chunks, md5_bytes = send_chunks(radio, data, mode)
    md5hex = hashlib.md5(data).hexdigest()
    # prepare chunk list for retransmit
    chunks = [data[i*CHUNK_PAYLOAD_SIZE:(i+1)*CHUNK_PAYLOAD_SIZE] for i in range(total_chunks)]

    nack_round = 0; status = None
    while nack_round < MAX_NACK_ROUNDS:
        pkt = listen_status(radio)
        if not pkt:
            print("[transmitter] no status received (timeout)", flush=True)
            break
        if pkt[0:1] != PT_STATUS:
            print("[transmitter] non-status packet received, ignoring", flush=True)
            break
        msg = pkt[1:].decode(errors="ignore")
        print(f"[transmitter] Got STATUS: {msg}", flush=True)
        if msg.startswith("OK"):
            status = "OK"; break
        if msg.startswith("NACK"):
            parts = msg.split(",")
            missing = [int(x) for x in parts[1:] if x.isdigit()]
            print(f"[transmitter] NACK round {nack_round+1}: {len(missing)} missing", flush=True)
            for seq in missing:
                if seq < 0 or seq >= len(chunks):
                    continue
                pkt = PT_DATA + struct.pack("<IH", seq, len(chunks[seq])) + chunks[seq]
                sent = False
                for attempt in range(RETRANSMIT_PER_CHUNK):
                    try:
                        ok = radio.write(pkt)
                    except Exception as e:
                        ok = False
                        print(f"[transmitter] retransmit write exception seq {seq}: {e}", flush=True)
                    if ok:
                        sent = True
                        break
                    time.sleep(0.01 * (attempt+1))
                if not sent:
                    print(f"[transmitter] retransmit seq {seq} failed after {RETRANSMIT_PER_CHUNK} attempts", flush=True)
            radio.write(PT_EOF)
            nack_round += 1
            continue
        status = msg; break

    if status == "OK":
        # atomically rename to .bin.sent
        try:
            sent_path = Path(str(path) + ".sent")
            os.replace(str(path), str(sent_path))
            print(f"[transmitter] Sent {path.name} OK -> renamed to {sent_path.name}", flush=True)
        except Exception as e:
            print("[transmitter] rename error:", e, flush=True)
        # persist md5 so restart knows it's sent
        if md5hex not in sent_hashes:
            record_sent_hash(md5hex)
            sent_hashes.add(md5hex)
        return True
    else:
        print(f"[transmitter] Did not confirm {path.name}, final status={status}", flush=True)
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["fast","robust"], default="fast")
    args = ap.parse_args()
    radio = init_radio(args.mode)

    sent_hashes = load_sent_hashes()
    last_hb = time.time()
    while True:
        try:
            # ensure encrypted dir exists
            ENCRYPTED_DIR.mkdir(exist_ok=True)
            # encrypt PNGs if needed
            for png in SAMPLE_DIR.glob("*.png"):
                try:
                    run_encrypt_if_needed(png)
                except Exception as e:
                    print("[transmitter] encrypt error:", e, flush=True)

            # scan for .bin files (ignore .bin.sent)
            for f in sorted(ENCRYPTED_DIR.glob("*.bin")):
                # skip files which are actually .bin.sent (glob won't match .bin.sent),
                # but double-check: ignore any path that endswith .bin.sent just in case
                if str(f).endswith(".bin.sent"):
                    continue
                if not f.exists():
                    continue
                # compute md5 and skip if already sent
                try:
                    data = f.read_bytes()
                except Exception as e:
                    print(f"[transmitter] failed to read {f}: {e}", flush=True)
                    continue
                md5hex = hashlib.md5(data).hexdigest()
                if md5hex in sent_hashes:
                    # Already confirmed earlier; optionally rename or skip
                    print(f"[transmitter] skipping already-confirmed {f.name}", flush=True)
                    # if there is no .sent file, create one (safe) - do atomic replace
                    sent_candidate = Path(str(f) + ".sent")
                    if not sent_candidate.exists():
                        try:
                            os.replace(str(f), str(sent_candidate))
                            print(f"[transmitter] moved {f.name} -> {sent_candidate.name}", flush=True)
                        except Exception as e:
                            # if move fails, leave original (no big deal)
                            print(f"[transmitter] could not move confirmed file: {e}", flush=True)
                    continue
                # send it
                try:
                    send_file(radio, f, args.mode, sent_hashes)
                except Exception as e:
                    print(f"[transmitter] send_file exception for {f}: {e}", flush=True)
            # heartbeat
            if time.time() - last_hb > HEARTBEAT_INTERVAL:
                print("[transmitter] heartbeat - running", flush=True)
                last_hb = time.time()
            time.sleep(1)
        except KeyboardInterrupt:
            print("[transmitter] interrupted", flush=True)
            break
        except Exception as e:
            print("[transmitter] main loop exception:", e, flush=True)
            time.sleep(1)

if __name__=="__main__":
    main()
