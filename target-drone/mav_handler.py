from dronekit import connect, VehicleMode, LocationGlobalRelative
from pymavlink import mavutil
from pymavlink.quaternion import QuaternionBase
import time
import math

from mavlinkHandler import MAVLinkHandlerDronekit, MAVLinkHandlerPymavlink



def to_quaternion(roll = 0.0, pitch = 0.0, yaw = 0.0):
    """
    Convert degrees to quaternions
    """
    t0 = math.cos(math.radians(yaw * 0.5))
    t1 = math.sin(math.radians(yaw * 0.5))
    t2 = math.cos(math.radians(roll * 0.5))
    t3 = math.sin(math.radians(roll * 0.5))
    t4 = math.cos(math.radians(pitch * 0.5))
    t5 = math.sin(math.radians(pitch * 0.5))

    w = t0 * t2 * t4 + t1 * t3 * t5
    x = t0 * t3 * t4 - t1 * t2 * t5
    y = t0 * t2 * t5 + t1 * t3 * t4
    z = t1 * t2 * t4 - t0 * t3 * t5

    return [w, x, y, z]





class MAVHandler:
    """
    MAVHandler is a helper class that uses DroneKit to manage MAVLink-based drones.
    It provides methods for connecting, arming, takeoff, navigation, and retrieving telemetry data.
    """

    def __init__(self, connection_string, baud_rate=57600):
        """
        Initialize the MAVHandler by connecting to the vehicle.

        :param connection_string: The address string for connecting to the vehicle
                                  (e.g., '/dev/ttyAMA0', 'udp:127.0.0.1:14550', etc.)
        :param baud_rate: Baud rate for serial connection (ignored for UDP/TCP connections).
        """
        print(f"Connecting to vehicle on: {connection_string}")
        self.vehicle = connect(connection_string, baud=baud_rate, wait_ready=True, rate=100)
        print("Connection established.")

        self.imu_data = {'xacc': 0, 'yacc': 0, 'zacc': 0}
        self.angular_velocity = {'xgyro': 0, 'ygyro': 0, 'zgyro': 0}
        self.boot_time = time.time()

        # Tell DroneKit to call our method on RAW_IMU messages
        self.vehicle.add_message_listener('RAW_IMU', self.receivedImu)

    def receivedImu(self, vehicle, name, msg):
        # Now `self` is the MAVHandler instance, and
        # `vehicle` is the dronekit.Vehicle object
        self.imu_data['xacc'] = msg.xacc
        self.imu_data['yacc'] = msg.yacc
        self.imu_data['zacc'] = msg.zacc
        self.angular_velocity['xgyro'] = msg.xgyro
        self.angular_velocity['ygyro'] = msg.ygyro
        self.angular_velocity['zgyro'] = msg.zgyro

    def set_parameter_value(self, parameter_name, value):
        self.vehicle.parameters[parameter_name] = value
        
    def get_parameter_value(self, parameter_name):
        """
        Get the value of a parameter from the vehicle.

        :param parameter_name: The name of the parameter to retrieve.
        :return: The value of the parameter.
        """
        return self.vehicle.parameters.get(parameter_name)

    def arm_and_takeoff(self, target_altitude):
        """
        Arms the drone and takes off to a specified altitude in meters.

        :param target_altitude: Target altitude (in meters) above ground.
        """
        print("Arming motors...")
        while not self.vehicle.is_armable:
            print("Waiting for vehicle to become armable...")
            time.sleep(1)

        # Set the vehicle mode to GUIDED (required for taking off)
        self.vehicle.mode = VehicleMode("GUIDED")
        while self.vehicle.mode != "GUIDED":
            print("Waiting for mode to change to GUIDED...")
            time.sleep(1)

        self.vehicle.armed = True
        while not self.vehicle.armed:
            print("Waiting for vehicle to become armed...")
            time.sleep(1)

        print("Taking off!")
        self.vehicle.simple_takeoff(target_altitude)

        # Wait until the vehicle reaches a safe height
        while True:
            current_altitude = self.vehicle.location.global_relative_frame.alt
            print(f"Current Altitude: {current_altitude:.2f} m")
            if current_altitude >= target_altitude * 0.95:
                print("Reached target altitude")
                break
            time.sleep(1)

    def goto_location(self, lat, lon, alt):
        """
        Commands the vehicle to move to a specified location (latitude, longitude, altitude).
        Uses simple_goto for demonstration.

        :param lat: Latitude in decimal degrees.
        :param lon: Longitude in decimal degrees.
        :param alt: Altitude in meters above ground.
        """
        print(f"Going to Location: lat={lat}, lon={lon}, alt={alt}")
        target_location = LocationGlobalRelative(lat, lon, alt)
        self.vehicle.simple_goto(target_location)

    def set_velocity_body(self, vx, vy, vz):
        """
        Set the vehicle velocity in the body frame (relative to heading).
        This shows an example of sending custom velocity commands using DroneKit.
        
        :param vx: Velocity in m/s along the vehicle's x-axis (forward is positive).
        :param vy: Velocity in m/s along the vehicle's y-axis (to the right is positive).
        :param vz: Velocity in m/s along the vehicle's z-axis (down is positive).
        """
        msg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,       # coordinate frame (1 = MAV_FRAME_LOCAL_NED)
            0b0000111111000111,  # type_mask (bitmask;  only velocity components enabled)
            0, 0, 0, # x, y, z positions (not used)
            vx, vy, vz,  # velocity components in m/s
            0, 0, 0, # accelerations (not used)
            0, 0     # yaw, yaw_rate (not used)
        )
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()

    def set_target_attitude(self, roll=0, pitch=0, yaw=0, thrust=0.5, roll_rate=0, pitch_rate=0, yaw_rate=0, bit_mask=0b00000000):
            msg = self.vehicle.message_factory.set_attitude_target_encode(
                int(1e3 * (time.time() - self.boot_time)),
                self.vehicle._master.target_system, self.vehicle._master.target_component,
                bit_mask,
                QuaternionBase([math.radians(angle) for angle in (roll, pitch, yaw)]),
                roll_rate, 
                pitch_rate, 
                yaw_rate, 
                thrust
            )
            self.vehicle.send_mavlink(msg)

    def set_position_target_local_ned(self, vx, vy=0, vz=0, yaw=None):
        """
        Set the vehicle's position target in local NED coordinates.

        :param vx: Velocity in m/s along the vehicle's x-axis (forward is positive).
        :param vy: Velocity in m/s along the vehicle's y-axis (to the right is positive).
        :param vz: Velocity in m/s along the vehicle's z-axis (down is positive).
        :param yaw: Yaw angle in radians. If None, the current vehicle yaw will be used.
        """
        if yaw is None:
            yaw = self.vehicle.attitude.yaw

        msg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,       # coordinate frame
            0b0000111111000111,  # type_mask (only velocity components enabled)
            0, 0, 0, # x, y, z positions (not used)
            vx, vy, vz,  # velocity components in m/s
            0, 0, 0, # accelerations (not used)
            math.degrees(yaw),  # yaw angle in degrees
            0     # yaw_rate (not used)
        )
        self.vehicle.send_mavlink(msg)


    def send_attitude_target_ignore_throttle(
        self,
        roll_angle=0.0,
        pitch_angle=0.0,
        yaw_angle=None,
        roll_rate=0.0,
        pitch_rate=0.0,
        yaw_rate=0.0,
        use_yaw_rate=True,
        thrust=0.0
    ):
        """
        This version of send_attitude_target ignores the throttle input by setting
        the corresponding bit (bit 3) in the type_mask. As a result, the 'thrust'
        field will not be used by the flight controller.

        Parameters
        ----------
        roll_angle : float
            Desired roll angle in radians.
        pitch_angle : float
            Desired pitch angle in radians.
        yaw_angle : float, optional
            Desired yaw angle in radians. If None, the current vehicle yaw will be used.
        roll_rate : float
            Desired roll rate in radians/second.
        pitch_rate : float
            Desired pitch rate in radians/second.
        yaw_rate : float
            Desired yaw rate in radians/second.
        use_yaw_rate : bool
            If True, yaw_rate is used and yaw_angle is ignored.
            If False, yaw_angle is used and yaw_rate is ignored.
        thrust : float
            Thrust value (0.0 to 1.0). This parameter will be ignored in this function
            because bit 3 of the type_mask is set to ignore throttle.
        """
        import math
        
        # If no yaw angle is provided, use the current vehicle yaw
        if yaw_angle is None:
            yaw_angle = self.vehicle.attitude.yaw

        # Determine the appropriate type_mask
        # bit 3 (0x08) is set to ignore throttle
        # bit 2 (0x04) is set to ignore yaw rate (i.e., use yaw angle) if use_yaw_rate=False
        if use_yaw_rate:
            # Use yaw rate => do not ignore yaw rate => bit 2 = 0, but bit 3 = 1
            typemask = 0b00001000  # 8 decimal
        else:
            # Use yaw angle => ignore yaw rate => bit 2 = 1, bit 3 = 1
            typemask = 0b00001100  # 12 decimal
        
        # Create the message
        msg = self.vehicle.message_factory.set_attitude_target_encode(
            0,    # time_boot_ms
            1,    # target system
            1,    # target component
            typemask,
            to_quaternion(roll_angle, pitch_angle, yaw_angle),  # attitude (quaternion)
            roll_rate,   # body roll rate in radians/sec
            pitch_rate,  # body pitch rate in radians/sec
            math.radians(yaw_rate),  # body yaw rate in radians/sec
            thrust       # thrust - ignored by FCU because bit 3 is set
        )

        self.vehicle.send_mavlink(msg)


    def condition_yaw(self, heading, relative=False, clockwise=True):
        """
        Yaw to a specific heading (in degrees). If relative=True, the heading is relative.
        """
        is_relative = 1 if relative else 0
        direction = 1 if clockwise else -1

        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_CMD_CONDITION_YAW, # command
            0,       # confirmation
            heading, # param 1: yaw angle or yaw rate if relative
            0,       # param 2: yaw speed (deg/s)
            direction,  # param 3: direction (1 = cw, -1 = ccw)
            is_relative, # param 4: 1 if relative
            0, 0, 0
        )
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
        

    def return_to_launch(self):
        """
        Commands the vehicle to return to its launch location (home).
        """
        print("Returning to Launch (RTL)...")
        self.vehicle.mode = VehicleMode("RTL")

    def get_location(self):
        """
        Retrieve the current global-relative location of the drone.

        :return: A LocationGlobalRelative object with the current location.
        """
        return self.vehicle.location.global_relative_frame.lat, self.vehicle.location.global_relative_frame.lon, self.vehicle.location.global_relative_frame.alt

    def get_attitude(self):
        """
        Retrieve the current attitude (roll, pitch, yaw) of the drone.

        :return: An Attitude object with roll, pitch, yaw in radians.
        """
        return self.vehicle.attitude.roll, self.vehicle.attitude.pitch, self.vehicle.attitude.yaw

    def get_heading(self):
        """
        Retrieve the current heading (yaw) of the vehicle in degrees.

        :return: Integer heading in degrees.
        """
        return self.vehicle.heading

    def set_mode(self, mode_name):
        """
        Set vehicle mode (e.g., 'GUIDED', 'LOITER', 'AUTO', etc.).

        :param mode_name: A valid flight mode string.
        """
        print(f"Changing mode to {mode_name}...")
        self.vehicle.mode = VehicleMode(mode_name)
        while self.vehicle.mode.name != mode_name:
            print("Waiting for mode to change...")
            time.sleep(1)
        print(f"Vehicle mode changed to {mode_name}.")

    def set_groundspeed(self, speed_m_s):
        """
        Set the default groundspeed for simple navigation commands.

        :param speed_m_s: Speed in meters per second.
        """
        print(f"Setting default groundspeed to {speed_m_s} m/s...")
        self.vehicle.groundspeed = speed_m_s

    def close_connection(self):
        """
        Closes the connection to the vehicle.
        """
        print("Closing vehicle connection...")
        self.vehicle.close()
        print("Connection closed.")

    def get_velocity(self):
        """
        Get the xyz velocity of aircraft.
        """
        return self.vehicle.velocity


# Example usage:
if __name__ == "__main__":
    # Replace with your connection details
    # connection_str = "127.0.0.1:14563"
    # handler = MAVHandler(connection_str)

    # while True:
    #     # Get the angular velocity of the drone
    #     handler.set_velocity_body(8, 0, 0)
    #     time.sleep(0.1)


    

    connection_str = "/dev/ttyACM0"
    handler = MAVHandler(connection_str)

    while True:
        print(handler.get_parameter_value("WP_YAW_BEHAVIOR"))
        handler.set_parameter_value("WP_YAW_BEHAVIOR", 0)



      