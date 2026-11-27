# CyberBots – WRO Future Engineers 2026

CyberBots is a Guatemalan robotics team developing an autonomous vehicle for **WRO Future Engineers 2026**. This repository documents our prototype work: design iterations, electronics, firmware, LiDAR sensing, navigation experiments, and the process of testing and improving the robot.

## Team

- **Sergio Andrea Carrera Canel** (16) – programming, electronics, and project documentation.
- **Jason Arturo Carrera Garrido** (17) – design and visual/project development.

## Project overview

Our goal is to build a robot that can perceive its surroundings and react autonomously on a competition-style track. Over time we have explored different hardware combinations; the current working software prototype in this repository focuses on:

- **Raspberry Pi 5** for LiDAR processing and high-level control
- **ESP32-S3** (USB JTAG/serial, board identifier Espressif `303a:1001`) for real-time motor and servo control
- **L298N** motor driver with 1 rear DC motor
- **1 steering servo**
- **Slamtec RPLIDAR C1** for distance/obstacle sensing
- **4× 18650 Li-ion batteries in series** in one battery holder (nominal 14.4–14.8 V, approximately 16.8 V fully charged) for the drive system
- **Buck converter** providing ~5.1 V for the Raspberry Pi 5 through USB-C power and for the steering servo supply

> Scope: this repository covers the LiDAR robot prototype and its control/telemetry code. Other separate projects are maintained outside this repo.

## WRO Future Engineers 2026

In 2026 the official season theme is **“Robots Meet Culture.”** CyberBots uses the WRO Future Engineers **Self-Driving Cars** category to explore autonomous navigation, sensing, motion control, mechanical engineering, energy design, engineering trade-offs, and reproducible documentation.

The official category rules describe two time-attack challenges:

- **Open Challenge:** complete three laps on a field with randomly placed internal walls.
- **Obstacle Challenge:** complete three laps while respecting randomly placed red and green traffic signs. Red signs indicate keeping the vehicle on the right side of the lane; green signs indicate keeping it on the left side. The vehicle must not move the signs and, after completing the laps, find the parking lot and perform parallel parking.

The direction of travel, starting position, and field configuration are randomized before each round. Each round is limited to **3 minutes**. The parking-lot score depends on starting inside the parking area and on parking completely and parallel. The 2026 rules also include a national/international **surprise rule**, so teams must always check the document published by WRO and their National Organizer before a competition.

Official 2026 links:

