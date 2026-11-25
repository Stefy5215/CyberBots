#!/usr/bin/env python3
"""Minimal serial reader for the RPLIDAR C1 standard scan protocol."""

from __future__ import annotations

from dataclasses import dataclass
import struct
import time


LIDAR_BAUDRATE = 460800
SYNC_BYTES = b"\xA5\x5A"
SCAN_COMMAND = b"\xA5\x20"
STOP_COMMAND = b"\xA5\x25"
STANDARD_NODE_SIZE = 5


@dataclass(frozen=True)
class ScanNode:
    quality: int
    angle_deg: float
    distance_mm: float
    starts_revolution: bool


def decode_measurement_node(raw: bytes) -> ScanNode | None:
    """Decode one 5-byte standard node; reject malformed sync/check bits."""
    if len(raw) != STANDARD_NODE_SIZE:
        return None

    sync_quality = raw[0]
    sync_flags = sync_quality & 0x03
    if sync_flags not in (0x01, 0x02):
        return None

    angle_check = struct.unpack_from("<H", raw, 1)[0]
    if not angle_check & 0x01:
        return None

    angle_deg = (angle_check >> 1) / 64.0
    if not 0.0 <= angle_deg <= 360.0:
        return None

    distance_q2 = struct.unpack_from("<H", raw, 3)[0]
    return ScanNode(
        quality=sync_quality >> 2,
        angle_deg=angle_deg,
        distance_mm=distance_q2 / 4.0,
        starts_revolution=bool(sync_quality & 0x01),
    )


def is_standard_scan_descriptor(raw: bytes) -> bool:
    if len(raw) != 7 or raw[:2] != SYNC_BYTES:
        return False
    size_mode = struct.unpack_from("<I", raw, 2)[0]
    payload_size = size_mode & 0x3FFFFFFF
    send_mode = size_mode >> 30
    response_type = raw[6]
    return payload_size == STANDARD_NODE_SIZE and send_mode == 1 and response_type == 0x81


class RPLidarC1:
    def __init__(self, port: str, baudrate: int = LIDAR_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._buffer = bytearray()
        self._running = False

    def start(self) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("Falta pyserial: instala requirements.txt") from exc

        self._serial = serial.Serial(self.port, self.baudrate, timeout=0.1, write_timeout=1)
        self._serial.dtr = True
        self._serial.write(STOP_COMMAND)
        time.sleep(0.1)
        self._serial.reset_input_buffer()
        self._serial.dtr = False
        time.sleep(0.25)
        self._serial.write(SCAN_COMMAND)
        self._read_scan_descriptor(timeout=3.0)
        self._running = True

    def _read_scan_descriptor(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._buffer.extend(self._serial.read(256))
            while len(self._buffer) >= 7:
                offset = self._buffer.find(SYNC_BYTES)
                if offset < 0:
                    del self._buffer[:-1]
                    break
                if offset:
                    del self._buffer[:offset]
                candidate = bytes(self._buffer[:7])
                if is_standard_scan_descriptor(candidate):
                    del self._buffer[:7]
                    return
                del self._buffer[0]
        raise TimeoutError(
            f"El LiDAR no entregó el descriptor C1 en {self.port} a {self.baudrate} baudios. "
            "Verifica alimentación USB, puerto, cable y que no haya otro proceso usando el puerto."
        )

    def iter_scans(self):
        current_scan: list[ScanNode] = []
        last_node_time = time.monotonic()

        while self._running:
            self._buffer.extend(self._serial.read(512))
            while len(self._buffer) >= STANDARD_NODE_SIZE:
                node = decode_measurement_node(bytes(self._buffer[:STANDARD_NODE_SIZE]))
                if node is None:
                    del self._buffer[0]
                    continue

                del self._buffer[:STANDARD_NODE_SIZE]
                last_node_time = time.monotonic()
                if node.starts_revolution and current_scan:
                    yield current_scan
                    current_scan = []
                if node.distance_mm > 0:
                    current_scan.append(node)

            if time.monotonic() - last_node_time > 3.0:
                raise TimeoutError("El LiDAR dejó de enviar nodos de medición por USB.")

    def iter_scans_fast(self, yield_every_nodes: int = 12):
        """Yield scan snapshots frecuentemente (cada N nodos válidos) para reacciones de baja latencia.

        Yields (scan_nodes, is_new_revolution). scan_nodes es una copia del escaneo actual.
        """
        current_scan: list[ScanNode] = []
        last_node_time = time.monotonic()
        nodes_since_yield = 0

        while self._running:
            self._buffer.extend(self._serial.read(512))
            while len(self._buffer) >= STANDARD_NODE_SIZE:
                node = decode_measurement_node(bytes(self._buffer[:STANDARD_NODE_SIZE]))
                if node is None:
                    del self._buffer[0]
                    continue

                del self._buffer[:STANDARD_NODE_SIZE]
                last_node_time = time.monotonic()
                new_rev = bool(node.starts_revolution and current_scan)
                if new_rev:
                    # yield revolución completa
                    yield list(current_scan), True
                    current_scan = []
                    nodes_since_yield = 0

                if node.distance_mm > 0:
                    current_scan.append(node)
                nodes_since_yield += 1

                if nodes_since_yield >= yield_every_nodes and current_scan:
                    yield list(current_scan), False
                    nodes_since_yield = 0

            if time.monotonic() - last_node_time > 3.0:
                raise TimeoutError("El LiDAR dejó de enviar nodos de medición por USB.")

    def stop(self) -> None:
        self._running = False
        if self._serial is not None:
            try:
                self._serial.write(STOP_COMMAND)
                self._serial.dtr = True
            finally:
                self._serial.close()
                self._serial = None
