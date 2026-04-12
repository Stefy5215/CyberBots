# Obstacle Avoidance Robot - Raspberry Pi 5 Setup Guide

Este es un robot autónomo que esquiva obstáculos usando LiDAR C1, un servo motor para dirección y un motor de 12V para la propulsión. Se comunica con una Arduino para el control preciso de los actuadores.

## 📋 Hardware Requerido

- **Raspberry Pi 5** (con Raspberry Pi OS)
- **LiDAR C1** (RPLIDAR C1)
- **Arduino** (Uno, Nano, o compatible)
- **Servo Motor** (SG90 o similar)
- **Motor DC 12V** (con Driver L298N o similar)
- **Batería 12V** (para motor)
- **Batería 5V** (para Raspberry Pi y Arduino)
- **Cable USB-A a USB-B** (Raspberry Pi a Arduino)
- **Cable USB-A a Mini-B** (Raspberry Pi a LiDAR)

## 🔌 Conexiones

### Arduino - Motor DC
```
Arduino Pin 5  (PWM)      → Motor Speed (PWM pin del Driver)
Arduino Pin 7  (Digital)  → Motor Direction Pin 1
Arduino Pin 8  (Digital)  → Motor Direction Pin 2
Arduino GND    → Driver GND
```

### Arduino - Servo Motor
```
Arduino Pin 9  (PWM)      → Servo Signal
Arduino 5V     → Servo VCC
Arduino GND    → Servo GND
```

### Raspberry Pi - Arduino
```
USB Port (Raspberry Pi) → USB Port (Arduino)
Puerto serial: /dev/ttyACM0
Baudrate: 9600
```

### Raspberry Pi - LiDAR C1
```
USB Port (Raspberry Pi) → USB Mini-B (LiDAR)
Puerto serial: /dev/ttyUSB0
Baudrate: 115200
```

## 💻 Instalación en Raspberry Pi OS

### 1. Actualizar el sistema
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Instalar dependencias del sistema
```bash
sudo apt-get install python3-pip python3-dev -y
```

### 3. Dar permisos para acceso a puertos seriales
```bash
sudo usermod -a -G dialout $USER
# Desconectar sesión y volver a conectar para aplicar cambios
```

### 4. Clonar o descargar los archivos del proyecto
```bash
# Opción 1: Desde el repositorio
git clone https://github.com/ishaannk/obstacle-avoidance-using-LiDAR.git

# Opción 2: Usar los archivos del Desktop (si están ahí)
cd ~/Desktop
```

### 5. Instalar dependencias Python
```bash
# Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 6. Verificar instalación
```bash
# Probar que las librerías se instalaron correctamente
python3 -c "import rplidar, serial; print('✅ Librerías instaladas')"
```

## 🔧 Solución de Problemas con RPLIDAR C1

### Problema: "LiDAR no funciona" o "funciona a veces por USB"

**Causa principal:** Conflictos de librerías y configuración incorrecta

### ✅ Solución paso a paso:

1. **Verificar conexiones físicas:**
   ```bash
   # Ejecutar detector de puertos
   python3 detectar_puertos.py
   ```

2. **Probar RPLIDAR solo:**
   ```bash
   # Test básico del LiDAR
   python3 test_lidar.py
   ```

3. **Probar Arduino solo:**
   ```bash
   # Test de comunicación con Arduino
   python3 prueba_conexiones.py
   ```

4. **Ejecutar robot completo:**
   ```bash
   # Una vez que ambos tests pasan
   python3 esquiva_obstaculos.py
   ```

### Configuración correcta para RPLIDAR C1:
- **Puerto:** `/dev/ttyUSB0` (verificar con `ls /dev/ttyUSB*`)
- **Baudrate:** `115200` (NO 460800)
- **Librería:** `rplidar` (NO adafruit_rplidar o rplidar-sdk)
- **Alimentación:** Necesita 5V estable (no compartir con servo)

### Comandos de diagnóstico:
```bash
# Ver dispositivos USB conectados
lsusb

