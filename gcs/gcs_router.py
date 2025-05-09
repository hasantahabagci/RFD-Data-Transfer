import serial
import time
import json

target_radio = serial.Serial("/dev/tty.usbserial-AL05THXK",115200)
chaser_radio = serial.Serial("/dev/tty.usbserial-AI055WQ5",115200)
print("Connected to target drone stream!")
while True:
    data = target_radio.readline()
    if not data:
        continue
    try:
        location = json.loads(data)
    except json.JSONDecodeError:
        continue
    lat = location.get('lat')
    lon = location.get('lon')
    alt = location.get('alt')
    if lat is None or lon is None or alt is None or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or not isinstance(alt, (int, float)) or lat < -90 or lat > 90 or lon < -180 or lon > 180:
        continue
    print(f"Received → lat: {lat}, lon: {lon}, alt: {alt}")
    
    chaser_radio.write(data)
    # line = target_radio.readline().decode('utf-8').strip()
    # if not line:
    #     continue
    # print(f"Received line: {line}")
    # location = json.loads(line)
    # lat = location.get('lat')
    # lon = location.get('lon')
    # alt = location.get('alt')
    # print(f"Received → lat: {lat}, lon: {lon}, alt: {alt}")
