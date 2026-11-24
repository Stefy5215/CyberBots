# CyberBots – WRO Future Engineers 2026

CyberBots is a Guatemalan robotics team developing an autonomous vehicle for **WRO Future Engineers 2026**. This repository documents our prototype work: design iterations, electronics, firmware, LiDAR sensing, navigation experiments, and the process of testing and improving the robot.

## Team

- **Sergio Andrea Carrera Canel** (16) – programming, electronics, and project documentation.
- **Jason Arturo Carrera Garrido** (17) – design and visual/project development.

## Project overview

Our goal is to build a robot that can perceive its surroundings and react autonomously on a competition-style track. Over time we have explored different hardware combinations; the current working software prototype in this repository focuses on:

- **Raspberry Pi 5** for LiDAR processing and high-level control
- **Classic ESP32** (DevKit/WROOM, USB serial) for real-time motor and servo control
- **L298N** motor driver with 1 rear DC motor
- **1 steering servo**
- **Slamtec RPLIDAR C1** for distance/obstacle sensing
- **2× 7.4 V batteries in series** (14.8 V nominal / 16.8 V max) for the drive system, with a buck converter providing ~5.1 V for the Raspberry Pi (USB-C power feed) and servo supply

> Scope: this repository covers the LiDAR robot prototype and its control/telemetry code. Other separate projects are maintained outside this repo.

## Repository highlights

| Path | Description |
| --- | --- |
| `esp32_l298n/esp32_l298n.ino` | ESP32 firmware: `S<angle>,M<speed>` serial protocol (9600 baud), safe boot, servo attach on command, and 1 s motor watchdog. |
| `test_motor_esp32.py` | Guarded motor/servo test (requires explicit confirmation, command refresh, and safe stop). |
| `lidar_c1.py` | RPLIDAR C1 scan descriptor/node parsing and serial reader. |
| `robot_c3_lidar.py` | Reactive LiDAR navigation (diagnostic mode or `--drive`) sending commands to the ESP32. |
| `tests/` | Unit tests for LiDAR decoding and navigation decisions. |
| `GUIA_ESP32_L298N_LIDAR.md`, `ESQUEMA_CONEXIONES.txt` | Wiring and setup notes. |

## ESP32 pin mapping (`esp32_l298n/esp32_l298n.ino`)

| ESP32 GPIO | Connects to |
| --- | --- |
| GPIO 25 | L298N `ENA` (remove ENA jumper; 10 kΩ pulldown to GND recommended) |
| GPIO 26 | L298N `IN1` |
| GPIO 27 | L298N `IN2` |
| GPIO 18 | Servo signal |
| GND | Common ground |

- Serial: **9600 baud**, command format `S<angle>,M<speed>\n` (`angle` 0–180, `speed` -255..255).
- Safety: motor off at boot, servo PWM attached only when angle changes, and motor stops if commands stop for ~1 s.

## Quick wiring summary (current working setup)

1. **Batteries:** 2× 7.4 V in series → 14.8 V nominal / 16.8 V max.
2. **Power:** battery positive (`VBAT+`) split to **L298N `VS/12V`** and **buck `IN+`**; battery negative to common GND. *(Never connect battery voltage to the L298N `5V` pin.)*
3. **Buck (~5.1 V):** powers Raspberry Pi 5 via USB-C (VBUS/GND) and servo V+; buck GND to common GND.
4. **L298N:** `VS` from `VBAT+`, `GND` common, `OUT1/OUT2` to DC motor, control from ESP32 GPIO25/26/27.
5. **Servo:** signal → GPIO18, V+ → regulated buck output, GND → common GND.
6. **USB data:** ESP32 ↔ Raspberry Pi (control), RPLIDAR C1 ↔ Raspberry Pi (scans).
7. **Common ground:** battery−, L298N, buck, servo, ESP32, and Raspberry Pi grounds tied together.

Check motor/driver voltage ratings (16.8 V fully charged) and L298N `5V-EN` jumper configuration for your module.

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ls -l /dev/serial/by-id
```

**Guarded motor test** (wheel lifted / power cut ready):

```bash
./.venv/bin/python test_motor_esp32.py /dev/serial/by-id/<esp32-port> --confirm-wheels-lifted
```

**LiDAR navigation** (diagnostic by default; add `--drive` to enable motion):

```bash
./.venv/bin/python robot_c3_lidar.py --lidar-port /dev/serial/by-id/<lidar-port> --mcu-port /dev/serial/by-id/<esp32-port> [--drive --max-speed 255]
```

**Tests:**

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## Work timeline

- **2026-10-31:** Built and tested initial RPLIDAR C1 protocol parsing/decoding and unit tests.
- **2026-11-20 to 2026-11-22:** Developed classic ESP32 + L298N firmware, guarded motor/servo test tooling, LiDAR navigation scripts, wiring notes, and setup documentation through iterative hardware testing.
- **2026-11-22:** Verified serial command acknowledgements and timed motor tests (with watchdog refresh), confirmed LiDAR scans, and tuned control/test parameters.
- **2026-11-23:** Consolidated documentation and integrated the robot codebase and project notes into the repository.

## Safety

- Never auto-run motors on boot; keep a physical power cutoff accessible.
- Test with wheels lifted or in a clear, supervised area.
- Verify polarities, buck output (~5.1 V), grounds, and voltage ratings before powering the system.
