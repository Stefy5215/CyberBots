# Raspberry Pi 5 + RPLIDAR C1 + ESP32 classic + L298N

This guide is for a classic dual-core ESP32 (ESP32-WROOM/DevKit with CH340 or CP210x USB bridge), one rear DC motor, one steering servo, L298N, buck converter, and a power switch for the buck. The Arduino is not part of this wiring.

## ESP32 pins

| ESP32 GPIO | Connect to |
| --- | --- |
| GPIO 25 | L298N `ENA` (remove ENA jumper; add 10 kΩ pulldown to GND) |
| GPIO 26 | L298N `IN1` |
| GPIO 27 | L298N `IN2` |
| GPIO 18 | Servo signal |
| GND | Common ground |

These are GPIO numbers, not physical header pin numbers. Leave L298N `ENB`, `IN3`, `IN4`, `OUT3`, and `OUT4` unused for one motor. Do not connect any button to an ESP32 GPIO; the switch in this build powers the buck.

## Complete wiring

| From | To | Notes |
| --- | --- | --- |
| ESP32 GPIO 25 | L298N ENA | Remove jumper; 10 kΩ ENA-to-GND pulldown |
| ESP32 GPIO 26 | L298N IN1 | Direction |
| ESP32 GPIO 27 | L298N IN2 | Direction |
| ESP32 GPIO 18 | Servo signal | Servo starts only on serial command |
| Motor | L298N OUT1 and OUT2 | Rear drive motor |
| Motor battery + | L298N VS/12V | Use voltage suitable for the motor and L298N |
| Motor battery − | L298N GND | Motor-current return goes directly to driver |
| Battery-pack + | Buck switch input | Your switch is in series with buck input positive |
| Buck switch output | Buck IN+ | Switch powers the buck only |
| Battery-pack − | Buck IN− | Common reference |
| Buck OUT+ | Servo V+ | Adjust with multimeter before connecting; use servo rated voltage |
| Buck OUT− | Servo GND and common ground | Join to L298N GND and ESP32 GND |
| ESP32 GND | Common ground point | Do not route motor current through this lead |
| ESP32 USB | Raspberry Pi USB | Serial control |
| RPLIDAR C1 USB | Raspberry Pi USB | Independent USB device |

With two 7.4 V batteries in series, the pack is 14.8 V nominal and 16.8 V fully charged. Do not feed 16.8 V directly to a 12 V motor. Verify the motor rating and the L298N module's `5V-EN` jumper: do not tie its regulator output to the buck or ESP32 3V3. Never connect 5 V to an ESP32 GPIO.

All grounds must share a reference: pack negative, L298N GND, buck IN−/OUT−, servo GND, and ESP32 GND. Use a star/common point near the driver; keep high motor current out of the thin ESP32 ground wire. The buck switch does not turn off the L298N motor supply. Use a separate motor-rated latching cutoff in series with motor-battery positive for an emergency stop.

## Firmware and test

Select `ESP32 Dev Module`, enable `USB CDC On Boot`, and select `Flash Mode: DIO`. Load `esp32_l298n/esp32_l298n.ino`. The firmware accepts `S<angle>,M<speed>` at 9600 baud, leaves ENA at zero at boot, attaches servo PWM only on an explicit angle change, and stops the motor if serial commands stop for one second.

The LiDAR and ESP32 connect separately to the Pi by USB. Find their current names with:

```bash
ls -l /dev/serial/by-id
```

Before a motor test, lift the drive wheel and make sure the physical motor-battery cutoff is reachable. The test script requires an explicit confirmation:

```bash
python3 test_motor_esp32.py /dev/ttyUSB0 --confirm-wheels-lifted
```

The manually invoked test commands servo angle 55, applies PWM 200 for 8 seconds, and then commands stop. It requires `--confirm-wheels-lifted`; it does not run automatically at ESP32 boot. Replace `/dev/ttyUSB0` with the ESP32's actual USB-serial port. The C1 LiDAR typically uses the other USB serial port at 460800 baud.

For LiDAR navigation, defaults are servo center 55 degrees, steering angles 25/85 degrees, and max PWM 200. Motion still requires `--drive`. Find stable device paths with `ls -l /dev/serial/by-id` and substitute those paths below:

```bash
python3 robot_c3_lidar.py --lidar-port "$LIDAR_PORT" --mcu-port "$ESP_PORT" --drive
```