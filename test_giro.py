#!/usr/bin/env python3
"""Prueba rápida de giro: servo a un lado + motor adelante por N segundos.

Seguridad: usa --confirm-wheels-lifted para ejecutar movimiento real.
"""
from __future__ import annotations

import argparse
import glob
import time

import serial


def autodetect_port() -> str | None:
    patterns = [
        "/dev/serial/by-id/*Espressif*",
        "/dev/serial/by-id/*USB_JTAG*",
        "/dev/serial/by-id/*1a86*USB_Serial*",
        "/dev/serial/by-id/*1a86*",
        "/dev/ttyACM*",
        "/dev/ttyUSB*",
    ]
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[0]
    return None


def send(ser: serial.Serial, angle: int, speed: int) -> str:
    angle = max(0, min(180, angle))
    speed = max(-255, min(255, speed))
    cmd = f"S{angle},M{speed}\n"
    ser.write(cmd.encode())
    ser.flush()
    time.sleep(0.12)
    resp = ser.read(ser.in_waiting or 256).decode(errors="ignore").strip()
    return resp


def hold(ser: serial.Serial, angle: int, speed: int, seconds: float, refresh: float = 0.4) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        resp = send(ser, angle, speed)
        if resp:
            print(f"  < {resp}")
        remaining = max(0.0, end - time.monotonic())
        time.sleep(min(refresh, remaining))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=autodetect_port(), help="Puerto serie ESP32/S3")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--speed", type=int, default=255, help="Velocidad adelante PWM (default: 255)")
    parser.add_argument("--seconds", type=float, default=2.0, help="Duración de cada giro en segundos (default: 2.0)")
    parser.add_argument("--left-angle", type=int, default=0, help="Ángulo servo izquierda (default: 0)")
    parser.add_argument("--right-angle", type=int, default=90, help="Ángulo servo derecha (default: 90)")
    parser.add_argument("--center-angle", type=int, default=45, help="Ángulo servo centro (default: 45)")
    parser.add_argument("--confirm-wheels-lifted", action="store_true", help="Confirma que las llantas están levantadas / zona segura")
    args = parser.parse_args()

    if not args.port:
        parser.error("No se detectó puerto serie. Usa --port")
    if not args.confirm_wheels_lifted:
        parser.error("Por seguridad, agrega --confirm-wheels-lifted (llantas levantadas / zona segura).")
    for name in ("speed",):
        v = getattr(args, name)
        if not 0 <= v <= 255:
            parser.error(f"--{name} debe estar entre 0 y 255")
    for name in ("left_angle", "right_angle", "center_angle"):
        v = getattr(args, name)
        if not 0 <= v <= 180:
            parser.error(f"--{name.replace('_','-')} debe estar entre 0 y 180")

    print(f"Puerto: {args.port} @ {args.baud}")
    print(f"Prueba: izquierda {args.left_angle}° y derecha {args.right_angle}°, {args.seconds}s @ PWM {args.speed}")

    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        time.sleep(2.0)
        boot = ser.read_all().decode(errors="ignore").strip()
        if boot:
            print(f"MCU: {boot}")

        try:
            print(f"\n[1] Centro {args.center_angle}°, motor 0")
            print(f"  < {send(ser, args.center_angle, 0)}")
            time.sleep(1.0)

            print(f"\n[2] IZQUIERDA {args.left_angle}° adelante PWM {args.speed} por {args.seconds}s")
            hold(ser, args.left_angle, args.speed, args.seconds)

            print(f"\n[3] IZQUIERDA {args.left_angle}° retroceso PWM {args.speed} por {args.seconds}s (regreso)")
            hold(ser, args.left_angle, -args.speed, args.seconds)

            print(f"\n[4] Stop centro {args.center_angle}°")
            print(f"  < {send(ser, args.center_angle, 0)}")
            time.sleep(1.0)

            print(f"\n[5] DERECHA {args.right_angle}° adelante PWM {args.speed} por {args.seconds}s")
            hold(ser, args.right_angle, args.speed, args.seconds)

            print(f"\n[6] DERECHA {args.right_angle}° retroceso PWM {args.speed} por {args.seconds}s (regreso)")
            hold(ser, args.right_angle, -args.speed, args.seconds)

            print(f"\n[7] Stop centro {args.center_angle}°")
            print(f"  < {send(ser, args.center_angle, 0)}")
        except KeyboardInterrupt:
            print("\nInterrumpido.")
        finally:
            try:
                send(ser, args.center_angle, 0)
                time.sleep(0.2)
                send(ser, args.center_angle, 0)
            except Exception:
                pass

    print("Prueba terminada (motor en 0).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
