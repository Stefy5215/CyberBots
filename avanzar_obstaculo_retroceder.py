#!/usr/bin/env python3
"""Avanza con LiDAR, reduce velocidad al acercarse, frena y retrocede ante obstáculo frontal.

Usa RPLIDAR C1 + ESP32/S3 (protocolo S<angulo>,M<velocidad>).
Por seguridad, NO mueve motores a menos que pases --drive.
"""

from __future__ import annotations

import argparse
import glob
import os
import threading
import time

from lidar_c1 import RPLidarC1, ScanNode


def normalize_deg(angle: float) -> float:
    return angle % 360.0


def car_relative_angle(lidar_angle_deg: float, car_front_lidar_deg: float) -> float:
    """Ángulo en marco del carro: 0=frente, 90=derecha, 180=atrás, 270=izquierda."""
    return normalize_deg(lidar_angle_deg - car_front_lidar_deg)


def front_distance_mm(
    scan: list[ScanNode],
    car_front_lidar_deg: float,
    half_width_deg: float = 25.0,
    min_mm: float = 50.0,
    max_mm: float = 8000.0,
    percentile: float = 0.2,
) -> float | None:
    distances = []
    for node in scan:
        if node.quality <= 0 or not (min_mm <= node.distance_mm <= max_mm):
            continue
        rel = car_relative_angle(node.angle_deg, car_front_lidar_deg)
        delta = abs((rel + 180.0) % 360.0 - 180.0)  # distancia angular a 0°
        if delta <= half_width_deg:
            distances.append(node.distance_mm)
    if not distances:
        return None
    ordered = sorted(distances)
    idx = int((len(ordered) - 1) * percentile)
    return ordered[idx]


def side_clearance_mm(
    scan: list[ScanNode],
    car_front_lidar_deg: float,
    center_deg: float,
    half_width_deg: float = 45.0,
    min_mm: float = 50.0,
    max_mm: float = 8000.0,
    percentile: float = 0.2,
) -> float | None:
    """Clearance around a car-relative direction (0=front,90=right,180=back,270=left)."""
    distances = []
    for node in scan:
        if node.quality <= 0 or not (min_mm <= node.distance_mm <= max_mm):
            continue
        rel = car_relative_angle(node.angle_deg, car_front_lidar_deg)
        delta = abs((rel - center_deg + 180.0) % 360.0 - 180.0)
        if delta <= half_width_deg:
            distances.append(node.distance_mm)
    if not distances:
        return None
    ordered = sorted(distances)
    idx = int((len(ordered) - 1) * percentile)
    return ordered[idx]


def autodetect_mcu_port(lidar_port: str | None = None) -> str | None:
    patterns = [
        "/dev/serial/by-id/*Espressif*",
        "/dev/serial/by-id/*USB_JTAG*",
        "/dev/serial/by-id/*1a86*USB_Serial*",
        "/dev/serial/by-id/*1a86*",
    ]
    lidar_real = os.path.realpath(lidar_port) if lidar_port else None
    for pat in patterns:
        for match in sorted(glob.glob(pat)):
            if lidar_real and os.path.realpath(match) == lidar_real:
                continue
            return match
    for pat in ("/dev/ttyACM*", "/dev/ttyUSB*"):
        for match in sorted(glob.glob(pat)):
            if lidar_real and os.path.realpath(match) == lidar_real:
                continue
            return match
    return None


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def compute_forward_speed(front_mm: float, stop_mm: float, slow_mm: float, max_speed: int, min_speed: int) -> int:
    """Reduce velocidad al acercarse al obstáculo; 0 si está en/por debajo de stop_mm."""
    if front_mm <= stop_mm:
        return 0
    if front_mm >= slow_mm:
        return max_speed
    span = max(slow_mm - stop_mm, 1.0)
    ratio = (front_mm - stop_mm) / span  # 0..1
    speed = min_speed + ratio * (max_speed - min_speed)
    return int(clamp(round(speed), min(min_speed, max_speed), max_speed))