- [WRO 2026 season page](https://wro-association.org/competition/2026-season/)
- [Future Engineers General & Game Rules](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.pdf)
- [2026 Surprise Rule](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Extra-Task.pdf)
- [WRO 2026 game mat](https://wro-association.org/wp-content/uploads/WRO-2026_FutureEngineers_Playfield.pdf)
- [Documentation rubric](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Documentation-Rubric.pdf)

> National competitions may adapt rules for local conditions. Official international rules and the explanations in the WRO Q&A take priority for international competition. Always confirm dimensions, signs, start/finish, surprise rules, and scoring with the current organizer's rules.

## Official vehicle constraints

According to the published 2026 Future Engineers rules:

- Maximum vehicle dimensions: **300 × 200 mm**, with maximum height of **300 mm**.
- Maximum vehicle weight: **1.5 kg**.
- Four wheels with one drive axle and one steering actuator.
- The vehicle must use rear-, front-, or all-wheel drive, and differential-wheel control is not allowed.
- No omnidirectional wheels, caster/spherical wheels, or electronic differential with one motor per side.
- The vehicle must run autonomously; radio, Wi-Fi, Bluetooth, remote control, and wired assistance are prohibited during rounds.
- The vehicle requires a start procedure that is independent of a computer or remote control.
- The team must submit engineering documentation in English for the international final.

These values are the official rules used as design targets. The actual competition chassis must be checked with a measuring cube/ruler during the venue's check time before every round.

## Current prototype

### Mechanical configuration

- Elegoo-style rear-wheel robot chassis.
- One rear DC motor through an L298N motor driver.
- One steering servo for left/right direction.
- Servo-centered angle is currently tuned around `45°` in software; side turns use `10°` left and `80°` right in the current tuning.
- The LiDAR is mounted to provide forward and side clearance measurements.
- The physical orientation must be calibrated: the LiDAR's front angle is currently configured as `270°` relative to its reported coordinate system.

### Sensing and perception

The current obstacle prototype uses the RPLIDAR C1 over USB at `460800` baud. The software:

- Decodes standard C1 scan nodes and filters malformed or low-quality samples.
- Computes a front distance using a configurable frontal sector around the LiDAR front angle.
- Computes lateral clearance for left and right sectors.
- Builds 360° cardinal diagnostics for test and calibration.
- Updates front distance quickly while advancing, and performs a longer stopped analysis before a turn.
- Uses the front distance to start deceleration and active braking before executing a reverse/turn maneuver.

The navigation code is designed for iterative hardware tuning. It keeps the high-speed command refresh separate from LiDAR parsing so the ESP32-S3 watchdog continues receiving motion commands during slow sensor sections.

### Control architecture

```mermaid
flowchart LR
    P[Physical field / walls / traffic signs] --> L[RPLIDAR C1]
    L -->|460800 baud| R[Raspberry Pi 5]
    R -->|Python scan decoding| C[Front and side clearance calculation]
    C -->|S(angle),M(speed) at 9600 baud| E[ESP32-S3]
    E -->|PWM / direction| M[L298N motor driver]
    M --> D[Rear DC motor]
    E --> S[Steering servo]
    R -->|No wireless control| P
```

### Software behavior

The main safety and navigation flow is:

1. Advance and scan without sending a command if no valid front reading is available.
2. Increase or reduce motor PWM as front clearance decreases.
3. At the braking threshold, stop forward motion and send a short active-brake reverse command.
4. Reverse for the configured maneuver clearance time.
5. Apply a short forward brake to stop the reverse motion.
6. Analyze left/right clearance and lock the first chosen direction for the execution as the side-turn policy.
7. Make up to 3 searches in the first maneuver and up to 2 searches in later maneuver sequences.
8. Resume advance only when the updated front reading is clear.

The exact timing and PWM values are defaults and can be overridden by command-line arguments. Physical testing remains the final source of truth because battery voltage, tire grip, floor friction, servo geometry, and L298N electrical behavior affect distance and braking time.

## Repository highlights

| Path | Description |
| --- | --- |
| `esp32_l298n/esp32_l298n.ino` | ESP32-S3 firmware: `S<angle>,M<speed>` serial protocol (9600 baud), safe boot, servo attach on command, and 1 s motor watchdog. |
| `test_motor_esp32.py` | Guarded motor/servo test (requires explicit confirmation, command refresh, and safe stop). |
| `lidar_c1.py` | RPLIDAR C1 scan descriptor/node parsing and serial reader. |
| `lidar_diagnostic_cardinal.py` | 360° cardinal diagnostic; reports N, NE, E/right, SE, S, SO, W/left, and NW without motor commands. |
| `avanzar_obstaculo_retroceder.py` | Autonomous obstacle prototype with incremental speed, reverse braking, LiDAR 360° analysis, and turn cycles. |
| `robot_c3_lidar.py` | Reactive LiDAR navigation (diagnostic mode or `--drive`) sending commands to the ESP32-S3. |
| `control_interactivo.py` | Keyboard-oriented interactive motor and servo control. |
| `test_motor_esp32.py` | Guarded motor/servo test with explicit wheel-lift confirmation and watchdog refresh. |
| `tests/` | Unit tests for LiDAR decoding and navigation decisions. |
| `GUIA_ESP32_L298N_LIDAR.md`, `ESQUEMA_CONEXIONES.txt` | Wiring and setup notes. |

## ESP32-S3 pin mapping (`esp32_l298n/esp32_l298n.ino`)

| ESP32-S3 GPIO | Connects to |
| --- | --- |
| GPIO 5 | L298N `ENA` (remove ENA jumper) |
| GPIO 6 | L298N `IN1` |
| GPIO 7 | L298N `IN2` |
| GPIO 4 | Steering servo signal |
| GND | Common ground |

- Serial: **9600 baud**, command format `S<angle>,M<speed>\n` (`angle` 0–180, `speed` -255..255).
- Board: ESP32-S3 with native USB/JTAG serial enabled by Arduino Core 3.x.
- USB detection: Espressif VID/PID `303a:1001`; in Linux this is commonly `/dev/ttyACM0` or a stable `/dev/serial/by-id/...` path.
- Safety: motor off at boot, servo PWM attached to GPIO 4 by the firmware, and motor stops if serial commands stop for ~1 s.

## Quick wiring summary (current working setup)

1. **Battery pack:** 4× 18650 Li-ion cells in series (4S), nominal 14.4–14.8 V and approximately 16.8 V fully charged. Use a holder with proper series wiring and one motor-rated emergency cutoff.
2. **Power:** battery positive (`VBAT+`) split to **L298N `VS/12V`** and **buck `IN+`**; battery negative to common GND. *(Never connect battery voltage directly to the ESP32, servo, or the L298N `5V` pin.)*
3. **Buck (~5.1 V):** powers Raspberry Pi 5 via USB-C (VBUS/GND) and the servo V+; buck GND goes to common GND.
4. **L298N:** `VS` from `VBAT+`, `GND` common, `OUT1/OUT2` to the rear DC motor, control from ESP32-S3 GPIO5/6/7.
5. **Servo:** signal → GPIO4, V+ → regulated buck output, GND → common GND.
6. **USB data:** ESP32-S3 ↔ Raspberry Pi (control), RPLIDAR C1 ↔ Raspberry Pi (scans).
7. **Common ground:** battery−, L298N, buck, servo, ESP32-S3, and Raspberry Pi grounds tied together.

> Safety: verify the exact voltage rating of every motor and accessory, battery balance/protection, buck output with a meter, and L298N `5V-EN` jumper configuration before energizing the system. Keep a physical battery cutoff available during testing.

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

**Obstacle avoidance prototype with active braking and LiDAR 360° side analysis:**

```bash
./.venv/bin/python avanzar_obstaculo_retroceder.py \
  --lidar-port /dev/serial/by-id/<lidar-port> \
  --mcu-port /dev/serial/by-id/<esp32-s3-port> \
  --drive
```

**LiDAR-only cardinal diagnostic (does not open or command the ESP32-S3):**

```bash
./.venv/bin/python lidar_diagnostic_cardinal.py \
  --lidar-port /dev/serial/by-id/<lidar-port> \
  --lidar-front-deg 270 \
  --seconds 30
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
- **2026-11-24:** Migrated the active controller to ESP32-S3, remapped motor/servo pins to GPIO5/6/7/4, and validated USB serial and RGB bring-up.
- **2026-11-25 to 2026-11-27:** Tuned interactive control, 360° LiDAR sector analysis, obstacle braking, reverse clearance, turn cycles, and cardinal diagnostics with real hardware tests.

## Testing and tuning workflow

Use this sequence to diagnose or test hardware changes safely:

1. Compile Python files and run unit tests before connecting motors.
2. Use `lidar_diagnostic_cardinal.py` to verify cardinal sectors and side identification without motion.
3. Run the LiDAR obstacle script without `--drive` to observe front distance, clearance, and decisions only.
4. Lift all driven wheels and enable `--drive` while a motor-rated emergency cutoff remains accessible.
5. Test low PWM values first, then test braking, reverse, servo angle, and complete turns on the floor.
6. Re-run the same test on the final battery charge range and record actual results.
7. Update the engineering log after every major tuning change.

### Suggested test log fields

- Battery voltage at start and end.
- Test surface and wheel grip.
- Front threshold and close-speed thresholds.
- Actual stop distance.
- Left/right clearance values selected.
- Servo angles used.
- Reverse and brake-forward durations.
- Number of scans and reaction time.
- LiDAR timeout/recovery behavior.
- Whether the robot moved signs or touched walls.

## Engineering documentation status

The repository is intended to support WRO Future Engineers documentation evidence:

- **Mechanical design:** chassis, steering geometry, motor mounting, servo linkage, LiDAR mounting, battery holder, wiring, and mass.
- **Power architecture:** 4S 18650 pack, buck conversion, L298N, motor/servo voltage distribution, ground topology, and fuse/cutoff.
- **Sensor architecture:** RPLIDAR C1 placement, angle calibration, measurement limits, filtering, and sector selection.
- **Software architecture:** LiDAR decoder, serial protocol, state flow, braking, reverse, turn cycle, watchdog, and diagnostic tools.
- **Engineering decisions:** trade-offs between speed, braking, reverse, reaction latency, and physical stability.
- **Iteration evidence:** commit history, dated tuning logs, test videos, measurements, and documented failures.
- **Reproducibility:** commands, serial port discovery, firmware flashing, Python setup, tests, and wiring.

The documentation rubric emphasizes reproducible repository structure, commit history, clear engineering rationale, risk analysis, testing/tuning evidence, CAD or wiring files, and a README that allows another team to rebuild and run the system.

## Safety

- Never auto-run motors on boot; keep a physical power cutoff accessible.
- Test with wheels lifted or in a clear, supervised area.
- Use the LiDAR-only diagnostic script before enabling `--drive`.
- Verify polarities, buck output (~5.1 V), grounds, and voltage ratings before powering the system.
- Protect the 4S Li-ion pack with an appropriate holder, balance/charge solution, fuse or breaker, and the real voltage limits of the hardware.
- Never route high motor current through ESP32-S3 ground leads or weak USB data cables.
- Keep a spare STOP command ready and stop testing immediately on unexpected reverse, servo, or USB behavior.

## Official sources and limits

- The WRO 2026 rules are authoritative only in the form published for the national/international event being attended.
- The README summarizes verified public 2026 category information, but local rules may differ.
- This repository is the engineering prototype, not a substitute for the official game rules or judge instructions.
- Always verify the official track setup, traffic-sign placement, parking configuration, surprise rule, and scoring with the judge and current rule package before competition.
