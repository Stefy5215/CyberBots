#!/usr/bin/env python3
"""
Test RPLIDAR C1 con diferentes configuraciones
"""

import serial
import time

LIDAR_PORT = '/dev/ttyUSB1'

def test_baudrate(baudrate):
    try:
        print(f"Probando baudrate {baudrate}...")
        ser = serial.Serial(LIDAR_PORT, baudrate, timeout=1)
        time.sleep(2)
        
        # Enviar comando de información
        ser.write(b'\xA5\x50')
        time.sleep(0.1)
        
        response = ser.read(7)
        if response:
            print(f"  Respuesta: {response.hex()}")
            if len(response) == 7 and response[0] == 0xA5:
                print(f"  ✓ LiDAR responde en {baudrate}")
                ser.close()
                return True
        else:
            print("  No respuesta")
        
        ser.close()
        return False
        
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 256000, 460800, 921600]
    
    print("Probando diferentes baudrates para RPLIDAR C1...")
    
    for baud in baudrates:
        if test_baudrate(baud):
            print(f"\n✓ LiDAR funciona en {baud} baud")
            break
    else:
        print("\n✗ No se encontró baudrate compatible")

if __name__ == '__main__':
    main()