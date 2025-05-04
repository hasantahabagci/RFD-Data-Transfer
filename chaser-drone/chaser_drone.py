#!/usr/bin/env python3
import json, serial

PORT = "COM5"        # Windows example – adjust as needed
BAUD = 57600

def main():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    try:
        while True:
            line = ser.readline()          # Blocks until '\n' or timeout
            if not line:
                continue                   # Timeout – no data this cycle
            try:
                pkt = json.loads(line)
                print(f"Lat: {pkt['lat']:.6f}  Lon: {pkt['lon']:.6f}  Alt: {pkt['alt']:.1f} m")
            except json.JSONDecodeError:
                # Corrupt or partial line – ignore or log
                continue
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

if __name__ == "__main__":
    main()
