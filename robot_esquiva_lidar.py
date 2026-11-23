#!/usr/bin/env python3
"""Robot esquiva obstáculos con LiDAR C1."""

import serial
import time
import struct
import threading

LIDAR_PORT = '/dev/ttyUSB1'
ARDUINO_PORT = '/dev/ttyUSB0'
ARDUINO_BAUDRATE = 9600
LIDAR_BAUDRATE = 460800

SERVO_CENTRO = 90
MOTOR_PARADO = 0
MOTOR_NORMAL = 200 # Pista 3.21m, más velocidad
MOTOR_RAPIDO = 220
MODO_SEGURIDAD = False
MAX_VEL_SEGURA = 200

UMBRAL_FRENTE = 150  # Pista 3.21m, detecta obstáculos más lejos
UMBRAL_LATERAL = 120   # Detección lateral para pista grande

class ControlRobotLidar:
    def __init__(self):
        self.lidar = None
        self.arduino = None
        self.running = True
        self.lock = threading.Lock()
        self.scan_data = {}
        self.servo_actual = SERVO_CENTRO
        self.motor_actual = 0
        self.vueltas_completadas = 0
        self.ciclos_servo = 0
        self.ultimo_servo = SERVO_CENTRO
        self.tiempo_inicio_vuelta = time.time()
        self.tiempo_estimado_vuelta = 50  # segundos estimados por vuelta en pista 3.21m
        self.init_lidar()
        self.init_arduino()

    def init_lidar(self):
        try:
            print(f"Conectando LiDAR en {LIDAR_PORT}...")
            self.lidar = serial.Serial(LIDAR_PORT, LIDAR_BAUDRATE, timeout=1)
            time.sleep(2)
            self.lidar.write(b"\xA5\x20")
            print("✓ LiDAR conectado")
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

    def send_command(self, servo_angulo, motor_velocidad):
        try:
            servo_angulo = max(0, min(180, int(servo_angulo)))
            motor_velocidad = max(0, min(255, int(motor_velocidad)))
            if MODO_SEGURIDAD:
                motor_velocidad = min(motor_velocidad, MAX_VEL_SEGURA)
            
            if self.vueltas_completadas >= 3:
                servo_angulo = SERVO_CENTRO
                motor_velocidad = MOTOR_PARADO
            
            comando = f"S{servo_angulo},M{motor_velocidad}\n"
            with self.lock:
                self.arduino.write(comando.encode())
                try:
                    respuesta = self.arduino.readline().decode(errors='ignore').strip()
                    if respuesta:
                        print(f"← {respuesta}")
                except Exception:
                    pass
                self.servo_actual = servo_angulo
                self.motor_actual = motor_velocidad
                
                if servo_angulo != self.ultimo_servo:
                    if (self.ultimo_servo <= SERVO_CENTRO and servo_angulo > SERVO_CENTRO) or \
                       (self.ultimo_servo > SERVO_CENTRO and servo_angulo <= SERVO_CENTRO):
                        self.ciclos_servo += 1
                        if self.ciclos_servo >= 4:
                            self.vueltas_completadas += 1
                            self.ciclos_servo = 0
                            self.tiempo_inicio_vuelta = time.time()
                            print(f"\n✓ Vuelta {self.vueltas_completadas}/3 completada!")
                    self.ultimo_servo = servo_angulo
            
            tiempo_vuelta = time.time() - self.tiempo_inicio_vuelta
            print(f"→ Servo={servo_angulo}° Motor={motor_velocidad} | Vuelta: {self.vueltas_completadas}/3 ({tiempo_vuelta:.1f}s)")
        except Exception as e:
            print(f"Error envío: {e}")

    def analizar_escaneo(self):
        if not self.scan_data:
            return None
        frente, izquierda, derecha = [], [], []
        for angulo, distancia in self.scan_data.items():
            if distancia < 5:
                continue
            if (350 <= angulo <= 360) or (0 <= angulo <= 10):
                frente.append(distancia)
            elif 60 <= angulo <= 120:
                izquierda.append(distancia)
            elif 240 <= angulo <= 300:
                derecha.append(distancia)
        return {
            'frente': min(frente) if frente else 999,
            'izquierda': min(izquierda) if izquierda else 999,
            'derecha': min(derecha) if derecha else 999,
        }

    def decidir_movimiento(self, obstaculos):
        if not obstaculos:
            return SERVO_CENTRO, MOTOR_RAPIDO
        frente = obstaculos['frente']
        izquierda = obstaculos['izquierda']
        derecha = obstaculos['derecha']
        if frente < UMBRAL_FRENTE:
            return SERVO_CENTRO, MOTOR_NORMAL
        if izquierda < UMBRAL_LATERAL:
            return 45, MOTOR_NORMAL
        if derecha < UMBRAL_LATERAL:
            return 135, MOTOR_NORMAL
        return SERVO_CENTRO, MOTOR_RAPIDO

    def bucle_lidar(self):
        buffer = bytearray()
        try:
            while self.running:
                if self.vueltas_completadas >= 3:
                    self.send_command(SERVO_CENTRO, MOTOR_PARADO)
                    time.sleep(1)
                    self.running = False
                    break
                
                if self.lidar.in_waiting > 0:
                    data = self.lidar.read(self.lidar.in_waiting)
                    buffer.extend(data)
                    while len(buffer) >= 5:
                        if buffer[0] != 0xA5 or buffer[1] != 0x5A:
                            buffer.pop(0)
                            continue
                        packet_len = struct.unpack('<H', buffer[3:5])[0]
                        if len(buffer) < 5 + packet_len:
                            break
                        packet = buffer[5:5 + packet_len]
                        buffer = buffer[5 + packet_len:]
                        self.scan_data.clear()
                        for i in range(0, len(packet), 5):
                            if i + 4 < len(packet):
                                angulo = ((packet[i+1] | ((packet[i] & 0x03) << 8))) / 64.0
                                distancia_cm = (packet[i+2] | (packet[i+3] << 8)) / 10.0
                                if distancia_cm > 0:
                                    self.scan_data[round(angulo)] = distancia_cm
                        obstaculos = self.analizar_escaneo()
                        if obstaculos:
                            servo, motor = self.decidir_movimiento(obstaculos)
                            self.send_command(servo, motor)
                            print(f"  Frente: {obstaculos['frente']:.1f}cm Izq: {obstaculos['izquierda']:.1f}cm Der: {obstaculos['derecha']:.1f}cm")
                else:
                    time.sleep(0.003)
        except Exception as e:
            print(f"Error LiDAR: {e}")
        finally:
            self.detener()

    def iniciar(self):
        print("\n🤖 Iniciando robot esquivador...")
        self.running = True
        hilo = threading.Thread(target=self.bucle_lidar, daemon=True)
        hilo.start()
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⏹ Deteniendo...")
            self.detener()

    def detener(self):
        self.running = False
        try:
            self.send_command(SERVO_CENTRO, MOTOR_PARADO)
            time.sleep(0.5)
            self.lidar.write(b"\xA5\x25")
            self.lidar.close()
            self.arduino.close()
        except Exception:
            pass
        print("✓ Robot detenido")

if __name__ == '__main__':
    robot = ControlRobotLidar()
    robot.iniciar()
