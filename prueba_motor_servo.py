#!/usr/bin/env python3
"""
Test simple para Motor + Servo
Sin LiDAR — solo pruebas manuales
"""

import serial
import time

ARDUINO_PORT = '/dev/ttyUSB0'
ARDUINO_BAUDRATE = 9600

def send_command(ser, servo_angle, motor_speed):
    """Enviar comando al Arduino"""
    command = f"S{servo_angle},M{motor_speed}\n"
    print(f"→ Enviando: {command.strip()}")
    ser.write(command.encode())
    time.sleep(0.2)
    
    try:
        response = ser.readline().decode(errors='ignore').strip()
        if response:
            print(f"← Respuesta: {response}\n")
        else:
            print("← (sin respuesta)\n")
    except Exception as e:
        print(f"Error lectura: {e}\n")

def main():
    try:
        print(f"Conectando Arduino en {ARDUINO_PORT}...")
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
        time.sleep(2)
        print("✓ Conectado\n")
        
        # Prueba 1: Servo al centro, motor parado
        print("=== PRUEBA 1: Servo centro + Motor parado ===")
        send_command(ser, 90, 0)
        time.sleep(1)
        
        # Prueba 2: Servo centro, motor lento adelante (velocidad 100)
        print("=== PRUEBA 2: Motor adelante (velocidad 100) ===")
        send_command(ser, 90, 100)
        time.sleep(2)
        
        # Prueba 2b: Velocidad mínima (20)
        print("=== PRUEBA 2b: Motor adelante (velocidad mínima 20) ===")
        send_command(ser, 90, 20)
        time.sleep(2)
        
        # Prueba 2c: Velocidad media (150)
        print("=== PRUEBA 2c: Motor adelante (velocidad 150) ===")
        send_command(ser, 90, 150)
        time.sleep(2)
        
        # Prueba 3: Motor parado
        print("=== PRUEBA 3: Motor parado ===")
        send_command(ser, 90, 0)
        time.sleep(1)
        
        # Prueba 4: Servo izquierda, motor parado
        print("=== PRUEBA 4: Servo izquierda (45°) ===")
        send_command(ser, 45, 0)
        time.sleep(1)
        
        # Prueba 5: Servo derecha
        print("=== PRUEBA 5: Servo derecha (135°) ===")
        send_command(ser, 135, 0)
        time.sleep(1)
        
        # Prueba 6: Servo centro + motor velocidad normal (150)
        print("=== PRUEBA 6: Servo centro + Motor velocidad 150 ===")
        send_command(ser, 90, 150)
        time.sleep(2)
        
        # Parar todo
        print("=== APAGANDO TODO ===")
        send_command(ser, 90, 0)
        
        print("\n✓ Test completado — motor y servo funcionan")
        ser.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == '__main__':
    main()
