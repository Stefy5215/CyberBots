#!/usr/bin/env python3
"""
Test script for RPLIDAR C1
This script tests the LIDAR connection and basic functionality
"""

import time
import sys

try:
    from rplidar import RPLidar
except ImportError:
    print("❌ Error: rplidar library not installed")
    print("Install with: pip install rplidar")
    sys.exit(1)

# RPLIDAR C1 Configuration
LIDAR_PORT = '/dev/ttyUSB0'  # Check with: ls /dev/ttyUSB*
LIDAR_BAUDRATE = 115200     # RPLIDAR C1 default baudrate

def test_lidar_connection():
    """Test basic LIDAR connection and read some scans"""
    print("🔍 Testing RPLIDAR C1 connection...")
    print(f"Port: {LIDAR_PORT}")
    print(f"Baudrate: {LIDAR_BAUDRATE}")
    print("-" * 40)

    lidar = None
    try:
        # Connect to LIDAR
        print("📡 Connecting to LIDAR...")
        lidar = RPLidar(LIDAR_PORT, baudrate=LIDAR_BAUDRATE)
        print("✅ LIDAR connected successfully!")

        # Get device info
        info = lidar.get_device_info()
        print(f"📋 Device Info: {info}")

        # Get health status
        health = lidar.get_device_health()
        print(f"🏥 Health Status: {health}")

        # Test scanning
        print("\n🔄 Testing scan functionality...")
        print("Reading 5 scans (press Ctrl+C to stop early):")

        scan_count = 0
        for scan in lidar.iter_scans():
            scan_count += 1
            print(f"📊 Scan {scan_count}: {len(scan)} points")

            # Show first few points of each scan
            if len(scan) > 0:
                print("   Sample points:")
                for i, (quality, angle, distance) in enumerate(scan[:3]):
                    print(".1f"
            print()

            if scan_count >= 5:
                break

            time.sleep(0.5)  # Small delay between scans

        print("✅ LIDAR test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check USB connection: ls /dev/ttyUSB*")
        print("2. Verify power supply (RPLIDAR needs stable 5V)")
        print("3. Try different USB port")
        print("4. Check permissions: sudo usermod -a -G dialout $USER")
        return False

    finally:
        if lidar:
            print("🔌 Disconnecting LIDAR...")
            lidar.stop()
            lidar.disconnect()
            print("✅ Disconnected")

if __name__ == '__main__':
    print("=" * 50)
    print("RPLIDAR C1 TEST SCRIPT")
    print("=" * 50)

    success = test_lidar_connection()

    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED - LIDAR is working!")
        print("You can now run: python3 esquiva_obstaculos.py")
    else:
        print("❌ TEST FAILED - Check connections and try again")
    print("=" * 50)