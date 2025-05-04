#!/usr/bin/env python3
import json, time, serial, random   # ← replace random with your real data source

PORT      = "/dev/ttyUSB0"   # Linux / Raspberry Pi example
BAUD      = 57600
SEND_HZ   = 5                # 5 packets · s⁻¹ → 200 ms period

def get_flight_sample():
    """
    Replace this stub with whatever supplies your real telemetry:
      * `vehicle.location.global_frame` from Drone‑Kit
      * MAVLink message
      * Sensor fusion output, etc.
    """
    lat  = 40.712345 + random.uniform(-1e-6, 1e-6)
    lon  = 29.123456 + random.uniform(-1e-6, 1e-6)
    alt  = 120.0     + random.uniform(-0.5, 0.5)
    return {"lat": lat, "lon": lon, "alt": alt}

def main():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    period = 1 / SEND_HZ
    try:
        while True:
            sample = get_flight_sample()
            payload = json.dumps(sample).encode("utf-8") + b"\n"
            ser.write(payload)
            # Optional flush for USB‑CDC adapters
            ser.flush()
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

if __name__ == "__main__":
    main()
