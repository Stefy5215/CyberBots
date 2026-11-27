# Alcance: Robot LiDAR

Este repositorio contiene únicamente el robot Elegoo controlado con Raspberry Pi 5 y LiDAR C1.

No contiene el proyecto del invernadero automático, su cámara ni su aplicación Android. Esos recursos viven por separado en `/home/sergio/arduino_ws`.

La carpeta `server/` de este repositorio corresponde solo a la telemetría del robot por puerto serie y WebSocket.

## Bitácora - 27 de noviembre de 2026

- Ajuste del robot autónomo con evasión por LiDAR y retroceso activo.
- Frenado inverso con PWM 255 al detectar obstáculos, con velocidades normales y cercanas configurables.
- Desaceleración incremental entre 1200 mm y 550 mm; freno frontal a 550 mm.
- Análisis 360° detenido para elegir izquierda o derecha, con 10° y 80° como ángulos de giro.
- Fijado el lado elegido en la primera detección para mantenerlo durante toda la ejecución.
- Primera búsqueda limitada a hasta 3 giros; búsquedas posteriores limitadas a 2 giros.
- Agregado el script `lidar_diagnostic_cardinal.py` para observar N, S, E y O sin mover los motores.
- Se corrigió el `UnboundLocalError` al fijar el primer lado de giro y se revisaron los temporizadores de reversa.
- Validación realizada con `py_compile` sobre el programa principal y el lector LiDAR.
