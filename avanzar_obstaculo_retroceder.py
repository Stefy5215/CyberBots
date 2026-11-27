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

from lidar_c1 import RPLidarC1, ScanNode, decode_measurement_node


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
    min_samples: int = 3,
) -> float | None:
    """Clearance conservadora en un sector angular relativo al carrito."""
    distances = []
    for node in scan:
        if node.quality <= 0 or not (min_mm <= node.distance_mm <= max_mm):
            continue
        rel = car_relative_angle(node.angle_deg, car_front_lidar_deg)
        delta = abs((rel - center_deg + 180.0) % 360.0 - 180.0)
        if delta <= half_width_deg:
            distances.append(node.distance_mm)
    if len(distances) < min_samples:
        return None
    ordered = sorted(distances)
    idx = int((len(ordered) - 1) * percentile)
    return ordered[idx]


def directional_clearance_mm(
    scan: list[ScanNode],
    car_front_lidar_deg: float,
    relative_deg: float,
    half_width_deg: float = 30.0,
) -> tuple[float | None, int]:
    """Devuelve espacio libre y muestras de un sector físico preciso."""
    distances = []
    for node in scan:
        if node.quality <= 0 or not (50.0 <= node.distance_mm <= 8000.0):
            continue
        rel = car_relative_angle(node.angle_deg, car_front_lidar_deg)
        delta = abs((rel - relative_deg + 180.0) % 360.0 - 180.0)
        if delta <= half_width_deg:
            distances.append(node.distance_mm)

    if len(distances) < 5:
        return None, len(distances)

    ordered = sorted(distances)
    # 75% de las mediciones están libres o muy cerca de ese rango.
    idx = int((len(ordered) - 1) * 0.75)
    return ordered[idx], len(distances)


def format_360_map(scan: list[ScanNode], car_front_lidar_deg: float) -> str:
    """Compact 12-sector range panorama relative to the car's forward direction."""
    sectors: list[list[float]] = [[] for _ in range(12)]
    for node in scan:
        if node.quality <= 0 or not (50.0 <= node.distance_mm <= 8000.0):
            continue
        rel = car_relative_angle(node.angle_deg, car_front_lidar_deg)
        sectors[int(rel // 30.0) % 12].append(node.distance_mm)
    ranges = [f"{min(values) / 1000:.2f}" if values else "--" for values in sectors]
    return "360m[" + " ".join(f"{angle:03d}:{distance}" for angle, distance in zip(range(0, 360, 30), ranges)) + "]"


def update_sector_map(sector_map: list[list[float]], scan: list[ScanNode], car_front_lidar_deg: float, max_samples: int = 180) -> None:
    """Acumula medidas relativas al robot: 12 sectores, mapa local persistente."""
    for node in scan:
        if node.quality <= 0 or not (50.0 <= node.distance_mm <= 8000.0):
            continue
        rel = car_relative_angle(node.angle_deg, car_front_lidar_deg)
        sector = int(rel // 30.0) % 12
        sector_map[sector].append(node.distance_mm)
        if len(sector_map[sector]) > max_samples:
            del sector_map[sector][: len(sector_map[sector]) - max_samples]


def mapped_sector_clearance(sector_map: list[list[float]], left_side: bool, percentile: float = 0.35) -> float | None:
    """Promedia una zona lateral de 90 grados usando la mediana baja del mapa."""
    center_sector = 9 if left_side else 3  # 270° izquierda, 90° derecha
    indices = [(center_sector - 1 + i) % 12 for i in range(3)]
    distances = [distance for i in indices for distance in sector_map[i][-90:]]
    if len(distances) < 6:
        return None
    ordered = sorted(distances)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * percentile))]


