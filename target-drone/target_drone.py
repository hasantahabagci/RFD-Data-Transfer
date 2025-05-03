import serial
import json
import time
import random  # Replace this with your actual GPS source

# Open serial port to RFD modem
ser = serial.Serial('COM3', 57600, timeout=1)  # Adjust COM port for your setup

try:
    while True:
        # Simulated real-time location data (replace with actual GPS readings)
        location_data = {
            "lat": round(37.7749 + random.uniform(-0.001, 0.001), 6),
            "lon": round(-122.4194 + random.uniform(-0.001, 0.001), 6),
            "alt": round(30.5 + random.uniform(-1, 1), 2)
        }

        # Serialize to JSON
        json_data = json.dumps(location_data)

        # Send over RFD
        ser.write((json_data + '\n').encode('utf-8'))  # Newline helps the receiver know when message ends
        print(f"Sent: {json_data}")

        time.sleep(1)  # Send every second
except KeyboardInterrupt:
    print("Transmission stopped.")
finally:
    ser.close()