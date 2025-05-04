#!/usr/bin/env python3
import json, serial, time

PORT = "/dev/tty.usbserial-A106AUJN"    # ★ adjust (COMx on Windows)
BAUD = 57600

def main():
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        # Optional: clear any junk still in the buffer
        ser.reset_input_buffer()

        while True:
            raw = ser.readline()          # bytes   (blocks ≤ timeout)
            if not raw:
                continue                  # timeout, no data

            # 1) decode   2) strip newline/CR
            try:
                line = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                # Non‑UTF‑8 garbage – just drop it
                continue

            # Empty after stripping? Ignore.
            if not line:
                continue

            # Parse JSON
            try:
                pkt = json.loads(line)
            except json.JSONDecodeError:
                # Received something but it wasn’t valid JSON
                continue

            # At this point we trust pkt
            print(f"{time.strftime('%H:%M:%S')}  "
                  f"Lat {pkt['lat']:.6f}  Lon {pkt['lon']:.6f}  Alt {pkt['alt']:.1f} m")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
