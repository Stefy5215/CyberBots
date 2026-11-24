# Raspberry Pi 5 + RPLIDAR C1 + ESP32-C3 + TB6612FNG

Esta ruta nueva conserva los sketches Arduino/Elegoo existentes. La Raspberry Pi lee el LiDAR C1 por USB y manda `S<angulo>,M<velocidad>` a la ESP32-C3; la C3 maneja el servo y el canal A del TB6612.

## Pines y cableado

| ESP32-C3 SuperMini | TB6612FNG / componente |
| --- | --- |
| GPIO 3 | STBY; añade pull-down de 10 kΩ a GND |
| GPIO 4 | PWMA |
| GPIO 1 | AIN1 |
| GPIO 5 | AIN2 |
| GPIO 0 | Señal del servo |
| 3V3 | VCC del TB6612 |
| GND | GND común |

Conecta el motor a `A01/A02` y su batería a `VM` y GND del TB6612. El servo necesita una fuente regulada de 5–6 V independiente; une su GND con el GND común. No alimentes el servo desde la C3. No conectes `VM` a 3V3, 5V ni a la Pi.

`STBY` es una habilitación separada: LOW pone el driver en espera; HIGH permite que `AIN1/AIN2` y `PWMA` controlen el motor. El firmware deja STBY en LOW al arrancar y lo baja si no recibe comandos durante 1 segundo.

Al arrancar, el firmware no adjunta PWM al servo: encender la batería por sí sola no debe moverlo. El servo solo recibe señal cuando llega una orden serial cuyo ángulo difiere del ángulo lógico actual. Una orden recta como `S90,M100` puede probar el motor sin activar el servo; `S90,M0` mantiene la parada.

## Cargar el firmware C3

En Arduino IDE selecciona `ESP32C3 Dev Module`, habilita `USB CDC On Boot` y selecciona `Flash Mode: DIO`, instala el core Espressif ESP32 y abre `esp32_c3_tb6612/esp32_c3_tb6612.ino`. En esta C3, DIO permitió arrancar estable; el modo anterior no llegaba al sketch. El servo y PWMA usan LEDC nativo del core, sin biblioteca de servo adicional. El puerto USB de la C3 puede aparecer como `/dev/ttyACM*` o `/dev/ttyUSB*`, según la revisión de la placa.

El protocolo serial queda a 9600 baudios y acepta `S90,M0` para centro/parada. Las velocidades positivas son avance y negativas reversa; invierte los cables del motor si el sentido físico queda al revés.

## Probar el LiDAR y la navegación

Instala `pyserial` usando el entorno Python del proyecto. Identifica los puertos con:

```bash
ls -l /dev/serial/by-id
ls /dev/ttyUSB* /dev/ttyACM*
```

Primero prueba solo el escaneo, sin movimiento:

```bash
python3 robot_c3_lidar.py --lidar-port /dev/ttyUSB0
```

Con la C3 conectada, puede hacerse diagnóstico mostrando decisiones pero manteniendo el motor parado:

```bash
python3 robot_c3_lidar.py --lidar-port /dev/ttyUSB0 --mcu-port /dev/ttyACM0
```

Solo después de verificar lecturas, cableado y sentido del motor, autoriza movimiento a baja velocidad, con las ruedas levantadas:

```bash
python3 robot_c3_lidar.py --lidar-port /dev/ttyUSB0 --mcu-port /dev/ttyACM0 --drive --max-speed 75
```

Los nombres de puerto son ejemplos: confirma los tuyos. `Ctrl+C` manda parada. El modo sin `--drive` nunca autoriza PWM distinto de cero.

La navegación usa la mediana del 20 % más cercano de cada sector para evitar reaccionar a una lectura aislada: reduce velocidad ante obstáculos cercanos, gira hacia el lado con más espacio y se detiene si falta la lectura frontal. No intenta contar tres vueltas: sin encoder, marca de pista u otro sensor de vueltas, el conteo anterior basado en cambios de servo no demuestra vueltas reales.

## LiDAR C1: baudios y alimentación USB

El C1 se abre a **460800 baudios**. El lector espera el descriptor estándar de siete bytes y luego decodifica nodos de cinco bytes; no trata cada medición como un paquete con cabecera propia. Cierra otros programas que puedan tener abierto el mismo puerto.

En una Raspberry Pi 5, si el LiDAR no aparece o se desconecta por límite de corriente USB, la configuración que mencionaste puede probarse en la propia Pi. Haz copia antes de editar:

```bash
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.bak
sudo nano /boot/firmware/config.txt
```

Añade `usb_max_current_enable=1` dentro de la sección `[all]`, guarda y reinicia:

```bash
sudo reboot
```

Comprueba el valor con `vcgencmd get_config usb_max_current_enable`. Usa una fuente USB-C de 5 V/5 A adecuada para la Pi 5. Este ajuste aumenta el límite disponible para periféricos; **no repara un corto, cable defectuoso ni una alarma real de sobrecorriente**. Si la alarma persiste con un solo dispositivo USB y cable probado, desconéctalo y revisa hardware antes de insistir.

## Verificación local

Desde la raíz del repo:

```bash
python3 -m unittest discover -s tests -v
```