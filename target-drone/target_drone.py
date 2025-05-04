import serial
import json
import time
import random  # Replace this with your actual GPS source
from mav_handler import MAVHandler

drone = MAVHandler("127.0.0.1:14538")  

# Open serial port to RFD modem
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)  # Adjust COM port for your setup

try:
    while True:
        # Simulated real-time location data (replace with actual GPS readings)
        lat, lon, alt = drone.get_location()
        location_data = {
            "lat": lat,
            "lon": lon,
            "alt": alt
        }

        # Serialize to JSON
        json_data = json.dumps(location_data)

        # Send over RFD
        ser.write((json_data + '\n').encode('utf-8'))  # Newline helps the receiver know when message ends
        print(f"Sent: {json_data}")

        time.sleep(0.01)  # Send every second
except KeyboardInterrupt:
    print("Transmission stopped.")
finally:
    ser.close()