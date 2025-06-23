import serial
import time
import json
import threading

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

target_radio = serial.Serial("/dev/tty.usbserial-B000IQDA",115200)
chaser_radio = serial.Serial("/dev/tty.usbserial-AI055WQ5",115200)
print("Connected to target drone stream!")

def inter_receiver_thread():
    while True:
        inter_data = chaser_radio.readline()
        if not inter_data:
            continue
        try:
            inter_info = json.loads(inter_data)
            print(bcolors.OKGREEN + f"Received inter data: {inter_info}" + bcolors.ENDC)
        except json.JSONDecodeError:
            print("Error decoding inter data")

# Start the inter receiver thread
inter_thread = threading.Thread(target=inter_receiver_thread)
inter_thread.daemon = True  # Ensure thread exits when main program exits
inter_thread.start()

while True:
    data = target_radio.readline()
    # chaser_data = chaser_radio.readline().decode('utf-8').strip()
    if not data:
        continue
    try:
        location = json.loads(data)
        # inter_info = json.loads(chaser_data)
    except json.JSONDecodeError:
        continue

    # inter_data = chaser_radio.readline()
    # if inter_info:
    #     try:
    #         print(f"Received inter data: {inter_info}")
    #     except json.JSONDecodeError:
    #         print("Error decoding inter data")

    lat = location.get('lat')
    lon = location.get('lon')
    alt = location.get('alt')
    vx = location.get('vx')
    vy = location.get('vy')
    vz = location.get('vz')
    if lat is None or lon is None or alt is None or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or not isinstance(alt, (int, float)) or lat < -90 or lat > 90 or lon < -180 or lon > 180:
        continue
    print(bcolors.OKCYAN + f"Received Target Data → lat: {lat}, lon: {lon}, alt: {alt}, vx: {vx}, vy: {vy}, vz: {vz}" + bcolors.ENDC)
    
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
