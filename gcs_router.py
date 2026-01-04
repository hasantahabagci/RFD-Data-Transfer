import serial
import time
import json
import threading
import tkinter as tk
from tkinter import font

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
#chaser_radio = serial.Serial("/dev/ttyUSB0",115200)
chaser_radio = serial.Serial("/dev/tty.usbserial-AI055XQJ",115200)

print("Connected to target drone stream!")

alts = {"target" : 0,
        "chaser" : 0}

def inter_receiver_thread():
    while True:
        inter_data = chaser_radio.readline()
        if not inter_data:
            continue
        try:
            inter_str = inter_data.decode('utf-8', errors='ignore').strip()
            if not inter_str:
                continue
            inter_info = json.loads(inter_str)
            if "alt" in inter_info:
                alts['chaser'] = inter_info["alt"]
                print(bcolors.OKCYAN + f"Received inter data: {inter_info}" + bcolors.ENDC)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, KeyError):
            continue



# Start the inter receiver thread
inter_thread = threading.Thread(target=inter_receiver_thread)
inter_thread.daemon = True  # Ensure thread exits when main program exits
inter_thread.start()


def target_receiver_thread():
    while True:
        try:
            data = target_radio.readline()
            # chaser_data = chaser_radio.readline().decode('utf-8').strip()
            if not data:
                continue
            try:
                data_str = data.decode('utf-8', errors='ignore').strip()
                if not data_str:
                    continue
                location = json.loads(data_str)
                # inter_info = json.loads(chaser_data)
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
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
            #if lat is None or lon is None or alt is None or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or not isinstance(alt, (int, float)) or lat < -90 or lat > 90 or lon < -180 or lon > 180:
            if lat is None or lon is None or alt is None or vx is None or vy is None or vz is None or \
                not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or not isinstance(alt, (int, float)) or \
                not isinstance(vx, (int, float)) or not isinstance(vy, (int, float)) or not isinstance(vz, (int, float)) or \
                lat < -90 or lat > 90 or lon < -180 or lon > 180:
                continue
            print(bcolors.OKGREEN + bcolors.BOLD + f"Received Target Data → lat: {lat}, lon: {lon}, alt: " +bcolors.UNDERLINE + bcolors.HEADER + f"{alt}"+bcolors.ENDC+bcolors.OKGREEN + bcolors.BOLD +f", vx: {vx}, vy: {vy}, vz: {vz}" + bcolors.ENDC)
            alts['target'] = alt
            chaser_radio.write(data)
            print(bcolors.WARNING + f"ALT Diff: {alts['target']-alts['chaser']}" + bcolors.ENDC)
            # line = target_radio.readline().decode('utf-8').strip()
            # if not line:
            #     continue
            # print(f"Received line: {line}")
            # location = json.loads(line)
            # lat = location.get('lat')
            # lon = location.get('lon')
            # alt = location.get('alt')
            # print(f"Received → lat: {lat}, lon: {lon}, alt: {alt}")
        except (UnicodeDecodeError, ValueError, KeyError, AttributeError) as e:
            continue
        except Exception as e:
            continue


# GUI Setup
root = tk.Tk()
root.title("GCS Router - Altitude Monitor")
root.geometry("800x600")
root.configure(bg='black')

# Large fonts
big_font = font.Font(family='Arial', size=72, weight='bold')
label_font = font.Font(family='Arial', size=24, weight='bold')
diff_font = font.Font(family='Arial', size=48, weight='bold')

# Target altitude
target_frame = tk.Frame(root, bg='black')
target_frame.pack(pady=20)
tk.Label(target_frame, text="TARGET ALTITUDE", font=label_font, fg='green', bg='black').pack()
target_label = tk.Label(target_frame, text="0.0", font=big_font, fg='green', bg='black')
target_label.pack()

# Chaser altitude
chaser_frame = tk.Frame(root, bg='black')
chaser_frame.pack(pady=20)
tk.Label(chaser_frame, text="CHASER ALTITUDE", font=label_font, fg='cyan', bg='black').pack()
chaser_label = tk.Label(chaser_frame, text="0.0", font=big_font, fg='cyan', bg='black')
chaser_label.pack()

# Altitude difference
diff_frame = tk.Frame(root, bg='black')
diff_frame.pack(pady=20)
tk.Label(diff_frame, text="ALTITUDE DIFFERENCE", font=label_font, fg='yellow', bg='black').pack()
diff_label = tk.Label(diff_frame, text="0.0", font=diff_font, fg='yellow', bg='black')
diff_label.pack()


def update_gui():
    target_label.config(text=f"{alts['target']:.3f}")
    chaser_label.config(text=f"{alts['chaser']:.3f}")
    diff = alts['target'] - alts['chaser']
    diff_label.config(text=f"{diff:.3f}")
    root.after(100, update_gui)


# Start target receiver thread
target_thread = threading.Thread(target=target_receiver_thread)
target_thread.daemon = True
target_thread.start()

# Start GUI update loop
root.after(100, update_gui)
root.mainloop()