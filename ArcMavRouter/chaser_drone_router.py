#!/usr/bin/env python3
import sys
sys.path.append('../')
sys.path.append('../venv/Lib/site-packages/')
from pymavlink import mavutil
import serial
import time
# ros related imports
import rospy
from anti_iha.msg import PosVel
from std_msgs.msg import Float32

def terrain_alt_callback(msg):
    global terrain_alt
    terrain_alt = msg.data
    
if __name__ == '__main__':
    # radio = serial.Serial("/dev/ttyUSB1",115200)
    radio = serial.Serial("/dev/ttyUSB0",115200)
    terrain_alt = 0.0
    connect = mavutil.mavlink_connection("udp:127.0.0.1:5500")
    print("Connected to target drone stream!")
    rospy.init_node('target_info', anonymous=True)
    time.sleep(1)
    target_pos_pub = rospy.Publisher('target_position', PosVel, queue_size=1)
    terrain_alt_sub = rospy.Subscriber('terrain_altitude', Float32, terrain_alt_callback, queue_size=1)
    
    while not rospy.is_shutdown():

        data = radio.read()
        # print(data)
        parse_data = connect.mav.parse_buffer(data)
        if parse_data != None:
            if parse_data[0].get_type() =="GLOBAL_POSITION_INT":
                target_pos_msg = PosVel()
                target_pos_msg.header.frame_id = "target_position"
                target_pos_msg.header.stamp = rospy.Time.now()
                target_pos_msg.latitude = float(parse_data[0].lat) / 1.0e7
                target_pos_msg.longitude = float(parse_data[0].lon) / 1.0e7
                target_pos_msg.altitude = float(parse_data[0].relative_alt) / 1000.0 + terrain_alt
                target_pos_msg.v_north = float(parse_data[0].vx) / 100.0
                target_pos_msg.v_east = float(parse_data[0].vy) / 100.0
                target_pos_msg.v_down = float(parse_data[0].vz) / 100.0
                target_pos_pub.publish(target_pos_msg)
