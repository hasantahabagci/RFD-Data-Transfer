import serial
import json

# Configure the serial port (update the port and baud rate as needed)
ser = serial.Serial(
    port='/dev/tty.usbserial-A10LF01N',  # Update this to your serial port
    baudrate=57600,       # Default baudrate for RFD900x
    timeout=1
)


try:
    while True:
        if ser.in_waiting > 0:
            try:
                # Read a line of data from the serial port
                data = ser.readline().decode('utf-8').strip()
                try:
                    # Parse JSON data
                    parsed_data = json.loads(data)
                    print("Received data:", parsed_data)
                except json.JSONDecodeError:
                    print("Failed to decode JSON:", data)
            except UnicodeDecodeError as e:
                print("UnicodeDecodeError:", e)
except KeyboardInterrupt:
    print("Reception stopped.")
finally:
    ser.close()  # Close the serial port