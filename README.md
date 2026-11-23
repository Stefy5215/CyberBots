# CyberBots - LiDAR Obstacle Avoidance Robot

This repository contains the software, firmware, wiring notes, and tests for a Raspberry Pi 5 + RPLIDAR C1 robot prototype controlled by a classic ESP32 driving one rear DC motor (L298N) and one steering servo.

> Scope note: this repository is focused on the LiDAR robot. The `server/` folder (if present locally) is intended only for robot telemetry over serial/WebSocket and is separate from other unrelated projects.

## Current architecture

- **Host computer:** Raspberry Pi 5 (runs LiDAR reading, navigation logic, and sends commands over USB serial)
- **Microcontroller:** Classic ESP32 (ESP32-DevKit / ESP32-WROOM class, CH340/CP210x USB bridge)
- **Motor driver:** L298N (single DC motor channel used: ENA/IN1/IN2/OUT1/OUT2)
- **Actuators:** 1 rear DC motor + 1 steering servo
- **Sensor:** Slamtec RPLIDAR C1 (USB)
- **Power (current working setup reported):** 2x 7.4V batteries in series (14.8V nominal / 16.8V max), battery positive split to `L298N VS` and buck input, buck output ~5.1V feeding Raspberry Pi 5 via USB-C power cable and servo V+

## Repository structure

| Path | Purpose |
| --- | --- |
| `esp32_l298n/esp32_l298n.ino` | ESP32 firmware for L298N + servo control (`S<angle>,M<speed>` over serial, 9600 baud), safe boot, servo attach-on-command, and 1 s motor watchdog. |
| `test_motor_esp32.py` | Guarded manual motor/servo test script (requires explicit lifted-wheel confirmation, refreshes commands to keep watchdog alive, stops at end). |
| `lidar_c1.py` | Minimal RPLIDAR C1 standard scan protocol reader/decoder. |
| `robot_c3_lidar.py` | Reactive LiDAR navigation controller that sends steering/speed commands to ESP32; supports diagnostic mode and `--drive` mode. |
| `tests/test_lidar_c1.py` | Unit tests for LiDAR packet/descriptor/measurement decoding. |
| `tests/test_robot_c3_lidar.py` | Unit tests for scan-sector summarization and movement decisions. |
| `GUIA_ESP32_L298N_LIDAR.md` | Detailed wiring/firmware/test guide (Spanish, classic ESP32 + L298N). |
| `ESQUEMA_CONEXIONES.txt` | Connection notes/schematic text. |
| `README_SETUP.md` | Legacy/setup notes (mixed Arduino/ESP32 history). |
| `control_arduino/` | Arduino-side control sketch variants. |
| `robot_esquiva_lidar.py` | Earlier obstacle-avoidance control script variant. |

## ESP32 pin mapping (firmware: `esp32_l298n/esp32_l298n.ino`)

| ESP32 GPIO | Connection |
| --- | --- |
| GPIO 25 | L298N `ENA` (remove ENA jumper; recommended 10 kΩ pulldown to GND) |
| GPIO 26 | L298N `IN1` |
| GPIO 27 | L298N `IN2` |
| GPIO 18 | Servo signal |
| GND | Common ground |

- ESP32 GPIOs are **3.3 V logic**. Do not apply 5 V to ESP32 GPIO pins.
- Firmware serial: **9600 baud**, command format: `S<angle>,M<speed>\n` where angle is `0..180` and speed is `-255..255`.
- Safety behavior: motor output is zeroed at boot, servo PWM attaches only on explicit angle change, and motor stops if no command is received for ~1 second (`STOP watchdog`).

## Wiring summary (current working setup)

> Always verify polarities and voltages with a multimeter before powering devices. Battery positive must never be connected to the L298N `5V` pin.

1. **Batteries:** 2x 7.4V in series (`B1+` to `B2-`) => 14.8V nominal / 16.8V max pack.
2. **Power split:** pack positive (`VBAT+`) feeds **L298N `VS/12V`** and **buck `IN+`** in parallel; pack negative to common GND. (A switch/fuse on `VBAT+` is strongly recommended.)
3. **Buck (5.1V):** `OUT+` (~5.1V) to Raspberry Pi 5 USB-C power input (VBUS) and to servo V+; `OUT-` to USB-C GND and common GND.
4. **L298N:** `VS` from `VBAT+`, `GND` to common GND, `OUT1/OUT2` to DC motor, `ENA/IN1/IN2` from ESP32 GPIO25/26/27 (ENA jumper removed).
5. **Servo:** signal to ESP32 GPIO18, V+ from regulated buck output, GND to common GND.
6. **USB data:** ESP32 <-> Raspberry Pi (serial control), RPLIDAR C1 <-> Raspberry Pi (scan data).
7. **Common ground:** battery negative, L298N GND, buck GND, servo GND, ESP32 GND, and Raspberry Pi power ground must share a common reference.

See `GUIA_ESP32_L298N_LIDAR.md` and `ESQUEMA_CONEXIONES.txt` for more details.

## Setup (Raspberry Pi)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Find stable serial device paths:

```bash
ls -l /dev/serial/by-id
```

## Usage

### 1) Manual motor/servo test (guarded)

The test script requires explicit confirmation that the drive wheel is lifted and power can be cut quickly:

```bash
./.venv/bin/python test_motor_esp32.py /dev/serial/by-id/<esp32-port> --confirm-wheels-lifted
```

Current script parameters: servo angle `55`, motor PWM `255`, pulse duration `4.0 s` (with watchdog-refresh commands), followed by an acknowledged stop.

### 2) LiDAR C1 read/navigation (diagnostic or drive)

Diagnostic (no motor movement command):

```bash
./.venv/bin/python robot_c3_lidar.py --lidar-port /dev/serial/by-id/<lidar-port> --mcu-port /dev/serial/by-id/<esp32-port>
```

Drive mode (sends movement commands; supervise the robot):

```bash
./.venv/bin/python robot_c3_lidar.py --lidar-port /dev/serial/by-id/<lidar-port> --mcu-port /dev/serial/by-id/<esp32-port> --drive --max-speed 255
```

Default navigation parameters include servo center `55` (left `25`, right `85`) and front/side distance thresholds for slow/stop behavior. Tune cautiously for your chassis and LiDAR mounting orientation.

## Tests

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## Work timeline (development log)

Dates below reflect repository file history and development sessions recorded during this project iteration:

- **2026-10-31:** Implemented and validated initial RPLIDAR C1 protocol parsing/decoding (`lidar_c1.py`) and related unit tests.
- **2026-11-20 to 2026-11-22:** Developed and iterated classic ESP32 + L298N control firmware (`esp32_l298n/esp32_l298n.ino`), guarded motor/servo test tooling (`test_motor_esp32.py`), LiDAR-based navigation/controller updates (`robot_c3_lidar.py`), wiring/connection guides, and project documentation.
- **2026-11-22:** Verified ESP32 serial control acknowledgements and guarded motor pulse tests (including watchdog-refresh behavior), validated LiDAR scans, and updated navigation/test parameters.
- **2026-11-23:** Consolidated repository documentation in English (`README.md`), organized commits, and prepared/pushed updates to the project repository.

## Safety notes

- Do not run motor tests automatically on boot; keep a physical way to cut power.
- Lift the drive wheel or secure the robot before motor tests; supervise all `--drive` runs.
- Ensure correct L298N jumper/configuration for your module and supply voltage; never feed battery voltage into the L298N `5V` pin.
- 2x 7.4V in series can reach 16.8V when fully charged: confirm motor and driver voltage ratings.
- Use a common ground and adequate wire gauge for motor current paths.
