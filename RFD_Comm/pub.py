
import serial
import time
import random
import json

# Configure the serial port (update the port and baud rate as needed)
ser = serial.Serial(
    port='/dev/tty.usbserial-AI055WQ5',  # Update this to your serial port
    baudrate=57600,       # Default baudrate for RFD900x
    timeout=1
)

def generate_data():
    location_data = [
        {
            "takim_numarasi": "Biz",
            "iha_enlem": round(random.uniform(40, 42), 6),
            "iha_boylam": round(random.uniform(35, 37), 6),
            "iha_irtifa": round(random.uniform(30, 50), 2),
            "iha_dikilme": round(random.uniform(-10, 10), 2),
            "iha_yonelme": round(random.uniform(100, 200), 2),
            "iha_yatis": round(random.uniform(-40, 40), 2),
            "iha_hizi": round(random.uniform(30, 50), 2),
            "zaman_farki": random.randint(200, 500)
        },
    ]

    focus_data = [
        {
            "kilitlenmeBaslangicZamani": {
                "saat": 11,
                "dakika": 40,
                "saniye": 51,
                "milisaniye": 478
            },
            "kilitlenmeBitisZamani": {
                "saat": 11,
                "dakika": 41,
                "saniye": 3,
                "milisaniye": 141
            },
            "otonom_kilitlenme": 1
        }
    ]

    kamikaze_data = [
        {
            "kamikazeBaslangicZamani": {
                "saat": 11,
                "dakika": 40,
                "saniye": 51,
                "milisaniye": 478
            },
            "kamikazeBitisZamani": {
                "saat": 11,
                "dakika": 41,
                "saniye": 3,
                "milisaniye": 141
            },
            "qrMetni": "teknofest2023"
        }
    ]

    data = {
        "location_data": location_data,
        "focus_data": focus_data,
        "kamikaze_data": kamikaze_data
    }

    return json.dumps(data)

try:
    while True:
        data = generate_data()
        ser.write((data + '\n').encode('utf-8'))  # Send data over serial with newline delimiter
        print(f"Sent: {data}")
        time.sleep(0.5)  # Wait for a second before sending next data
except KeyboardInterrupt:
    print("Transmission stopped.")
finally:
    ser.close()  # Close the serial port