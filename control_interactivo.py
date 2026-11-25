#!/usr/bin/env python3
import argparse
import glob
import threading
import time

import serial


def autodetect_port():
    patterns = [
        "/dev/serial/by-id/*Espressif*",
        "/dev/serial/by-id/*USB_JTAG*",
        "/dev/serial/by-id/*1a86*USB_Serial*",
        "/dev/serial/by-id/*1a86*",
        "/dev/serial/by-id/*CP210*",
    ]
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[0]
    for pat in ("/dev/ttyACM*", "/dev/ttyUSB*"):
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[0]
    return "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def read_response(ser):
    time.sleep(0.12)
    data = ser.read(ser.in_waiting or 256)
    if not data:
        return ""
    return data.decode(errors="ignore").strip()


def is_routine_ok(text, angle, speed):
    if not text:
        return True
    expected = f"OK S{angle} M{speed}"
    # puede venir con saltos de línea/cr; comparamos líneas
    for line in [ln.strip() for ln in text.replace("\r", "\n").split("\n") if ln.strip()]:
        if line != expected:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Control interactivo de servo (ángulo) y motor (velocidad) para ESP32."
    )
    parser.add_argument("--port", default=autodetect_port(), help="Puerto serie (auto-detect por defecto).")
    parser.add_argument("--baud", type=int, default=9600, help="Baudrate (default: 9600).")
    parser.add_argument("--angle", type=int, default=45, help="Ángulo inicial del servo 0-180 (default: 45).")
    parser.add_argument("--speed", type=int, default=0, help="Velocidad inicial del motor -255..255 (default: 0).")
    parser.add_argument("--refresh", type=float, default=0.4, help="Segundos entre reenvíos para evitar watchdog (default: 0.4).")
    parser.add_argument("--verbose", action="store_true", help="Muestra cada respuesta OK del refresco (puede ensuciar la entrada).")
    args = parser.parse_args()

    state = {"angle": clamp(args.angle, 0, 180), "speed": clamp(args.speed, -255, 255)}
    lock = threading.Lock()
    ser_lock = threading.Lock()
    stop_event = threading.Event()
    last_resp = {"text": ""}

    def send_cmd(ser, angle, speed, show=False):
        cmd = f"S{angle},M{speed}\n"
        with ser_lock:
            ser.write(cmd.encode())
            ser.flush()
            resp = read_response(ser)
        if resp:
            last_resp["text"] = resp
            important = (args.verbose or show or ("ERR" in resp) or ("STOP" in resp) or (not is_routine_ok(resp, angle, speed)))
            if important:
                print(f"< {resp}")
        return resp

    def sender_loop(ser):
        while not stop_event.is_set():
            with lock:
                angle, speed = state["angle"], state["speed"]
            try:
                send_cmd(ser, angle, speed, show=False)
            except Exception as e:
                msg = f"ERR serial: {e}"
                last_resp["text"] = msg
                print(f"< {msg}")
                stop_event.set()
                break
            stop_event.wait(args.refresh)

    print(f"Puerto: {args.port} @ {args.baud}")
    try:
        with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
            time.sleep(2.0)  # reset al abrir puerto
            with ser_lock:
                boot = ser.read_all().decode(errors="ignore").strip()
            if boot:
                print(boot)

            # estado inicial (mostrar respuesta)
            with lock:
                a, s = state["angle"], state["speed"]
            send_cmd(ser, a, s, show=True)

            t = threading.Thread(target=sender_loop, args=(ser,), daemon=True)
            t.start()

            print("Comandos:")
            print("  adelante <vel>         motor adelante 0-255   ej: adelante 150")
            print("  atras/retroceso <vel>  motor atrás 0-255      ej: atras 150")
            print("  izquierda <angulo>     servo 0-180            ej: izquierda 30")
            print("  derecha <angulo>       servo 0-180            ej: derecha 60")
            print("  centro                 servo al centro (45°)")
            print("  s <angulo>             solo servo             ej: s 60")
            print("  m <velocidad>          solo motor -255..255   ej: m -120")
            print("  <angulo> <velocidad>   servo+motor            ej: 45 150")
            print("  stop                   motor a 0")
            print("  status                 muestra estado")
            print("  q                      salir (detiene motor)")

            while not stop_event.is_set():
                try:
                    line = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not line:
                    continue
                low = line.lower()
                if low in {"q", "quit", "exit", "salir"}:
                    break
                if low == "stop":
                    with lock:
                        state["speed"] = 0
                        a, s = state["angle"], state["speed"]
                    print(f"Estado: angulo={a} velocidad={s}")
                    send_cmd(ser, a, s, show=True)
                    continue
                if low in {"status", "estado"}:
                    with lock:
                        a, s = state["angle"], state["speed"]
                    print(f"Estado: angulo={a} velocidad={s} | ultimo='{last_resp['text']}'")
                    continue
                if low in {"centro", "c", "center"}:
                    with lock:
                        state["angle"] = 45
                        a, s = state["angle"], state["speed"]
                    print(f"Estado: angulo={a} velocidad={s}")
                    send_cmd(ser, a, s, show=True)
                    continue

                parts = line.replace(",", " ").split()
                changed = False
                try:
                    cmd = parts[0].lower()
                    if len(parts) == 2 and cmd in {"s", "servo", "izquierda", "derecha", "giro", "g"}:
                        with lock:
                            state["angle"] = clamp(int(parts[1]), 0, 180)
                        changed = True
                    elif len(parts) == 2 and cmd in {"m", "motor"}:
                        with lock:
                            state["speed"] = clamp(int(parts[1]), -255, 255)
                        changed = True
                    elif len(parts) == 2 and cmd in {"adelante", "avanzar", "forward", "a"}:
                        with lock:
                            state["speed"] = clamp(int(parts[1]), 0, 255)
                        changed = True
                    elif len(parts) == 2 and cmd in {"atras", "retroceso", "reversa", "reverse", "r"}:
                        with lock:
                            state["speed"] = -clamp(int(parts[1]), 0, 255)
                        changed = True
                    elif len(parts) == 2 and cmd == "s":
                        # already handled above, keep for clarity
                        with lock:
                            state["angle"] = clamp(int(parts[1]), 0, 180)
                        changed = True
                    elif len(parts) == 2 and cmd == "m":
                        with lock:
                            state["speed"] = clamp(int(parts[1]), -255, 255)
                        changed = True
                    elif len(parts) == 2:
                        # intento: <angulo> <velocidad>
                        a = clamp(int(parts[0]), 0, 180)
                        sp = clamp(int(parts[1]), -255, 255)
                        with lock:
                            state["angle"], state["speed"] = a, sp
                        changed = True
                    elif len(parts) == 1:
                        # solo ángulo
                        with lock:
                            state["angle"] = clamp(int(parts[0]), 0, 180)
                        changed = True
                    else:
                        print("Formato no reconocido. Ej: adelante 150 | atras 150 | izquierda 30 | centro | stop | q")
                        continue
                except ValueError:
                    print("Valores inválidos. Usa enteros. Ej: adelante 150 | derecha 60")
                    continue

                if changed:
                    with lock:
                        a, s = state["angle"], state["speed"]
                    print(f"Estado: angulo={a} velocidad={s}")
                    send_cmd(ser, a, s, show=True)

            # detener motor al salir
            stop_event.set()
            try:
                with lock:
                    a = state["angle"]
                with ser_lock:
                    ser.write(f"S{a},M0\n".encode())
                    ser.flush()
                    time.sleep(0.2)
                    ser.read(ser.in_waiting or 256)
            except Exception:
                pass
            t.join(timeout=1.0)
    except serial.SerialException as e:
        print(f"Error abriendo puerto serie: {e}")
        return 1

    print("Salido (motor detenido).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
