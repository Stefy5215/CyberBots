#!/usr/bin/env python3
"""Diagnóstico 360° del RPLIDAR sin enviar comandos al robot."""

import argparse
import time

from lidar_c1 import RPLidarC1, ScanNode


def relative_angle(lidar_angle: float, lidar_front_deg: float) -> float:
    return (lidar_angle - lidar_front_deg) % 360.0


def sector_name(relative_deg: float) -> str:
    if relative_deg < 22.5 or relative_deg >= 337.5:
        return "N (frente)"
    if relative_deg < 67.5:
        return "NE"
    if relative_deg < 112.5:
        return "E (derecha)"
    if relative_deg < 157.5:
        return "SE"
    if relative_deg < 202.5:
        return "S (atrás)"
    if relative_deg < 247.5:
        return "SO"
    if relative_deg < 292.5:
        return "O (izquierda)"
    if relative_deg < 337.5:
        return "NO"
    return "N (frente)"


def sector_distances(scan: list[ScanNode], lidar_front_deg: float) -> dict[str, list[float]]:
    sectors: dict[str, list[float]] = {
        "N (frente)": [], "NE": [], "E (derecha)": [], "SE": [],
        "S (atrás)": [], "SO": [], "O (izquierda)": [], "NO": [],
    }
    for node in scan:
        if node.quality <= 0 or not (50.0 <= node.distance_mm <= 8000.0):
            continue
        rel = relative_angle(node.angle_deg, lidar_front_deg)
        name = sector_name(rel)
        sectors[name].append(node.distance_mm)
    return sectors


def clearance(distances: list[float]) -> float | None:
    if len(distances) < 3:
        return None
    ordered = sorted(distances)
    return ordered[int((len(ordered) - 1) * 0.75)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lidar-port", required=True)
    parser.add_argument("--lidar-front-deg", type=float, default=270.0)
    parser.add_argument("--seconds", type=float, default=8.0)
    args = parser.parse_args()

    lidar = RPLidarC1(args.lidar_port)
    lidar.start()
    print("Diagnóstico sin motores. Presiona Ctrl+C para salir.")

    try:
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            for scan, is_new_rev in lidar.iter_scans_fast(yield_every_nodes=12):
                if not is_new_rev:
                    continue

                sectors = sector_distances(scan, args.lidar_front_deg)
                clearances = {name: clearance(values) for name, values in sectors.items()}

                left = clearances["O (izquierda)"]
                right = clearances["E (derecha)"]
                winner = "DERECHA" if right is not None and (left is None or right > left) else "IZQUIERDA"

                print("\n--- Vista 360° ---")
                for name in ("N (frente)", "NE", "E (derecha)", "SE", "S (atrás)", "SO", "O (izquierda)", "NO"):
                    value = clearances[name]
                    text = "--" if value is None else f"{value:.0f} mm"
                    print(f"{name:12} {text}")

                left_text = "--" if left is None else f"{left:.0f} mm"
                right_text = "--" if right is None else f"{right:.0f} mm"
                print(f"COMPARACIÓN lados: izquierda={left_text} derecha={right_text} -> {winner}")
                time.sleep(1.0)
                break
    except KeyboardInterrupt:
        print("\nDiagnóstico detenido.")
    finally:
        lidar.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
