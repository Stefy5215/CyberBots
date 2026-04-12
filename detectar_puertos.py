#!/usr/bin/env python3
"""
Port detection utility for RPLIDAR and Arduino
Run this to find the correct serial ports for your devices
"""

import serial
import time
import glob
import sys

def detect_ports():
    """Detect available serial ports"""
    print("🔍 Detecting serial ports...")

    ports = glob.glob('/dev/tty[AU]*')
    if not ports:
        print("❌ No serial ports found!")
        print("   Make sure your devices are connected and powered on")
        return []

    print(f"📋 Found {len(ports)} serial ports:")
    for port in sorted(ports):
        print(f"   {port}")

    return ports

def test_port(port, name, baudrate=None):
    """Test if a port responds to connection"""
    try:
        if baudrate:
            ser = serial.Serial(port, baudrate, timeout=1)
        else:
            # Try common baudrates
            for br in [9600, 115200, 460800]:
                try:
                    ser = serial.Serial(port, br, timeout=1)
                    break
                except:
                    continue
            else:
                return False, "Could not connect at any baudrate"

        time.sleep(0.5)  # Let device initialize

        # Try to read something
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            ser.close()
            return True, f"Received {len(data)} bytes"
        else:
            ser.close()
            return True, "Connected (no data received)"

    except Exception as e:
        return False, str(e)

def identify_devices():
    """Try to identify which ports have Arduino vs RPLIDAR"""
    print("\n🔬 Testing ports for devices...")

    ports = detect_ports()
    if not ports:
        return

    arduino_candidates = []
    lidar_candidates = []

    for port in ports:
        print(f"\nTesting {port}:")

        # Test as Arduino (9600 baud)
        success, msg = test_port(port, "Arduino", 9600)
        if success:
            print(f"   🤖 Arduino: {msg}")
            arduino_candidates.append(port)
        else:
            print(f"   ❌ Arduino: {msg}")

        # Test as RPLIDAR (115200 baud)
        success, msg = test_port(port, "RPLIDAR", 115200)
        if success:
            print(f"   🔍 RPLIDAR: {msg}")
            lidar_candidates.append(port)
        else:
            print(f"   ❌ RPLIDAR: {msg}")

    # Recommendations
    print("\n" + "="*50)
    print("RECOMMENDATIONS")
    print("="*50)

    if arduino_candidates:
        print(f"🤖 Arduino ports: {', '.join(arduino_candidates)}")
        print("   Use the first one in your scripts")
    else:
        print("🤖 No Arduino detected")
        print("   Check Arduino connection and power")

    if lidar_candidates:
        print(f"🔍 RPLIDAR ports: {', '.join(lidar_candidates)}")
        print("   Use the first one in your scripts")
    else:
        print("🔍 No RPLIDAR detected")
        print("   Check RPLIDAR connection and power (needs 5V)")

    if arduino_candidates and lidar_candidates:
        print("\n✅ Both devices detected! Ready to run:")
        print("   python3 prueba_conexiones.py")
        print("   python3 esquiva_obstaculos.py")

def main():
    print("=" * 60)
    print("SERIAL PORT DETECTOR")
    print("For RPLIDAR C1 + Arduino Robot")
    print("=" * 60)

    identify_devices()

    print("\n" + "=" * 60)
    print("TIPS")
    print("- RPLIDAR needs stable 5V power supply")
    print("- Arduino appears as /dev/ttyACM*")
    print("- RPLIDAR appears as /dev/ttyUSB*")
    print("- Run with sudo if permission errors occur")
    print("=" * 60)

if __name__ == '__main__':
    main()