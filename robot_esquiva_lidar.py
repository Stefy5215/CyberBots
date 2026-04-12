#!/usr/bin/env python3
"""
Robot Esquiva Obstáculos con LiDAR C1
Raspberry Pi 5 + Elegoo Smart Car + LiDAR C1
Compatible con Raspberry Pi OS
"""

import serial
import time
import threading
import struct

class SimpleRPLidar:
    """Driver básico para RPLIDAR usando el protocolo serial.

    Este driver lee paquetes de escaneo y devuelve (quality, angle, distance_mm).
    Funciona con RPLIDAR C1 en 460800 baud.
    """

    def __init__(self, port, baudrate=460800):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.running = False

    def connect(self):
        self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
        time.sleep(2)

    def start_scan(self):
        self.serial.write(b"\xA5\x20")  # Comando Start Scan
        self.running = True

    def stop_scan(self):
        self.running = False
        self.serial.write(b"\xA5\x25")  # Comando Stop

    def iter_scans(self):
        buffer = bytearray()

        while self.running:
            if self.serial.in_waiting > 0:
                data = self.serial.read(self.serial.in_waiting)
                buffer.extend(data)

                while len(buffer) >= 5:
                    if buffer[0] == 0xA5 and buffer[1] == 0x5A:
                        packet_len = struct.unpack("<H", buffer[3:5])[0]
                        if len(buffer) >= 5 + packet_len:
                            packet = buffer[5:5 + packet_len]
                            buffer = buffer[5 + packet_len :]

                            scan_data = []
                            for i in range(0, len(packet), 5):
                                if i + 4 < len(packet):
                                    quality = packet[i] >> 2
                                    angle = ((packet[i + 1] | (packet[i] & 0x03) << 8)) / 64.0
                                    distance_mm = packet[i + 2] | (packet[i + 3] << 8)
                                    scan_data.append((quality, angle, distance_mm))
                            if scan_data:
                                yield scan_data
                        else:
                            break
                    else:
                        buffer.pop(0)
            else:
                time.sleep(0.005)

    def disconnect(self):
        if self.serial:
            self.serial.close()

# Configuración de puertos
LIDAR_PORT = '/dev/ttyUSB1'
ARDUINO_PORT = '/dev/ttyUSB0'
ARDUINO_BAUDRATE = 9600
LIDAR_BAUDRATE = 460800  # Baudrate correcto encontrado

# Parámetros del robot
SERVO_CENTER = 90
MOTOR_STOP = 0
MOTOR_MIN = 100   # Aumentado para que avance más
MOTOR_NORMAL = 150 # Velocidad normal más alta
MOTOR_FAST = 200   # Velocidad máxima  # Velocidad máxima ajustada a 200
# Safe start mode: caps motor speed to SAFE_MAX_SPEED while True
SAFE_START_MODE = False  # Desactivado para usar velocidades normales
SAFE_MAX_SPEED = 200

# Umbrales de distancia (cm) - aumentados para reacción más temprana
FRONT_THRESHOLD = 80  # Antes 50
SIDE_THRESHOLD = 60   # Antes 35
ANGLE_RANGE = 30

