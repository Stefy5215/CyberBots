# Raspberry Pi 5 + RPLIDAR C1 + ESP32-C3 + L298N

La Raspberry Pi lee el LiDAR C1 y manda comandos seriales `S<angulo>,M<velocidad>` a la ESP32-C3. La C3 maneja el servo y el canal A del L298N. Esta guía corresponde al L298N; el firmware TB6612 está separado.

## Pines de la C3

| ESP32-C3 SuperMini | Conexión |
| --- | --- |
| GPIO 4 | `ENA` del L298N; quitar el jumper de ENA |
| GPIO 1 | `IN1` |
| GPIO 5 | `IN2` |
| GPIO 0 | Señal del servo |
| GND | Tierra común |

No se usa GPIO para el botón. El firmware recibe comandos por USB serial y detiene el motor si dejan de llegar comandos durante 1 segundo.

## L298N y motor

- Motor de tracción entre `OUT1` y `OUT2`.
- Positivo de la batería del motor a `12V`, `VS` o `VMS` del módulo, según su etiqueta.
- Negativo de esa batería a `GND` del L298N.
- `ENA` a GPIO 4, `IN1` a GPIO 1 e `IN2` a GPIO 5.
- Deja `ENB`, `IN3`, `IN4`, `OUT3` y `OUT4` sin conectar si usas solo un motor.
- Añade un pull-down de 10 kΩ entre `ENA` y GND para mantener el motor deshabilitado durante el arranque; quita el jumper de ENA.

Los módulos L298N varían en el regulador lógico y el jumper `5V-EN`. No adivines ese cableado: revisa la serigrafía de tu placa. Si tiene `5V-EN` y el regulador integrado acepta el voltaje de tu batería, sigue el diagrama del propio módulo; si el jumper está quitado, alimenta el pin lógico de 5 V como indique el módulo. **No conectes el 5 V del L298N al 3V3, 5V/VIN de la C3 ni al Raspberry Pi.** El 3.3 V de GPIO de la C3 va solo a las entradas `IN1/IN2/ENA`.

El L298N pierde más voltaje y se calienta más que un TB6612. Comprueba la corriente nominal/atascada del motor y usa disipador; corta la batería si el driver se calienta rápidamente.

## Servo, buck y tierras

- Ajusta el buck con multímetro a **5.0 V antes de conectar el servo**, salvo que la etiqueta del servo indique otra tensión.
- Servo: señal a GPIO 0, positivo a la salida regulada del buck y GND al negativo del buck.
- Negativo de batería, GND del L298N, GND del buck y GND de la C3 deben compartir referencia. Lleva la corriente alta del motor de vuelta al L298N/batería, no por el cable GND de la Pi.
- No alimentes servo ni motor desde la C3 o los pines USB de la Pi.
- Si tu botón conmuta la alimentación del buck, conecta batería `+` → botón → `IN+` del buck; batería `−` → `IN−` del buck. Eso solo enciende/apaga la salida del buck (por ejemplo, el servo), no corta la alimentación `VS` del L298N.
- Para cortar el motor, usa un interruptor enclavable dimensionado para la corriente del motor en serie con batería `+` hacia `VS` del L298N. No pases la corriente del motor por un botón pequeño no especificado para esa carga.

## Raspberry Pi y LiDAR

- Alimenta la Pi 5 por su USB-C con su fuente adecuada.
- LiDAR C1 por USB a la Pi; normalmente aparece como `/dev/ttyUSB*` (en esta instalación se identificó como CP2102N).
- ESP32-C3 por USB de datos a la Pi; aparece como `/dev/ttyACM*` (en esta instalación `/dev/ttyACM0`). No conectes otra fuente de 5 V a la C3 mientras comparte USB.
- Si reaparece el error del controlador USB de la Pi, detén la prueba y conecta los periféricos uno por uno. `usb_max_current_enable=1` no soluciona cortos ni un host USB que se cae.

## Cargar y probar

En Arduino IDE selecciona `ESP32C3 Dev Module`, habilita `USB CDC On Boot`, selecciona `Flash Mode: DIO` y carga `esp32_c3_l298n/esp32_c3_l298n.ino`. El servo usa LEDC nativo; no necesita una biblioteca de servo.

Primero confirma los puertos y ejecuta diagnóstico sin movimiento:

```bash
ls -l /dev/serial/by-id
python3 robot_c3_lidar.py --lidar-port /dev/ttyUSB0 --mcu-port /dev/ttyACM0
```

Para movimiento se requiere `--drive` y ruedas levantadas. El botón de alimentación del buck no arma el motor. Empieza con velocidad baja:

```bash
python3 robot_c3_lidar.py --lidar-port /dev/ttyUSB0 --mcu-port /dev/ttyACM0 --drive --max-speed 75
```

Los nombres de puerto son ejemplos: confirma los tuyos. Si el motor gira al revés, intercambia los cables del motor en `OUT1/OUT2` con la batería desconectada.