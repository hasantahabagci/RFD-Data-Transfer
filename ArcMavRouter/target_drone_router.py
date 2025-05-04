"""
    ITU-ARC SRUS PROJESI
        Onur SEVIMLI
            25.12.2020
                        """

# Import libraries
import sys
sys.path.append('../')
# sys.path.append('/home/pi/Desktop/anti-iha_haberlesme')
# sys.path.append('/home/pi/Desktop/anti-iha_haberlesme/venv/Lib/site-packages/')
from ArcMavRouter.ARCHub.ARCHub import HubMain
import time

# Global parameters
baud = 115200

# Create the main hub object
hub = HubMain()

""" 
While adding elements to the Hub, note that
there are three different element types can be added to the hub:
- autopilot: real or SIL autopilot connection
- serial: serial connection (for radio links etc.)
- socket: socket connection (for mission script or additional GCS etc.)
 """

# SITL UAV adresses
radio_address = '/dev/ttyUSB0'
uav1_address = '/dev/ttyACM0'
script_address = '127.0.0.1:6000'

uav1 = hub.addElement(name="uav1",
                      type="autopilot",
                      address=uav1_address,
                      baudrate=115200)
script = hub.addElement(name="script",
                      type="socket",
                      address=script_address,
                      baudrate=115200)
radio = hub.addElement(name="radio",
                       type="serial",
                       address=radio_address,
                       baudrate=115200
                       )

pipe1 = hub.addPipe(name="uav1_to_radio_script",
                    input=uav1,
                    outputs=[radio,script],
                    msg_filter=["BAD_DATA","HEARTBEAT","AHRS3","STATUSTEXT","SCALED_PRESSURE2","SYSTEM_TIME","TIMESYNC","EKF_STATUS_REPORT","GPS_GLOBAL_ORIGIN","HWSTATUS","AHRS","AHRS2","RAW_IMU","SCALED_IMU2","SCALED_IMU3","POWER_STATUS","MEMINFO","NAV_CONTROLLER_OUTPUT","MISSION_CURRENT","SERVO_OUTPUT_RAW","RC_CHANNELS","RC_CHANNELS_RAW","SCALED_PRESSURE","SIMSTATE","TERRAIN_REPORT","TERRAIN_REQUEST"],
                    targets_to_be_filtered=[radio])
pipe2 = hub.addPipe(name="script_to_uav1",
                    input=script,
                    outputs=[uav1],
                    msg_filter=[],
                    targets_to_be_filtered=[])
pipe3 = hub.addPipe(name="radio_to_uav1",
                    input=radio,
                    outputs=[uav1],
                    msg_filter=[],
                    targets_to_be_filtered=[])

# Initialize the hub object
hub.initialize_pipes()

# Infinite dummy loop
while True:
    # print('---- ARCHub is alive ----')
    time.sleep(1)