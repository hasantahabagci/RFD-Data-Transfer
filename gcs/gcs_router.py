import serial

target_radio = serial.Serial("/dev/ttyUSB0",115200)
chaser_radio = serial.Serial("/dev/ttyUSB1",115200)
print("Connected to target drone stream!")
while True:
    data = target_radio.read()
    # print(data)
    chaser_radio.write(data)
