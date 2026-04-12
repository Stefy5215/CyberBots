#!/usr/bin/env python3
"""
Test raw del puerto serial del LiDAR
"""

import serial
import time

LIDAR_PORT = '/dev/ttyUSB1'
LIDAR_BAUDRATE = 115200

def test_raw():
    try:
        print(f"Abriendo puerto {LIDAR_PORT} a {LIDAR_BAUDRATE}...")
        ser = serial.Serial(LIDAR_PORT, LIDAR_BAUDRATE, timeout=1)
        time.sleep(2)
        print("✓ Puerto abierto")
        
        print("Leyendo datos raw por 10 segundos...")
        start_time = time.time()
        while time.time() - start_time < 10:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"Recibido: {data.hex()} ({len(data)} bytes)")
            time.sleep(0.1)
        
        ser.close()
        print("✓ Test completado")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == '__main__':
    test_raw()