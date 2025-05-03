import serial
import json

# Configure this to the other end’s RF‐module serial port
SERIAL_PORT = '/dev/ttyUSB1'
BAUD_RATE = 9600

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                lat = data.get('lat')
                lon = data.get('lon')
                alt = data.get('alt')
                print(f"Received → lat: {lat}, lon: {lon}, alt: {alt}")
            except json.JSONDecodeError:
                print(f"Failed to parse JSON: {line}")
    except KeyboardInterrupt:
        print("Stopping receiver")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