class LiDARRobotController:
    def __init__(self):
        self.lidar = None
        self.arduino = None
        self.running = True
        self.lock = threading.Lock()
        
        self.scan_data = {}
        self.current_servo = SERVO_CENTER
        self.current_motor = 0
        
        self.init_lidar()
        self.init_arduino()
    
    def init_lidar(self):
        try:
            print(f"Conectando LiDAR en {LIDAR_PORT}...")
            self.lidar = SimpleRPLidar(LIDAR_PORT, LIDAR_BAUDRATE)
            self.lidar.connect()
            self.lidar.start_scan()
            print(f"✓ LiDAR conectado")
        except Exception as e:
            print(f"✗ Error LiDAR: {e}")
            exit(1)
    
    def init_arduino(self):
        try:
            print(f"Conectando Elegoo en {ARDUINO_PORT}...")
            self.arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
            time.sleep(2)
            print("✓ Elegoo conectado")
        except Exception as e:
            print(f"✗ Error Elegoo: {e}")
            exit(1)
    
    def send_command(self, servo_angle, motor_speed):
        try:
            servo_angle = max(0, min(180, int(servo_angle)))
            motor_speed = max(0, min(255, int(motor_speed)))
            if SAFE_START_MODE:
                motor_speed = min(motor_speed, SAFE_MAX_SPEED)
            
            command = f"S{servo_angle},M{motor_speed}\n"

            with self.lock:
                self.arduino.write(command.encode())
                # try to read ACK line from Arduino
                try:
                    resp = self.arduino.readline().decode(errors='ignore').strip()
                    if resp:
                        print(f"← {resp}")
                except Exception:
                    pass

                self.current_servo = servo_angle
                self.current_motor = motor_speed

            print(f"→ Servo={servo_angle}° Motor={motor_speed}")
        except Exception as e:
            print(f"Error envío: {e}")
    
    def analyze_scan(self):
        if not self.scan_data:
            return None
        
        front = []
        left = []
        right = []
        
        for angle, distance in self.scan_data.items():
            # Filtrar distancias muy cortas (< 5cm) que pueden ser ruido
            if distance < 5:
                continue
                
            if (350 <= angle <= 360 or 0 <= angle <= 10):  # Frente amplio
                front.append(distance)
            elif 60 <= angle <= 120:  # Izquierda
                left.append(distance)
            elif 240 <= angle <= 300:  # Derecha
                right.append(distance)
        
        return {
            'front': min(front) if front else 999,
            'left': min(left) if left else 999,
            'right': min(right) if right else 999,
        }
    
    def make_decision(self, obstacles):
        if not obstacles:
            return SERVO_CENTER, MOTOR_FAST  # Camino libre - máxima velocidad
        
        front = obstacles['front']
        left = obstacles['left']
        right = obstacles['right']
        
        # Lógica mejorada: más autónomo
        if front < FRONT_THRESHOLD:
            # Obstáculo adelante - reducir velocidad en lugar de girar
            return SERVO_CENTER, MOTOR_NORMAL  # Reducir velocidad cuando detecte algo cerca
        elif left < SIDE_THRESHOLD:
            return 45, MOTOR_NORMAL  # Gira izquierda moderado
        elif right < SIDE_THRESHOLD:
            return 135, MOTOR_NORMAL  # Gira derecha moderado
        else:
            return SERVO_CENTER, MOTOR_FAST  # Camino libre - máxima velocidad
    
    def lidar_loop(self):
        try:
            for scan in self.lidar.iter_scans():
                if not self.running:
                    break
                
                self.scan_data.clear()
                for quality, angle, distance in scan:
                    distance_cm = distance / 10
                    if distance_cm > 0:
                        self.scan_data[round(angle)] = distance_cm
                
                obstacles = self.analyze_scan()
                if obstacles:
                    servo, motor = self.make_decision(obstacles)
                    self.send_command(servo, motor)
                    print(f"  Adelante: {obstacles['front']:.1f}cm Izq: {obstacles['left']:.1f}cm Der: {obstacles['right']:.1f}cm")
        except Exception as e:
            print(f"Error LiDAR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
    
    def start(self):
        print("\n🤖 Iniciando robot esquivador...")
        self.running = True
        
        lidar_thread = threading.Thread(target=self.lidar_loop, daemon=True)
        lidar_thread.start()
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⏹ Deteniendo...")
            self.stop()
    
    def stop(self):
        self.running = False
        self.send_command(SERVO_CENTER, MOTOR_STOP)
        time.sleep(0.5)
        
        if self.lidar:
            try:
                self.lidar.stop_scan()
            except Exception:
                pass
            try:
                self.lidar.disconnect()
            except Exception:
                pass
        
        if self.arduino:
            self.arduino.close()
        
        print("✓ Robot detenido")

if __name__ == '__main__':
    robot = LiDARRobotController()
    robot.start()
