#!/usr/bin/env python3
"""Prueba de conexión de componentes"""
import serial
import time
import sys

#!/usr/bin/env python3
"""Connection test for RPLIDAR C1 and Arduino"""

import serial
import time
import sys
import os

def check_permissions():
    """Check if user has access to serial ports"""
    print("🔐 Checking serial port permissions...")

    # Check if user is in dialout group
    try:
        groups = os.popen('groups').read().strip().split()
        if 'dialout' in groups:
            print("✅ User is in dialout group")
            return True
        else:
            print("⚠️  User NOT in dialout group")
            print("   Run: sudo usermod -a -G dialout $USER")
            print("   Then logout and login again")
            return False
    except:
        print("❌ Could not check groups")
        return False

def list_serial_ports():
    """List available serial ports"""
    print("\n🔌 Available serial ports:")
    try:
        import glob
        ports = glob.glob('/dev/tty[AU]*')
        if ports:
            for port in sorted(ports):
                print(f"   {port}")
        else:
            print("   No serial ports found")
            print("   Make sure devices are connected and powered")
    except:
        print("   Could not list ports")

def test_arduino(port='/dev/ttyACM0', baudrate=9600):
    """Test Arduino connection"""
    print(f"\n🤖 Testing Arduino on {port}...")

    try:
        arduino = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Wait for Arduino reset

        # Send test command
        test_cmd = "S90,M100\n"
        arduino.write(test_cmd.encode())
        print(f"✅ Sent test command: {test_cmd.strip()}")

        time.sleep(0.5)

        # Send stop command
        stop_cmd = "S90,M0\n"
        arduino.write(stop_cmd.encode())
        print(f"✅ Sent stop command: {stop_cmd.strip()}")

        arduino.close()
        print("✅ Arduino test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Arduino test failed: {e}")
        return False

def test_lidar(port='/dev/ttyUSB0'):
    """Test RPLIDAR C1 connection"""
    print(f"\n🔍 Testing RPLIDAR C1 on {port}...")

    try:
        from rplidar import RPLidar
    except ImportError:
        print("❌ rplidar library not installed")
        print("   Install with: pip install rplidar")
        return False

    lidar = None
    try:
        lidar = RPLidar(port, baudrate=115200)

        # Get device info
        info = lidar.get_device_info()
        print("✅ RPLIDAR connected!"        print(f"   Model: {info.model}")
        print(f"   Firmware: {info.firmware_version}")
        print(f"   Hardware: {info.hardware_version}")

        # Get health
        health = lidar.get_device_health()
        print(f"   Health: {health.status}")

        # Quick scan test
        print("   Testing scan...")
        scan_count = 0
        for scan in lidar.iter_scans():
            scan_count += 1
            print(f"   ✅ Scan {scan_count}: {len(scan)} points")
            if scan_count >= 2:
                break
            time.sleep(0.5)

        print("✅ RPLIDAR test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ RPLIDAR test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check USB connection and power supply")
        print("2. Try different USB port")
        print("3. Verify RPLIDAR has stable 5V power")
        print("4. Check permissions (run as sudo if needed)")
        return False

    finally:
        if lidar:
            lidar.stop()
            lidar.disconnect()

def main():
    print("=" * 60)
    print("ROBOT CONNECTION DIAGNOSTIC")
    print("=" * 60)

    # Check environment
    check_permissions()
    list_serial_ports()

    # Test components
    arduino_ok = test_arduino()
    lidar_ok = test_lidar()

    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    if arduino_ok and lidar_ok:
        print("🎉 ALL TESTS PASSED!")
        print("Your robot should be ready to run.")
        print("Command: python3 esquiva_obstaculos.py")
    else:
        print("❌ Some tests failed:")
        if not arduino_ok:
            print("   - Arduino connection failed")
        if not lidar_ok:
            print("   - RPLIDAR connection failed")
        print("\n🔧 Check connections and try again")

    print("=" * 60)

if __name__ == '__main__':
    main()
    print("="*50)
    
    arduino_ok = test_arduino()
    lidar_ok = test_lidar()
    
    print("\n" + "="*50)
    print(f"Arduino: {'✓' if arduino_ok else '✗'}")
    print(f"LiDAR:   {'✓' if lidar_ok else '✗'}")
    print("="*50)