# Ver puertos seriales disponibles
ls /dev/tty*

# Verificar permisos de usuario
groups $USER

# Agregar permisos si faltan
sudo usermod -a -G dialout $USER
# Luego cerrar sesión y volver a abrir
```

## 🚀 Carga del código en Arduino

1. Instalar Arduino IDE en tu computadora:
   - Descargar desde: https://www.arduino.cc/en/software

2. Abrir el archivo `control_arduino.ino` en Arduino IDE

3. Seleccionar la placa:
   - Tools → Board → Arduino Uno (o tu modelo)

4. Seleccionar el puerto:
   - Tools → Port → /dev/ttyACM0

5. Cargar el código (Ctrl+U)

## ⚙️ Configuración Personalizada

Editar el archivo `esquiva_obstaculos.py` para ajustar:

```python
FRONT_THRESHOLD = 50    # Distancia para detectar obstáculo frontal (cm)
SIDE_THRESHOLD = 40     # Distancia para detectar obstáculos laterales (cm)
DEFAULT_SPEED = 150     # Velocidad de motor por defecto (0-255)
SERVO_CENTER = 90       # Ángulo central del servo (0-180)
```

## ▶️ Ejecución

### En Raspberry Pi:
```bash
python3 esquiva_obstaculos.py
```

### Prueba de conexión:
```bash
# Verificar Arduino
ls /dev/ttyACM*

# Verificar LiDAR
ls /dev/ttyUSB*
```

## 📊 Protocolo de Comunicación Raspberry Pi ↔ Arduino

**Formato de comando:**
```
S<ángulo>,M<velocidad>\n
```

**Ejemplos:**
- `S90,M150\n` - Servo a 90°, Motor a velocidad 150
- `S45,M200\n` - Servo a 45° (giro izquierda), Motor a velocidad 200
- `S135,M100\n` - Servo a 135° (giro derecha), Motor a velocidad 100

**Rangos de valores:**
- Servo: 0-180 grados
- Motor: 0-255 (PWM)
- 0 motor = parado
- 255 motor = velocidad máxima

## 🐛 Troubleshooting

### Problema: "Permission denied" al acceder a /dev/ttyACM0
**Solución:**
```bash
sudo usermod -a -G dialout $USER
# Reinicia la sesión
```

### Problema: LiDAR no se conecta
**Verificar:**
```bash
lsusb  # Ver dispositivos USB conectados
ls /dev/ttyUSB*  # Verificar puerto del LiDAR
```

### Problema: Arduino no responde
**Verificar:**
```bash
ls /dev/ttyACM*  # Verificar puerto Arduino
# Resetear Arduino desconectando y reconectando USB
```

### Problema: Motor o servo no funcionan
**Verificar:**
1. Conexiones de poder (12V para motor, 5V para Arduino)
2. Pins PWM correctos (5, 9)
3. Código Arduino cargado correctamente

## 📝 Notas Importantes

1. **Seguridad**: Usar guantes y protección al trabajar con el motor de 12V
2. **Calibración servo**: Asegurarse de que el servo esté centrado en 90°
3. **Rango LiDAR C1**: Detección hasta 12 metros (ajustar thresholds según necesidad)
4. **Consumo de batería**: Monitorear voltaje en tiempo de ejecución
5. **Ambiente**: Mejor rendimiento en superficies lisas y bien iluminadas

## 🔗 Recursos Útiles

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Arduino Official Documentation](https://docs.arduino.cc/)
- [LiDAR C1 Specifications](https://www.slamtec.com/products/rplidar/)
- [Repositorio Original](https://github.com/ishaannk/obstacle-avoidance-using-LiDAR.git)

## 📞 Contacto y Soporte

Para problemas o mejoras, consulta:
- Documentación original del proyecto
- Foro de Arduino: https://forum.arduino.cc/
- Comunidad Raspberry Pi: https://www.raspberrypi.org/community/

---
**Versión**: 1.0  
**Compatible con**: Raspberry Pi 5, Raspberry Pi OS  
**Fecha**: Enero 2026