def format_sector_map(sector_map: list[list[float]]) -> str:
    values = []
    for sector in sector_map:
        if not sector:
            values.append("--")
        else:
            recent = sorted(sector[-90:])
            values.append(f"{recent[max(0, int((len(recent) - 1) * 0.35))] / 1000:.2f}")
    return "MAP360[" + " ".join(f"{angle:03d}:{distance}" for angle, distance in zip(range(0, 360, 30), values)) + "]"


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
    parser.add_argument("--speed", type=int, default=210, help="Velocidad PWM hacia adelante 0-255 (default: 210)")
    parser.add_argument("--threshold-mm", type=float, default=550.0, help="Distancia frontal para frenar/reversa en mm (default: 550 = 55cm)")
    parser.add_argument("--close-mm", type=float, default=1200.0, help="Distancia desde la que comienza la desaceleración incremental (default: 1200 = 120cm)")
    parser.add_argument("--close-speed", type=int, default=170, help="Velocidad PWM mínima al llegar al obstáculo (default: 170)")
    parser.add_argument("--brake-reverse-seconds", type=float, default=0.12, help="Freno activo en reversa corta al detectar obstáculo (default: 0.12)")
    parser.add_argument("--brake-reverse-speed", type=int, default=255, help="PWM del freno activo en reversa (default: 255)")
    parser.add_argument("--backup-seconds", type=float, default=0.90, help="Único retroceso largo al inicio (default: 0.90)")
    parser.add_argument("--later-backup-seconds", type=float, default=0.60, help="Retroceso después de obstáculos posteriores (default: 0.60)")
    parser.add_argument("--backup-speed", type=int, default=220, help="PWM de reversa de despeje (default: 220)")
    parser.add_argument("--brake-forward-seconds", type=float, default=0.15, help="Freno hacia adelante tras retroceder (default: 0.15)")
    parser.add_argument("--brake-forward-speed", type=int, default=180, help="PWM para frenar retroceso yendo adelante (default: 180)")
    parser.add_argument("--cycle-count", type=int, default=2, help="Ciclos de giro y retroceso por detección posterior (default: 2)")
    parser.add_argument("--initial-search-cycles", type=int, default=3, help="Máximo de giros en la primera detección (default: 3)")
    parser.add_argument("--later-search-cycles", type=int, default=2, help="Máximo de giros en detecciones posteriores (default: 2)")
    parser.add_argument("--cycle-repeat-count", type=int, default=1, help="Una sola tanda por detección (default: 1)")
    parser.add_argument("--maneuver-limit", type=int, default=0, help="Máximo de maniobras; 0 repite indefinidamente (default: 0)")
    parser.add_argument("--cycle-turn-seconds", type=float, default=1.0, help="Duración giro adelante en ciclo normal (default: 1.0)")
    parser.add_argument("--cycle-turn-extra-seconds", type=float, default=1.2, help="Duración giro adelante en ciclo 2 (default: 1.2)")
    parser.add_argument("--cycle-pause-seconds", type=float, default=0.8, help="Pausa antes de reversa en ciclo (default: 0.8)")
    parser.add_argument("--cycle-reverse-seconds", type=float, default=0.50, help="Retrocesos posteriores durante giros de búsqueda (default: 0.50)")
    parser.add_argument("--cycle-end-pause-seconds", type=float, default=0.3, help="Pausa final de ciclo (default: 0.3)")
    parser.add_argument("--turn-speed", type=int, default=255, help="Velocidad PWM adelante durante giro de ciclo (default: 255)")
    parser.add_argument("--turn-angle-left", type=int, default=10, help="Ángulo servo para giro izquierda (default: 10)")
    parser.add_argument("--turn-angle-right", type=int, default=80, help="Ángulo servo para giro derecha (default: 80)")
    parser.add_argument("--servo-center", type=int, default=45, help="Ángulo servo centrado (default: 45)")
    parser.add_argument("--lidar-front-deg", type=float, default=270.0, help="Ángulo LiDAR que apunta al frente del carro (default: 270)")
    parser.add_argument("--front-half-width", type=float, default=25.0, help="Semiancho del sector frontal en grados (default: 25)")
    parser.add_argument("--side-min-clear-mm", type=float, default=350.0, help="Clearance mínima lateral para preferir un lado (default: 350)")
    parser.add_argument("--refresh", type=float, default=0.10, help="Intervalo rápido de reenvío de comando (default: 0.10)")
    parser.add_argument("--log-every", type=int, default=1, help="Imprimir cada N escaneos completos (default: 1)")
    parser.add_argument("--analysis-seconds", type=float, default=6.0, help="Tiempo máximo detenido para análisis lateral 360° (default: 6.0)")
    parser.add_argument("--analysis-revolutions", type=int, default=3, help="Vueltas completas 360° agregadas antes de decidir (default: 3)")
    args = parser.parse_args()

    if args.mcu_port is None:
        args.mcu_port = autodetect_mcu_port(args.lidar_port)

    if args.drive and not args.mcu_port:
        parser.error("--drive requiere --mcu-port (no se detectó ESP32/S3 automáticamente)")

    for name in ("speed", "close_speed", "backup_speed", "brake_reverse_speed", "brake_forward_speed", "turn_speed"):
        v = getattr(args, name)
        if not 0 <= v <= 255:
            parser.error(f"--{name.replace('_','-')} debe estar entre 0 y 255")
    for name in ("servo_center", "turn_angle_left", "turn_angle_right"):
        v = getattr(args, name)
        if not 0 <= v <= 180:
            parser.error(f"--{name.replace('_','-')} debe estar entre 0 y 180")
    if args.cycle_count < 1:
        parser.error("--cycle-count debe ser >= 1")
    if not 1 <= args.initial_search_cycles <= 3:
        parser.error("--initial-search-cycles debe estar entre 1 y 3")
    if not 1 <= args.later_search_cycles <= 2:
        parser.error("--later-search-cycles debe estar entre 1 y 2")
    if args.cycle_repeat_count < 1:
        parser.error("--cycle-repeat-count debe ser >= 1")
    if args.maneuver_limit < 0:
        parser.error("--maneuver-limit debe ser >= 0")
    if args.close_mm <= args.threshold_mm:
        parser.error("--close-mm debe ser mayor que --threshold-mm")

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
    latest_full_scan: list[ScanNode] = []
    sector_map: list[list[float]] = [[] for _ in range(12)]
    maneuvers_done = 0
    awaiting_clear = False
    first_turn_dir: int | None = None

    def drain_lidar(duration_s: float) -> None:
        """Mantiene drenado el buffer del LiDAR durante maniobras temporizadas."""
        end = time.monotonic() + max(0.0, duration_s)
        while time.monotonic() < end:
            try:
                if lidar._serial is not None:
                    raw = lidar._serial.read(512)
                    if raw:
                        lidar.mark_stream_activity()
            except Exception:
                pass
            time.sleep(0.02)

    def hold_motion(angle: int, speed: int, seconds: float) -> None:
        if args.drive and controller is not None:
            controller.set(angle, speed)
        drain_lidar(seconds)

    def sample_front_clearance(duration_s: float) -> float | None:
        """Lee datos recientes del LiDAR durante un giro corto y devuelve el frente."""
        end = time.monotonic() + duration_s
        while time.monotonic() < end:
            try:
                if lidar._serial is not None:
                    raw = lidar._serial.read(512)
                    if raw:
                        lidar.mark_stream_activity()
                        lidar._buffer.extend(raw)
            except Exception:
                pass
            time.sleep(0.02)

        nodes: list[ScanNode] = []
        while len(lidar._buffer) >= 5:
            node = decode_measurement_node(bytes(lidar._buffer[:5]))
            if node is not None:
                nodes.append(node)
                del lidar._buffer[:5]
            else:
                del lidar._buffer[0]
        return front_distance_mm(nodes, args.lidar_front_deg, half_width_deg=args.front_half_width)

    def analyze_full_360() -> list[ScanNode]:
        """Detiene el robot y recoge una vuelta completa para decidir izquierda/derecha."""
        if args.drive and controller is not None:
            controller.set(args.servo_center, 0)
        if lidar._serial is not None:
            lidar._serial.reset_input_buffer()
            lidar._buffer.clear()

        current_revolution: list[ScanNode] = []
        completed_nodes: list[ScanNode] = []
        started_revolution = False
        completed_revolutions = 0
        end = time.monotonic() + args.analysis_seconds

        while time.monotonic() < end:
            try:
                if lidar._serial is not None:
                    raw = lidar._serial.read(512)
                    if raw:
                        lidar.mark_stream_activity()
                        lidar._buffer.extend(raw)
            except Exception:
                pass

            while len(lidar._buffer) >= 5:
                node = decode_measurement_node(bytes(lidar._buffer[:5]))
                if node is None:
                    del lidar._buffer[0]
                    continue
                del lidar._buffer[:5]

                if node.starts_revolution:
                    if started_revolution:
                        completed_nodes.extend(current_revolution)
                        completed_revolutions += 1
                        if completed_revolutions >= args.analysis_revolutions:
                            print(f"  análisis listo: {completed_revolutions} vueltas completas")
                            return completed_nodes
                        current_revolution = []
                    else:
                        started_revolution = True
                        current_revolution = []
                    continue

                if started_revolution and node.distance_mm > 0:
                    current_revolution.append(node)

            time.sleep(0.02)

        print(f"  análisis terminó por tiempo: {completed_revolutions} vueltas completas")
        return completed_nodes

    def do_obstacle_maneuver(scan: list[ScanNode], full_scan: list[ScanNode], maneuver_number: int) -> str:
        nonlocal first_turn_dir
        print(f"    freno activo reversa {args.brake_reverse_seconds:.2f}s @ {args.brake_reverse_speed}")
        hold_motion(args.servo_center, -args.brake_reverse_speed, args.brake_reverse_seconds)
        print(f"  análisis 360° detenido: {args.analysis_revolutions} vueltas completas")
        analysis_scan = analyze_full_360()

        despeje_s = args.backup_seconds if maneuver_number == 1 else args.later_backup_seconds
        tipo_retroceso = "INICIO" if maneuver_number == 1 else "SIGUIENTE OBSTÁCULO"
        print(f"    retroceso despeje [{tipo_retroceso}] {despeje_s:.2f}s @ {args.backup_speed}")
        hold_motion(args.servo_center, -args.backup_speed, despeje_s)
        print(f"    freno avance {args.brake_forward_seconds:.2f}s @ {args.brake_forward_speed}")
        hold_motion(args.servo_center, args.brake_forward_speed, args.brake_forward_seconds)
        hold_motion(args.servo_center, 0, 0.2)

        # Solo se comparan los lados físicos alrededor del frente del carrito.
        # 270° relativo = izquierda; 90° relativo = derecha.
        left_clear, left_samples = directional_clearance_mm(
            analysis_scan, args.lidar_front_deg, 270.0, half_width_deg=35.0,
        )
        right_clear, right_samples = directional_clearance_mm(
            analysis_scan, args.lidar_front_deg, 90.0, half_width_deg=35.0,
        )
        print(
            f"  sectores: IZQ(lateral)=muestras {left_samples}, "
            f"DER(lateral)=muestras {right_samples}"
        )
        lc = left_clear
        rc = right_clear

        if lc is not None and rc is not None:
            print(f"  comparacion física: IZQ(lateral)= {lc:.0f}mm DER(lateral)= {rc:.0f}mm")
            if first_turn_dir is not None:
                turn_dir = first_turn_dir
            elif lc > rc:
                turn_dir = 0  # IZQUIERDA = servo 10°
            else:
                turn_dir = 1  # DERECHA = servo 80°
        elif lc is not None:
            turn_dir = 0
        elif rc is not None:
            turn_dir = 1
        else:
            turn_dir = 0

        if first_turn_dir is None:
            first_turn_dir = turn_dir
            print(f"  primer lado fijado para toda la ejecución: {'IZQ' if turn_dir == 0 else 'DER'}")

        turn_angle = args.turn_angle_left if turn_dir == 0 else args.turn_angle_right
        side_name = "IZQ" if turn_dir == 0 else "DER"
        ltxt = f"{left_clear:.0f}mm" if left_clear is not None else "--"
        rtxt = f"{right_clear:.0f}mm" if right_clear is not None else "--"
        print(
            f"OBSTACULO -> lado {side_name} (servo {turn_angle}°) "
            f"clear izq={ltxt} der={rtxt}"
        )

        # Repite la preparación y la tanda completa de giros.
        # Mantiene el mapa para diagnostico, pero no lo usa para decidir el lado.

        for repeat in range(1, args.cycle_repeat_count + 1):
            print(f"  tanda {repeat}/{args.cycle_repeat_count}: {args.cycle_count} ciclos")

            cycle = 0
            search_cycle_limit = args.initial_search_cycles if maneuver_number == 1 else args.later_search_cycles
            while True:
                cycle += 1
                if maneuver_number == 1:
                    giro_s = args.cycle_turn_extra_seconds if cycle == 2 else args.cycle_turn_seconds
                else:
                    giro_s = max(0.1, args.cycle_turn_seconds - 0.20) if cycle == 2 else args.cycle_turn_seconds
                print(f"    búsqueda {cycle}: giro {side_name} {turn_angle}° adelante {giro_s:.2f}s @ {args.turn_speed}")
                hold_motion(turn_angle, args.turn_speed, giro_s)
                hold_motion(args.servo_center, 0, args.cycle_pause_seconds)
                hold_motion(args.servo_center, -args.backup_speed, args.cycle_reverse_seconds)
                hold_motion(args.servo_center, 0, args.cycle_end_pause_seconds)

                front_clear = sample_front_clearance(0.35)
                if front_clear is not None:
                    print(f"    frente después del giro: {front_clear:.0f}mm")
                if front_clear is not None and front_clear > args.threshold_mm:
                    print(f"    espacio disponible enfrente ({front_clear:.0f}mm); termina búsqueda")
                    break
                if cycle >= search_cycle_limit:
                    print(f"    búsqueda completó {search_cycle_limit} giros; escaneo lateral preciso")
                    if args.drive and controller is not None:
                        controller.set(args.servo_center, 0)
                    post_scan = analyze_full_360()
                    post_left, post_left_samples = directional_clearance_mm(
                        post_scan, args.lidar_front_deg, 270.0, half_width_deg=35.0,
                    )
                    post_right, post_right_samples = directional_clearance_mm(
                        post_scan, args.lidar_front_deg, 90.0, half_width_deg=35.0,
                    )
                    print(
                        f"    escaneo post-giro: IZQ={post_left_samples} muestras "
                        f"{(''+f'{post_left:.0f}mm') if post_left is not None else '--'}, "
                        f"DER={post_right_samples} muestras "
                        f"{(''+f'{post_right:.0f}mm') if post_right is not None else '--'}"
                    )
                    if first_turn_dir is not None:
                        side_name = "IZQ" if first_turn_dir == 0 else "DER"
                        turn_angle = args.turn_angle_left if first_turn_dir == 0 else args.turn_angle_right
                        print(f"    lado permanente después del giro: {side_name} (servo {turn_angle}°)")
                    break

        hold_motion(args.servo_center, 0, 0.1)
        return side_name

    try:
        if args.drive:
            if not args.mcu_port:
                parser.error("--drive requiere --mcu-port")
            controller = MotorController(args.mcu_port, baud=9600, refresh=args.refresh)
            controller.start()
            controller.set(args.servo_center, 0)
            print(f"ESP32/S3 conectado en {args.mcu_port}")

        if args.drive:
            print(
                f"DRIVE: vel {args.speed}, frena/reversa a {args.threshold_mm:.0f}mm "
                f"(freno activo rev {args.brake_reverse_speed} x {args.brake_reverse_seconds:.2f}s), "
                f"maniobras={'sin límite' if args.maneuver_limit == 0 else args.maneuver_limit}, "
                f"ciclos por detección={args.cycle_count}, "
                f"giro IZQ={args.turn_angle_left}° DER={args.turn_angle_right}°"
            )
        else:
            print("DIAGNÓSTICO: no se enviarán comandos de movimiento. Usa --drive para habilitar.")

        lidar.start()
        print(f"LiDAR leyendo {args.lidar_port} @ 460800 (frente LiDAR={args.lidar_front_deg}°)")

        for scan, is_new_rev in lidar.iter_scans_fast(yield_every_nodes=1):
            update_sector_map(sector_map, scan, args.lidar_front_deg)
            if is_new_rev:
                scan_count += 1
                latest_full_scan = scan
            front = front_distance_mm(scan, args.lidar_front_deg, half_width_deg=args.front_half_width)
            desired_angle = args.servo_center
            maneuver_triggered = False
            sequence_complete = False

            if front is None:
                if args.drive and controller is not None:
                    controller.set(args.servo_center, 0)
                desired_speed = 0
                action = "SIN_LECTURA_FRENTE -> STOP HASTA RECUPERAR DATOS"
            elif awaiting_clear and front <= args.threshold_mm:
                desired_speed = args.close_speed
                desired_angle = args.turn_angle_left if first_turn_dir == 0 else args.turn_angle_right
                action = f"FRENTE BLOQUEADO ({front:.0f}mm) -> AVANZAR LENTO HACIA LADO FIJO {desired_angle}°"
            elif awaiting_clear:
                awaiting_clear = False
                desired_speed = args.close_speed
                action = f"FRENTE DESPEJADO ({front:.0f}mm) -> AVANZAR LENTO vel {desired_speed}"
            elif front <= args.threshold_mm:
                if args.drive and controller is not None:
                    controller.set(args.servo_center, 0)
                next_maneuver_number = maneuvers_done + 1
                side = do_obstacle_maneuver(scan, latest_full_scan, next_maneuver_number)
                maneuvers_done += 1
                awaiting_clear = True
                maneuver_triggered = True
                sequence_complete = args.maneuver_limit > 0 and maneuvers_done >= args.maneuver_limit
                count_label = f"{maneuvers_done}/{args.maneuver_limit}" if args.maneuver_limit > 0 else f"#{maneuvers_done}"
                action = f"MANIOBRA_COMPLETA {count_label} lado {side}"
                # después de la maniobra, continuar con siguiente lectura
                desired_speed = 0
                desired_angle = args.servo_center
                if args.drive and controller is not None:
                    controller.set(args.servo_center, 0)
                print("Maniobra terminada; reanudando escaneo LiDAR.")
                if sequence_complete:
                    print(f"Secuencia de {args.maneuver_limit} maniobras completada; deteniendo robot.")
            elif front <= args.close_mm:
                span = max(args.close_mm - args.threshold_mm, 1.0)
                ratio = (front - args.threshold_mm) / span
                ratio = max(0.0, min(1.0, ratio))
                desired_speed = args.close_speed + int(round(ratio * (args.speed - args.close_speed)))
                action = f"ACERCANDO frente={front:.0f}mm -> vel incremental {desired_speed}"
            else:
                desired_speed = args.speed
                action = f"AVANZAR frente={front:.0f}mm vel {desired_speed}"

            if args.drive and controller is not None and not maneuver_triggered:
                controller.set(desired_angle, desired_speed)

            should_log = (is_new_rev and scan_count % args.log_every == 0) or "MANIOBRA_COMPLETA" in action
            if should_log:
                ftxt = "--" if front is None else f"{front:.0f}mm"
                panorama = f" {format_sector_map(sector_map)}" if is_new_rev else ""
                print(f"scan={scan_count} frente={ftxt} accion={action}{panorama}")
            if sequence_complete:
                break

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
