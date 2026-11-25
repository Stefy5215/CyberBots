import argparse
import time

import serial


def main() -> int:
    parser = argparse.ArgumentParser(description="Control manual del servo del ESP32 por USB serial.")
    parser.add_argument(
        "--port",
        default="/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
        help="Puerto serie del ESP32.",
    )
    parser.add_argument("--baud", type=int, default=9600, help="Baudrate (default: 9600).")
    parser.add_argument(
        "--angle",
        type=int,
        help="Mueve el servo una vez a este ángulo (0-180) y sale. Si se omite, modo interactivo.",
    )
    args = parser.parse_args()

    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        time.sleep(2.0)  # el ESP32 suele reiniciarse al abrir el puerto
        boot = ser.read_all().decode(errors="ignore").strip()
        if boot:
            print(boot)

        def send_angle(angle: int) -> None:
            angle = max(0, min(180, angle))
            ser.write(f"S{angle},M0\n".encode())
            ser.flush()
            time.sleep(0.3)
            resp = ser.read_all().decode(errors="ignore").strip()
            print(resp or f"Enviado S{angle},M0")

        if args.angle is not None:
            send_angle(args.angle)
            return 0

        print('Modo interactivo: escribe un ángulo (0-180, ej: 35, 50, 65) y Enter. "q" para salir.')
        while True:
            try:
                cmd = input("angulo> ").strip()
            except EOFError:
                print()
                break
            if not cmd:
                continue
            if cmd.lower() in {"q", "quit", "exit"}:
                break
            try:
                angle = int(cmd)
            except ValueError:
                print("Ingresa un número entero (0-180) o q para salir.")
                continue
            send_angle(angle)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
