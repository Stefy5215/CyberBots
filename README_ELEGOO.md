# Robot Esquiva Obstáculos con Elegoo Smart Car y LiDAR C1

## Descripción del Proyecto

Robot autónomo basado en **Elegoo Smart Car** que utiliza **LiDAR C1** para detectar obstáculos y esquivarlos automáticamente en una pista. La Raspberry Pi 5 controla la lógica de detección mientras que la placa Elegoo maneja los motores y servo.

## Hardware

- **Raspberry Pi 5** (Raspberry Pi OS)
- **Elegoo Smart Car Kit** (con 2 motores DC y drivers integrados)
- **LiDAR C1** (RPLIDAR C1)
- **Servo Motor** (control de dirección)
- **Batería 12V** (para motores)

## Pines Elegoo Utilizados

| Componente | Pin | Función |
|-----------|-----|---------|
| Motor PWM A | 5 | Control velocidad motor A |
| Motor PWM B | 6 | Control velocidad motor B |
| Motor Dir A | 7 | Dirección motor A |
| Motor Dir B | 8 | Dirección motor B |
| Motor STBY | 3 | Standby motores |
| Servo | 10 | Control del servo |
| LED | 13 | Indicador de estado |

## Instalación Rápida

### 1. Preparar Raspberry Pi

```bash
cd ~/Desktop/proyecto\ 18012026
chmod +x setup_elegoo.sh
bash setup_elegoo.sh
# Reiniciar sesión
```

### 2. Cargar Código en Elegoo

1. Abrir Arduino IDE
2. Crear nuevo proyecto con los siguientes archivos:
   - `esquiva_lidar_elegoo.ino`
   - `DeviceDriverSet.h`
   - `DeviceDriverSet.cpp`
3. Seleccionar: Tools → Board → Arduino Uno
4. Cargar el código

### 3. Ejecutar Robot en Raspberry Pi

```bash
cd ~/Desktop/proyecto\ 18012026
python3 robot_esquiva_lidar.py
```

## Protocolo de Comunicación

**Formato**: `S<ángulo>,M<velocidad>\n`

| Comando | Ejemplo | Descripción |
|---------|---------|-------------|
| Servo | S90 | Ángulo 0-180° |
| Motor | M70 | Velocidad 0-255 |
| Completo | S90,M70 | Servo 90°, Motor velocidad 70 |

## Velocidades Recomendadas

| Velocidad | Valor | Uso |
|-----------|-------|-----|
| SLOW | 20-40 | Giros, áreas estrechas |
| NORMAL | 70 | Velocidad de crucero |
| FAST | 120+ | Espacios abiertos |
| STOP | 0 | Detención |

## Ángulos Servo

- **90°**: Recto (adelante)
- **45°**: Derecha máxima
- **135°**: Izquierda máxima
- **60-120°**: Giros suaves

## Umbrales de Detección (Ajustables)

```python
FRONT_THRESHOLD = 50      # cm - Distancia mínima frontal
SIDE_THRESHOLD = 35       # cm - Distancia mínima lateral
ANGLE_RANGE = 30          # grados - Rango de visión frontal
```

## Lógica de Esquiva

1. **Obstáculo adelante** → Gira hacia el lado más despejado
2. **Obstáculo izquierda** → Gira derecha
3. **Obstáculo derecha** → Gira izquierda
4. **Camino libre** → Avanza recto

## Troubleshooting

### Arduino no se conecta
```bash
ls /dev/ttyACM*  # Verificar puerto
# Si no aparece, reconecta USB
```

### LiDAR no funciona
```bash
ls /dev/ttyUSB*  # Verificar puerto
# Editar en robot_esquiva_lidar.py:
LIDAR_PORT = '/dev/ttyUSB0'  # Cambiar número si necesario
```

### Motores no se mueven
- Verificar conexiones L298N
- Verificar batería 12V
- Revisar en Arduino IDE el serial monitor

### Servo no responde
- Verificar pin 10
- Verificar alimentación 5V
- Centr calibración en 90°

## Archivos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `robot_esquiva_lidar.py` | Lógica principal Raspberry Pi |
| `esquiva_lidar_elegoo.ino` | Firmware para Elegoo |
| `DeviceDriverSet.h/cpp` | Drivers de motores y servo |
| `setup_elegoo.sh` | Script de instalación |

## Parámetros Personalizables

Editar `robot_esquiva_lidar.py`:

```python
FRONT_THRESHOLD = 50      # Detectar obstáculos más/menos lejos
SIDE_THRESHOLD = 35       # Sensibilidad lateral
MOTOR_NORMAL = 70         # Velocidad de crucero (0-255)
SERVO_CENTER = 90         # Centro del servo
```

## Control Manual (Opcional)

Si deseas probar componentes individualmente:

```bash
# Necesitarías crear un script de prueba similar a control_manual.py
python3 << 'PYTHON'
import serial
import time

arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)

# Adelante
arduino.write("S90,M70\n".encode())
time.sleep(2)

# Parar
arduino.write("S90,M0\n".encode())
arduino.close()
PYTHON
```

## Notas Importantes

- El watchdog de Elegoo detiene motores si no recibe comandos por 5 segundos
- Servo centra automáticamente al reiniciar
- LiDAR C1 tiene alcance efectivo de ~12 metros
- Mejor rendimiento en superficies lisas

## Siguiente Fase

Para mejorar el proyecto:
- Añadir obstáculos dinámicos
- Implementar mapeo con ROS2
- Calibración automática de servo
- Sistemas de evitación más complejos (A*, RRT, etc.)

---

**Versión**: 1.0 - Enero 2026
**Compatible**: Raspberry Pi 5 + Elegoo Smart Car + LiDAR C1
