#!/usr/bin/env python3
"""
Obstacle Avoidance Robot using LiDAR C1
Compatible with Raspberry Pi OS on Raspberry Pi 5
Communicates with Arduino via Serial for motor/servo control
"""

import serial
import time
import math
import threading
from collections import deque

try:
    from rplidar import RPLidar
except ImportError:
    print("Error: Install rplidar-python with: pip3 install rplidar-python")
    exit(1)

#!/usr/bin/env python3
"""
Obstacle Avoidance Robot using RPLIDAR C1
Compatible with Raspberry Pi OS on Raspberry Pi 5
Communicates with Arduino via Serial for motor/servo control

This version uses the official rplidar library for reliable operation.
"""

import serial
import time
import math
import threading
from collections import deque

try:
    from rplidar import RPLidar
except ImportError:
    print("❌ Error: rplidar library not installed")
    print("Install with: pip install rplidar")
    exit(1)

# Configuration
LIDAR_PORT = '/dev/ttyUSB0'      # Check with: ls /dev/ttyUSB*
ARDUINO_PORT = '/dev/ttyACM0'    # Check with: ls /dev/ttyACM*
ARDUINO_BAUDRATE = 9600
LIDAR_BAUDRATE = 115200          # RPLIDAR C1 default

# Robot parameters
SERVO_CENTER = 90
MOTOR_MIN = 0
MOTOR_MAX = 255
DEFAULT_SPEED = 150

# Obstacle detection thresholds (in cm)
FRONT_THRESHOLD = 50
SIDE_THRESHOLD = 40
ANGLE_RANGE = 30

