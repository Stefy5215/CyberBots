#!/usr/bin/env python3
"""Guarded one-motor, one-servo test for a classic ESP32 + L298N."""

import argparse
import time

import serial


SERVO_ANGLE = 55
TEST_SPEED = 255
PULSE_SECONDS = 4.0


def wait_for(ser, expected, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = ser.readline().decode("ascii", errors="replace").strip()
        if line:
            print(f"ESP32: {line}")
            if line == expected:
                return True
            if line.startswith("ERR"):
                return False
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", help="ESP32 serial port, e.g. /dev/ttyUSB0")
    parser.add_argument(
        "--confirm-wheels-lifted",
        action="store_true",
        help="Confirm the drive wheel is lifted and the motor cutoff is reachable",
    )
    args = parser.parse_args()
    if not args.confirm_wheels_lifted:
        parser.error("Lift the drive wheel and rerun with --confirm-wheels-lifted")

    ser = serial.Serial(args.port, 9600, timeout=0.2, write_timeout=0.5)
    moving = False
    try:
        time.sleep(0.5)
        ser.write(f"S{SERVO_ANGLE},M0\n".encode("ascii"))
        if not wait_for(ser, f"OK S{SERVO_ANGLE} M0", 1.0):
            raise SystemExit("No L298N stop acknowledgement; no motor command was sent.")

        ser.write(f"S{SERVO_ANGLE},M{TEST_SPEED}\n".encode("ascii"))
        moving = True
        if not wait_for(ser, f"OK S{SERVO_ANGLE} M{TEST_SPEED}", 1.0):
            raise SystemExit("No motor acknowledgement; watchdog should stop within 1 s.")

        pulse_deadline = time.monotonic() + PULSE_SECONDS
        while time.monotonic() < pulse_deadline:
            time.sleep(min(0.3, pulse_deadline - time.monotonic()))
            if time.monotonic() >= pulse_deadline:
                break
            ser.write(f"S{SERVO_ANGLE},M{TEST_SPEED}\n".encode("ascii"))
            if not wait_for(ser, f"OK S{SERVO_ANGLE} M{TEST_SPEED}", 0.7):
                raise SystemExit("Motor command acknowledgement lost; watchdog should stop within 1 s.")

        ser.write(f"S{SERVO_ANGLE},M0\n".encode("ascii"))
        if not wait_for(ser, f"OK S{SERVO_ANGLE} M0", 1.0):
            raise SystemExit("Stop sent without acknowledgement; cut motor battery if it keeps turning.")
        moving = False
        print("TEST COMPLETE: PWM 255 for 4 s, servo command 55 degrees, stop acknowledged.")
    finally:
        if moving:
            try:
                ser.write(f"S{SERVO_ANGLE},M0\n".encode("ascii"))
            except serial.SerialException:
                pass
        ser.close()


if __name__ == "__main__":
    main()