class MotorController:
    """Envía comandos al ESP32/S3 y los refresca en background para evitar watchdog."""

    def __init__(self, port: str, baud: int = 9600, refresh: float = 0.4):
        import serial

        self.ser = serial.Serial(port, baud, timeout=0.2, write_timeout=1)
        self.refresh = refresh
        self._lock = threading.Lock()
        self._ser_lock = threading.Lock()
        self._angle = 45
        self._speed = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        time.sleep(2.0)
        try:
            with self._ser_lock:
                boot = self.ser.read_all().decode(errors="ignore").strip()
            if boot:
                print(f"MCU: {boot}")
        except Exception:
            pass
        self._thread.start()

    def set(self, angle: int, speed: int):
        with self._lock:
            self._angle = int(clamp(angle, 0, 180))
            self._speed = int(clamp(speed, -255, 255))

    def get(self):
        with self._lock:
            return self._angle, self._speed

    def _send_once(self, angle: int, speed: int):
        cmd = f"S{angle},M{speed}\n".encode()
        with self._ser_lock:
            self.ser.write(cmd)
            self.ser.flush()
            time.sleep(0.05)
            try:
                self.ser.read(self.ser.in_waiting or 0)
            except Exception:
                pass

    def _loop(self):
        while not self._stop.is_set():
            angle, speed = self.get()
            try:
                self._send_once(angle, speed)
            except Exception:
                # si falla el puerto, dejamos que el hilo principal maneje
                pass
            self._stop.wait(self.refresh)

    def close(self):
        self._stop.set()
        try:
            self._send_once(self._angle, 0)
            time.sleep(0.15)
            self._send_once(self._angle, 0)
        except Exception:
            pass
        self._thread.join(timeout=1.0)
        try:
            self.ser.close()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lidar-port", required=True, help="Puerto serie del RPLIDAR C1")
    parser.add_argument("--mcu-port", default=None, help="Puerto serie del ESP32/S3 (auto-detect por defecto, excluyendo el LiDAR)")
    parser.add_argument("--drive", action="store_true", help="Habilita movimiento real (por defecto solo diagnóstico)")
    parser.add_argument("--speed", type=int, default=230, help="Velocidad máxima PWM hacia adelante 0-255 (default: 230)")
    parser.add_argument("--min-speed", type=int, default=140, help="Velocidad mínima PWM al acercarse (default: 140, útil por peso)")
    parser.add_argument("--threshold-mm", type=float, default=400.0, help="Distancia frontal para frenar/reversa en mm (default: 400 = 40cm)")
    parser.add_argument("--slow-mm", type=float, default=800.0, help="Distancia desde la que empieza a reducir velocidad en mm (default: 800)")
    parser.add_argument("--brake-reverse-seconds", type=float, default=0.30, help="Freno activo en reversa al detectar obstáculo (default: 0.30)")
    parser.add_argument("--backup-seconds", type=float, default=1.15, help="Reversa de despeje antes de ciclos (default: 1.15)")
    parser.add_argument("--backup-speed", type=int, default=230, help="PWM de reversa/freno activo (default: 230)")
    parser.add_argument("--brake-forward-seconds", type=float, default=0.15, help="Freno hacia adelante tras retroceder (default: 0.15)")
    parser.add_argument("--brake-forward-speed", type=int, default=180, help="PWM para frenar retroceso yendo adelante (default: 180)")
    parser.add_argument("--cycle-count", type=int, default=3, help="Ciclos de giro por maniobra (default: 3)")
    parser.add_argument("--cycle-turn-seconds", type=float, default=1.0, help="Duración giro adelante en ciclo normal (default: 1.0)")
    parser.add_argument("--cycle-turn-extra-seconds", type=float, default=1.2, help="Duración giro adelante en ciclo 2 (default: 1.2)")
    parser.add_argument("--cycle-pause-seconds", type=float, default=0.8, help="Pausa antes de reversa en ciclo (default: 0.8)")
    parser.add_argument("--cycle-reverse-seconds", type=float, default=0.6, help="Reversa recta en ciclo (default: 0.6)")
    parser.add_argument("--cycle-end-pause-seconds", type=float, default=0.3, help="Pausa final de ciclo (default: 0.3)")
    parser.add_argument("--turn-speed", type=int, default=255, help="Velocidad PWM adelante durante giro de ciclo (default: 255)")
    parser.add_argument("--turn-angle-left", type=int, default=0, help="Ángulo servo para giro izquierda (default: 0)")
    parser.add_argument("--turn-angle-right", type=int, default=90, help="Ángulo servo para giro derecha (default: 90)")
    parser.add_argument("--servo-center", type=int, default=45, help="Ángulo servo centrado (default: 45)")
    parser.add_argument("--lidar-front-deg", type=float, default=270.0, help="Ángulo LiDAR que apunta al frente del carro (default: 270)")
    parser.add_argument("--front-half-width", type=float, default=25.0, help="Semiancho del sector frontal en grados (default: 25)")
    parser.add_argument("--side-min-clear-mm", type=float, default=350.0, help="Clearance mínima lateral para preferir un lado (default: 350)")
    parser.add_argument("--refresh", type=float, default=0.4, help="Intervalo de reenvío de comando en segundos (default: 0.4)")
    parser.add_argument("--log-every", type=int, default=1, help="Imprimir cada N escaneos completos (default: 1)")
    args = parser.parse_args()

    if args.mcu_port is None:
        args.mcu_port = autodetect_mcu_port(args.lidar_port)

    if args.drive and not args.mcu_port:
        parser.error("--drive requiere --mcu-port (no se detectó ESP32/S3 automáticamente)")

    for name in ("speed", "min_speed", "backup_speed", "brake_forward_speed", "turn_speed"):
        v = getattr(args, name)
        if not 0 <= v <= 255:
            parser.error(f"--{name.replace('_','-')} debe estar entre 0 y 255")
    if args.min_speed > args.speed:
        parser.error("--min-speed no puede ser mayor que --speed")
    for name in ("servo_center", "turn_angle_left", "turn_angle_right"):
        v = getattr(args, name)
        if not 0 <= v <= 180:
            parser.error(f"--{name.replace('_','-')} debe estar entre 0 y 180")
    if args.slow_mm <= args.threshold_mm:
        parser.error("--slow-mm debe ser mayor que --threshold-mm")
    if args.cycle_count < 1:
        parser.error("--cycle-count debe ser >= 1")

    lidar_real = os.path.realpath(args.lidar_port)
    if args.mcu_port and os.path.realpath(args.mcu_port) == lidar_real:
        parser.error("El puerto MCU y el LiDAR son el mismo dispositivo. Conecta el ESP32/S3 en otro puerto.")

    try:
        import serial  # noqa: F401
    except ImportError:
        parser.error("Falta pyserial. Instala con: pip install pyserial")

    controller: MotorController | None = None
    lidar = RPLidarC1(args.lidar_port)
    scan_count = 0

    def drain_lidar(duration_s: float) -> None:
        """Mantiene drenado el buffer del LiDAR durante maniobras temporizadas."""
        end = time.monotonic() + max(0.0, duration_s)
        while time.monotonic() < end:
            try:
                if lidar._serial is not None:
                    lidar._serial.read(512)
            except Exception:
                pass
            time.sleep(0.02)

    def hold_motion(angle: int, speed: int, seconds: float) -> None:
        if controller is not None:
            controller.set(angle, speed)
        drain_lidar(seconds)

    def do_obstacle_maneuver(scan: list[ScanNode]) -> str:
        left_clear = side_clearance_mm(scan, args.lidar_front_deg, 270.0)
        right_clear = side_clearance_mm(scan, args.lidar_front_deg, 90.0)
        lc = left_clear if left_clear is not None else -1.0
        rc = right_clear if right_clear is not None else -1.0

        if rc < args.side_min_clear_mm and lc >= args.side_min_clear_mm:
            turn_dir = 0
        elif lc < args.side_min_clear_mm and rc >= args.side_min_clear_mm:
            turn_dir = 1
        elif lc > rc:
            turn_dir = 0
        elif rc > lc:
            turn_dir = 1
        else:
            turn_dir = 0

        turn_angle = args.turn_angle_left if turn_dir == 0 else args.turn_angle_right
        side_name = "IZQ" if turn_dir == 0 else "DER"
        ltxt = f"{left_clear:.0f}mm" if left_clear is not None else "--"
        rtxt = f"{right_clear:.0f}mm" if right_clear is not None else "--"
        print(
            f"OBSTACULO -> lado {side_name} (servo {turn_angle}°) "
            f"clear izq={ltxt} der={rtxt}"
        )

        # 1) Freno activo con reversa para no seguir avanzando por inercia.
        print(f"  freno activo reversa {args.brake_reverse_seconds:.2f}s @ {args.backup_speed}")
        hold_motion(args.servo_center, -args.backup_speed, args.brake_reverse_seconds)

        # 2) Retrocede para despejar.
        print(f"  retroceso despeje {args.backup_seconds:.2f}s @ {args.backup_speed}")
        hold_motion(args.servo_center, -args.backup_speed, args.backup_seconds)

        # 3) Frena el retroceso avanzando un poco.
        print(f"  freno avance {args.brake_forward_seconds:.2f}s @ {args.brake_forward_speed}")
        hold_motion(args.servo_center, args.brake_forward_speed, args.brake_forward_seconds)
        hold_motion(args.servo_center, 0, 0.2)

        # 4) Ciclos de giro hacia el lado con espacio.
        for i in range(1, args.cycle_count + 1):
            giro_s = args.cycle_turn_extra_seconds if i == 2 else args.cycle_turn_seconds
            print(f"  ciclo {i}/{args.cycle_count}: giro {side_name} {turn_angle}° adelante {giro_s:.2f}s @ {args.turn_speed}")
            hold_motion(turn_angle, args.turn_speed, giro_s)
            hold_motion(args.servo_center, 0, args.cycle_pause_seconds)
            hold_motion(args.servo_center, -args.backup_speed, args.cycle_reverse_seconds)
            hold_motion(args.servo_center, 0, args.cycle_end_pause_seconds)

        hold_motion(args.servo_center, 0, 0.1)
        return side_name

    try:
        if args.mcu_port:
            controller = MotorController(args.mcu_port, baud=9600, refresh=args.refresh)
            controller.start()
            controller.set(args.servo_center, 0)
            print(f"ESP32/S3 conectado en {args.mcu_port}")

        if args.drive:
            print(
                f"DRIVE: vel máx {args.speed} (mín {args.min_speed}), "
                f"frena/reversa a {args.threshold_mm:.0f}mm, baja desde {args.slow_mm:.0f}mm, "
                f"ciclos={args.cycle_count} giro IZQ={args.turn_angle_left}° DER={args.turn_angle_right}°"
            )
        else:
            print("DIAGNÓSTICO: no se enviarán comandos de movimiento. Usa --drive para habilitar.")

        lidar.start()
        print(f"LiDAR leyendo {args.lidar_port} @ 460800 (frente LiDAR={args.lidar_front_deg}°)")

        for scan, is_new_rev in lidar.iter_scans_fast(yield_every_nodes=12):
            if is_new_rev:
                scan_count += 1
            front = front_distance_mm(scan, args.lidar_front_deg, half_width_deg=args.front_half_width)
            desired_angle = args.servo_center

            if front is None:
                desired_speed = 0
                action = "SIN_LECTURA_FRENTE -> STOP"
            elif front <= args.threshold_mm:
                if args.drive and controller is not None:
                    controller.set(args.servo_center, 0)
                side = do_obstacle_maneuver(scan)
                action = f"MANIOBRA_COMPLETA lado {side}"
                # después de la maniobra, continuar con siguiente lectura
                desired_speed = 0
                desired_angle = args.servo_center
                if args.drive and controller is not None:
                    controller.set(args.servo_center, 0)
                # limpia buffer viejo de LiDAR para reaccionar a estado actual
                try:
                    if lidar._serial is not None:
                        lidar._serial.reset_input_buffer()
                        lidar._buffer.clear()
                except Exception:
                    pass
            else:
                desired_speed = compute_forward_speed(front, args.threshold_mm, args.slow_mm, args.speed, args.min_speed)
                if desired_speed < args.speed:
                    action = f"ACERCANDO frente={front:.0f}mm -> vel {desired_speed}"
                else:
                    action = f"AVANZAR frente={front:.0f}mm vel {desired_speed}"

            if args.drive and controller is not None and not (front is not None and front <= args.threshold_mm):
                controller.set(desired_angle, desired_speed)

            should_log = (is_new_rev and scan_count % args.log_every == 0) or "MANIOBRA_COMPLETA" in action
            if should_log:
                ftxt = "--" if front is None else f"{front:.0f}mm"
                print(f"scan={scan_count} frente={ftxt} accion={action}")

    except KeyboardInterrupt:
        print("\nInterrumpido por usuario.")
    except TimeoutError as e:
        print(f"\nLiDAR: {e}")
        print("Sugerencia: revisa alimentación/cable USB del LiDAR y que no comparta puerto con el MCU.")
    finally:
        try:
            if controller is not None:
                controller.close()
        except Exception:
            pass
        try:
            lidar.stop()
        except Exception:
            pass
        print("Detenido (motor en 0).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
