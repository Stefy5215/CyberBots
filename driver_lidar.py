#!/usr/bin/env python3
"""
Driver simple para RPLIDAR C1 usando comunicación serial directa
"""

import serial
import time
import threading
import struct

LIDAR_PORT = '/dev/ttyUSB1'
LIDAR_BAUDRATE = 460800

class SimpleRPLidar:
    def __init__(self, port, baudrate=460800):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.running = False
        
    def connect(self):
        self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
        time.sleep(2)
        
    def start_scan(self):
        self.serial.write(b'\xA5\x20')  # Start scan
        self.running = True
        
    def stop_scan(self):
        self.running = False
        self.serial.write(b'\xA5\x25')  # Stop
        
    def iter_scans(self):
        buffer = bytearray()
        
        while self.running:
            if self.serial.in_waiting > 0:
                data = self.serial.read(self.serial.in_waiting)
                buffer.extend(data)
                
                # Procesar paquetes completos
                while len(buffer) >= 5:
                    if buffer[0] == 0xA5 and buffer[1] == 0x5A:
                        # Paquete de respuesta
                        packet_len = struct.unpack('<H', buffer[3:5])[0]
                        if len(buffer) >= 5 + packet_len:
                            packet = buffer[5:5+packet_len]
                            buffer = buffer[5+packet_len:]
                            
                            # Parse scan data
                            scan_data = []
                            for i in range(0, len(packet), 5):
                                if i + 4 < len(packet):
                                    quality = packet[i] >> 2
                                    angle = ((packet[i+1] | (packet[i] & 0x03) << 8)) / 64.0
                                    distance = (packet[i+2] | packet[i+3] << 8) / 4.0
                                    scan_data.append((quality, angle, distance))
                            
                            if scan_data:
                                yield scan_data
                        else:
                            break
                    else:
                        buffer.pop(0)  # Remove invalid byte
            else:
                time.sleep(0.01)
    
    def disconnect(self):
        if self.serial:
            self.serial.close()

# Test simple
if __name__ == '__main__':
    lidar = SimpleRPLidar(LIDAR_PORT, LIDAR_BAUDRATE)
    lidar.connect()
    lidar.start_scan()
    
    print("Leyendo escaneos...")
    for i, scan in enumerate(lidar.iter_scans()):
        if i >= 3:
            break
        print(f"Escaneo {i+1}: {len(scan)} puntos")
        for quality, angle, distance in scan[:3]:
            print(f"  Ángulo: {angle:.1f}°, Distancia: {distance:.1f}mm")
    
    lidar.stop_scan()
    lidar.disconnect()
    print("✓ Test completado")