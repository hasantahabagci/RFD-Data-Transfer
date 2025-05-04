#!/usr/bin/env python3
import json, time, serial, random      # replace random with real telemetry

PORT      = "/dev/ttyUSB0"             # ★ adjust
BAUD      = 57600
SEND_HZ   = 5

def get_sample():
    # stub – swap in your real source
    return {
        "lat": 41.085000 + random.uniform(-1e-6, 1e-6),
        "lon": 29.044000 + random.uniform(-1e-6, 1e-6),
        "alt": 120.0     + random.uniform(-0.5, 0.5),
    }

def main():
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        period = 1 / SEND_HZ
        while True:
            pkt = json.dumps(get_sample()).encode() + b"\n"
            ser.write(pkt)
            time.sleep(period)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
