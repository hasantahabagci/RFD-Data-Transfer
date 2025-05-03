import serial
import json

# Open serial port to RFD modem
ser = serial.Serial('COM4', 57600, timeout=5)  # Adjust COM port for your receiver

try:
    while True:
        incoming_data = ser.readline().decode('utf-8').strip()

        if incoming_data:
            try:
                location = json.loads(incoming_data)
                print(f"Received → lat: {location['lat']}, lon: {location['lon']}, alt: {location['alt']}m")
            except json.JSONDecodeError:
                print(f"Invalid JSON: {incoming_data}")
except KeyboardInterrupt:
    print("Reception stopped.")
finally:
    ser.close()
