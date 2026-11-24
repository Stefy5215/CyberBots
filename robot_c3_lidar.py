#!/usr/bin/env python3
"""LiDAR C1 navigation for a classic ESP32 + L298N robot."""

import argparse
import statistics
import time

from lidar_c1 import RPLidarC1, ScanNode


SERVO_CENTER = 55
SERVO_LEFT = 25
SERVO_RIGHT = 85
FRONT_SLOW_MM = 850
FRONT_STOP_MM = 300
SIDE_CLOSE_MM = 350
SIDE_SLOW_MM = 450


def _sector_distance(scan: list[ScanNode], angle_test) -> float | None:
    distances = [
        node.distance_mm
        for node in scan
        if node.quality > 0
        and 50 <= node.distance_mm <= 8000
        and angle_test(node.angle_deg)
    ]
    if not distances:
        return None
    distances.sort()
    return distances[int((len(distances) - 1) * 0.2)]


def summarize_scan(scan: list[ScanNode]) -> dict[str, float | None]:
    return {
        "front": _sector_distance(
            scan, lambda angle: angle <= 20 or angle >= 340
        ),
        "left": _sector_distance(scan, lambda angle: 30 <= angle <= 150),
        "right": _sector_distance(scan, lambda angle: 210 <= angle <= 330),
    }


def decide_command(
    distances: dict[str, float | None], max_speed: int
) -> tuple[int, int, str]:
    front = distances["front"]
    left = distances["left"]
    right = distances["right"]
    slow_speed = max(30, max_speed // 2)

    if front is None:
        return SERVO_CENTER, 0, "sin lecturas frontales: parada segura"
    if front <= FRONT_STOP_MM:
        return SERVO_CENTER, 0, "obstáculo crítico: parada"
    if front <= FRONT_SLOW_MM:
        left_clearance = left if left is not None else -1
        right_clearance = right if right is not None else -1
        if max(left_clearance, right_clearance) < SIDE_SLOW_MM:
            return SERVO_CENTER, 0, "frente bloqueado y laterales sin espacio"
        direction = SERVO_LEFT if left_clearance > right_clearance else SERVO_RIGHT
        return direction, slow_speed, "obstáculo al frente: giro lento"
    if left is not None and left <= SIDE_CLOSE_MM:
        return SERVO_RIGHT, slow_speed, "obstáculo cercano a la izquierda"
    if right is not None and right <= SIDE_CLOSE_MM:
        return SERVO_LEFT, slow_speed, "obstáculo cercano a la derecha"
    if left is None or right is None:
        return SERVO_CENTER, 0, "lectura lateral incompleta: parada segura"
    if left <= SIDE_SLOW_MM or right <= SIDE_SLOW_MM:
        return SERVO_CENTER, slow_speed, "obstáculo lateral: velocidad reducida"
    return SERVO_CENTER, max_speed, "camino despejado"


def send_command(controller, angle: int, speed: int) -> str:
    command = f"S{angle},M{speed}\n".encode("ascii")
    controller.write(command)
    return controller.readline().decode("ascii", errors="replace").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lidar-port", required=True, help="Puerto USB del LiDAR C1")
    parser.add_argument("--mcu-port", help="Puerto USB serial de la ESP32")
    parser.add_argument(
        "--drive",
        action="store_true",
        help="Permite movimiento; sin esta opción solo muestra decisiones y manda parada",
    )
    parser.add_argument("--max-speed", type=int, default=200, help="PWM máximo inicial (0-255)")
    args = parser.parse_args()

    if not 1 <= args.max_speed <= 255:
        parser.error("--max-speed debe estar entre 1 y 255")
    if args.drive and not args.mcu_port:
        parser.error("--drive requiere --mcu-port")

    try:
        import serial
    except ImportError:
        parser.error("Falta pyserial; instala con python3 -m pip install pyserial")

    controller = None
    lidar = RPLidarC1(args.lidar_port)
    try:
        if args.mcu_port:
            controller = serial.Serial(args.mcu_port, 9600, timeout=0.2, write_timeout=1)
            time.sleep(2)
            print(f"ESP32-C3 conectada en {args.mcu_port}")
            send_command(controller, SERVO_CENTER, 0)
        if args.drive:
            print("MODO CON MOVIMIENTO: velocidad limitada; prueba con ruedas levantadas.")
        else:
            print("MODO DIAGNÓSTICO: no se habilita el motor. Usa --drive para autorizar movimiento.")

        lidar.start()
        print(f"LiDAR C1 leyendo {args.lidar_port} a 460800 baudios")
        for scan in lidar.iter_scans():
            distances = summarize_scan(scan)
            angle, speed, reason = decide_command(distances, args.max_speed)
            actual_speed = speed if args.drive else 0
            if controller is not None:
                response = send_command(controller, angle if args.drive else SERVO_CENTER, actual_speed)
            else:
                response = ""
            front = distances["front"]
            front_text = "sin dato" if front is None else f"{front:.0f} mm"
            print(
                f"puntos={len(scan)} frente={front_text} "
                f"servo={angle if args.drive else SERVO_CENTER} motor={actual_speed} "
                f"({reason}) {response}"
            )
    except KeyboardInterrupt:
        print("\nParada solicitada")
    except (OSError, TimeoutError, RuntimeError) as error:
        print(f"Fallo seguro: {error}")
        return 1
    finally:
        try:
            lidar.stop()
        except OSError:
            pass
        if controller is not None:
            try:
                send_command(controller, SERVO_CENTER, 0)
            finally:
                controller.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())