class LiDARObstacleAvoidance:
    def __init__(self):
        self.lidar = None
        self.arduino = None
        self.running = True
        self.lock = threading.Lock()
        self.scan_data = {}
        self.current_servo_angle = SERVO_CENTER
        self.current_motor_speed = 0

        # Statistics
        self.scan_count = 0
        self.last_scan_time = time.time()

        self.init_lidar()
        self.init_arduino()

    def init_lidar(self):
        """Initialize RPLIDAR C1 connection"""
        try:
            print(f"🔍 Connecting to RPLIDAR C1 on {LIDAR_PORT}...")
            self.lidar = RPLidar(LIDAR_PORT, baudrate=LIDAR_BAUDRATE)

            # Test connection
            info = self.lidar.get_device_info()
            health = self.lidar.get_device_health()

            print("✅ RPLIDAR C1 connected successfully!"            print(f"   Model: {info.model}")
            print(f"   Firmware: {info.firmware_version}")
            print(f"   Hardware: {info.hardware_version}")
            print(f"   Health: {health.status}")

        except Exception as e:
            print(f"❌ Failed to connect to RPLIDAR: {e}")
            print("\n🔧 Troubleshooting:")
            print("1. Check USB connection: ls /dev/ttyUSB*")
            print("2. Verify power supply (needs stable 5V)")
            print("3. Try different USB port")
            print("4. Check permissions: sudo usermod -a -G dialout $USER")
            exit(1)

    def init_arduino(self):
        """Initialize Arduino serial connection"""
        try:
            print(f"🔌 Connecting to Arduino on {ARDUINO_PORT}...")
            self.arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset

            # Test connection by sending center position
            self.send_command_to_arduino(SERVO_CENTER, 0)
            time.sleep(0.5)

            print("✅ Arduino connected successfully!")

        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            print("\n🔧 Troubleshooting:")
            print("1. Check USB connection: ls /dev/ttyACM*")
            print("2. Verify Arduino is powered and programmed")
            print("3. Try different USB port")
            exit(1)

    def send_command_to_arduino(self, servo_angle, motor_speed):
        """Send steering and motor commands to Arduino"""
        try:
            servo_angle = max(0, min(180, int(servo_angle)))
            motor_speed = max(MOTOR_MIN, min(MOTOR_MAX, int(motor_speed)))

            command = f"S{servo_angle},M{motor_speed}\n"

            with self.lock:
                self.arduino.write(command.encode())
                self.current_servo_angle = servo_angle
                self.current_motor_speed = motor_speed

            print(f"📤 Sent: Servo={servo_angle}° Motor={motor_speed}")

        except Exception as e:
            print(f"❌ Failed to send command: {e}")

    def detect_obstacles(self):
        """Analyze scan data for obstacles in different directions"""
        if not self.scan_data:
            return None

        front_distances = []
        left_distances = []
        right_distances = []

        for angle, distance_cm in self.scan_data.items():
            # Front sector (±30° from forward)
            if (360 - ANGLE_RANGE) <= angle <= 360 or 0 <= angle <= ANGLE_RANGE:
                front_distances.append(distance_cm)
            # Left sector (70°-110°)
            elif 70 <= angle <= 110:
                left_distances.append(distance_cm)
            # Right sector (250°-290°)
            elif 250 <= angle <= 290:
                right_distances.append(distance_cm)

        # Get minimum distances in each sector
        front_min = min(front_distances) if front_distances else float('inf')
        left_min = min(left_distances) if left_distances else float('inf')
        right_min = min(right_distances) if right_distances else float('inf')

        return {'front': front_min, 'left': left_min, 'right': right_min}

    def calculate_navigation(self, obstacles):
        """Calculate steering and speed based on obstacle distances"""
        if not obstacles:
            return SERVO_CENTER, DEFAULT_SPEED

        front = obstacles['front']
        left = obstacles['left']
        right = obstacles['right']

        # Obstacle avoidance logic
        if front < FRONT_THRESHOLD:
            # Obstacle ahead - turn away from closer side obstacle
            if left > right:
                servo_angle = SERVO_CENTER + 45  # Turn left
                motor_speed = int(DEFAULT_SPEED * 0.7)  # Slow down
                direction = "LEFT"
            else:
                servo_angle = SERVO_CENTER - 45  # Turn right
                motor_speed = int(DEFAULT_SPEED * 0.7)  # Slow down
                direction = "RIGHT"
        elif left < SIDE_THRESHOLD:
            # Obstacle on left - turn right
            servo_angle = SERVO_CENTER - 30
            motor_speed = DEFAULT_SPEED
            direction = "RIGHT (avoid left obstacle)"
        elif right < SIDE_THRESHOLD:
            # Obstacle on right - turn left
            servo_angle = SERVO_CENTER + 30
            motor_speed = DEFAULT_SPEED
            direction = "LEFT (avoid right obstacle)"
        else:
            # Clear path - go straight
            servo_angle = SERVO_CENTER
            motor_speed = DEFAULT_SPEED
            direction = "STRAIGHT"

        return servo_angle, motor_speed, direction

    def lidar_thread(self):
        """Main LIDAR scanning thread"""
        try:
            print("🔄 Starting LIDAR scanning...")
            for scan in self.lidar.iter_scans():
                if not self.running:
                    break

                # Process scan data
                self.scan_data.clear()
                for quality, angle, distance in scan:
                    # Convert mm to cm and filter low quality readings
                    if quality > 0:
                        distance_cm = distance / 10.0
                        if distance_cm > 0:
                            self.scan_data[int(angle)] = distance_cm

                # Update scan statistics
                self.scan_count += 1
                current_time = time.time()
                scan_rate = 1.0 / (current_time - self.last_scan_time) if self.scan_count > 1 else 0
                self.last_scan_time = current_time

                # Detect obstacles and navigate
                obstacles = self.detect_obstacles()
                if obstacles:
                    servo_angle, motor_speed, direction = self.calculate_navigation(obstacles)
                    self.send_command_to_arduino(servo_angle, motor_speed)

                    # Display status
                    print("25"
                          f"Direction: {direction}")

        except Exception as e:
            print(f"❌ LIDAR error: {e}")
        finally:
            self.stop()

    def start(self):
        """Start the robot"""
        print("🚀 Starting Obstacle Avoidance Robot...")
        print("=" * 50)

        self.running = True

        # Start LIDAR scanning thread
        lidar_thread = threading.Thread(target=self.lidar_thread, daemon=True)
        lidar_thread.start()

        try:
            print("🤖 Robot active! Press Ctrl+C to stop")
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping robot...")
            self.stop()

    def stop(self):
        """Stop the robot and cleanup"""
        self.running = False

        # Stop motors
        self.send_command_to_arduino(SERVO_CENTER, 0)
        time.sleep(0.5)

        # Disconnect devices
        if self.lidar:
            print("🔌 Disconnecting LIDAR...")
            self.lidar.stop()
            self.lidar.disconnect()

        if self.arduino:
            self.arduino.close()

        print("✅ Robot stopped and cleaned up")

if __name__ == '__main__':
    robot = LiDARObstacleAvoidance()
    robot.start()
        try:
            print(f"Connecting to LiDAR on {LIDAR_PORT}...")
            self.lidar = RPLidar(port=LIDAR_PORT, baudrate=LIDAR_BAUDRATE)
            self.lidar.connect()
            print(f"LiDAR connected. Info: {self.lidar.get_device_info()}")
            time.sleep(1)
        except Exception as e:
            print(f"Failed to connect to LiDAR: {e}")
            exit(1)
    
    def init_arduino(self):
        try:
            print(f"Connecting to Arduino on {ARDUINO_PORT}...")
            self.arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
            time.sleep(2)
            print("Arduino connected successfully")
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            exit(1)
    
    def send_command_to_arduino(self, servo_angle, motor_speed):
        try:
            servo_angle = max(0, min(180, int(servo_angle)))
            motor_speed = max(MOTOR_MIN, min(MOTOR_MAX, int(motor_speed)))
            
            command = f"S{servo_angle},M{motor_speed}\n"
            
            with self.lock:
                self.arduino.write(command.encode())
                self.current_servo_angle = servo_angle
                self.current_motor_speed = motor_speed
            
            print(f"Sent: Servo={servo_angle}° Motor={motor_speed}")
        except Exception as e:
            print(f"Failed to send command: {e}")
    
    def detect_obstacles(self):
        if not self.scan_data:
            return None
        
        front_distances = []
        left_distances = []
        right_distances = []
        
        for angle, distance in self.scan_data.items():
            if (360 - ANGLE_RANGE) <= angle <= 360 or 0 <= angle <= ANGLE_RANGE:
                front_distances.append(distance)
            elif 70 <= angle <= 110:
                left_distances.append(distance)
            elif 250 <= angle <= 290:
                right_distances.append(distance)
        
        front_min = min(front_distances) if front_distances else float('inf')
        left_min = min(left_distances) if left_distances else float('inf')
        right_min = min(right_distances) if right_distances else float('inf')
        
        return {'front': front_min, 'left': left_min, 'right': right_min}
    
    def calculate_navigation(self, obstacles):
        if not obstacles:
            return SERVO_CENTER, DEFAULT_SPEED
        
        front = obstacles['front']
        left = obstacles['left']
        right = obstacles['right']
        
        if front < FRONT_THRESHOLD:
            if left > right:
                servo_angle = SERVO_CENTER + 45
                motor_speed = int(DEFAULT_SPEED * 0.7)
            else:
                servo_angle = SERVO_CENTER - 45
                motor_speed = int(DEFAULT_SPEED * 0.7)
        elif left < SIDE_THRESHOLD:
            servo_angle = SERVO_CENTER - 30
            motor_speed = DEFAULT_SPEED
        elif right < SIDE_THRESHOLD:
            servo_angle = SERVO_CENTER + 30
            motor_speed = DEFAULT_SPEED
        else:
            servo_angle = SERVO_CENTER
            motor_speed = DEFAULT_SPEED
        
        return servo_angle, motor_speed
    
    def lidar_thread(self):
        try:
            for scan in self.lidar.iter_scans():
                if not self.running:
                    break
                
                self.scan_data.clear()
                for quality, angle, distance in scan:
                    distance_cm = distance / 10
                    if distance_cm > 0:
                        self.scan_data[round(angle)] = distance_cm
                
                obstacles = self.detect_obstacles()
                if obstacles:
                    servo_angle, motor_speed = self.calculate_navigation(obstacles)
                    self.send_command_to_arduino(servo_angle, motor_speed)
                    print(f"Front: {obstacles['front']:.1f}cm Left: {obstacles['left']:.1f}cm Right: {obstacles['right']:.1f}cm")
        
        except Exception as e:
            print(f"LiDAR error: {e}")
        finally:
            self.stop()
    
    def start(self):
        print("Starting robot...")
        self.running = True
        
        lidar_thread = threading.Thread(target=self.lidar_thread, daemon=True)
        lidar_thread.start()
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping robot...")
            self.stop()
    
    def stop(self):
        self.running = False
        self.send_command_to_arduino(SERVO_CENTER, 0)
        time.sleep(0.5)
        
        if self.lidar:
            self.lidar.stop()
            self.lidar.disconnect()
        
        if self.arduino:
            self.arduino.close()
        
        print("Robot stopped")

if __name__ == '__main__':
    robot = LiDARObstacleAvoidance()
    robot.start()
