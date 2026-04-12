# GUÍA RÁPIDA - Robot Esquiva Obstáculos con LiDAR C1

## 📁 Archivos Principales

| Archivo | Descripción |
|---------|-------------|
| `esquiva_obstaculos.py` | **PRINCIPAL** - Código del robot en Raspberry Pi |
| `control_arduino.ino` | Código para cargar en Arduino |
| `config_robot.py` | Configuración personalizable |
| `control_manual.py` | Control manual para pruebas |
| `prueba_conexiones.py` | Verificar conexiones |
| `requirements.txt` | Dependencias Python |
| `setup.sh` | Script de instalación automática |

---

## 🚀 Guía de Instalación Rápida

### EN RASPBERRY PI (Paso 1 - 2 minutos)

```bash
# 1. Copiar archivos a Raspberry Pi
# (Usa SCP o copia manualmente desde Desktop)

cd ~/proyecto-robot

# 2. Hacer ejecutable el script
chmod +x setup.sh

# 3. Ejecutar instalación automática
bash setup.sh

# 4. REINICIAR SESIÓN (importante!)
exit
# Reconectar SSH o reiniciar
```

### EN ARDUINO IDE (Paso 2 - 1 minuto)

1. Descargar Arduino IDE: https://www.arduino.cc/en/software
2. Abrir `control_arduino.ino`
3. Seleccionar: Tools → Board → Arduino Uno
4. Seleccionar: Tools → Port → /dev/ttyACM0
5. Click en **Upload** (Ctrl+U)

---

## 🔍 Verificar Conexiones

```bash
# En Raspberry Pi, ejecutar prueba:
python3 prueba_conexiones.py
```

**Salida esperada:**
```
✓ Arduino conectado
✓ LiDAR conectado
✓ ¡Todo está listo!
```

---

## ▶️ EJECUTAR EL ROBOT

```bash
# Opción 1: Ejecución automática (recomendado)
python3 esquiva_obstaculos.py

# Opción 2: Controlar manualmente (para pruebas)
python3 control_manual.py
```

---

## 🎮 Comandos Control Manual

| Tecla | Acción |
|-------|--------|
| `f` | Adelante recto |
| `l` | Giro izquierda fuerte |
| `r` | Giro derecha fuerte |
| `L` | Giro izquierda suave |
| `R` | Giro derecha suave |
| `t` | Marcha lenta |
| `T` | Marcha rápida |
| `s` | Parar |
| `q` | Salir |

---

## ⚙️ Personalizar Comportamiento

Editar `config_robot.py`:

```python
FRONT_THRESHOLD = 50      # ↓ Valor = más sensible
SIDE_THRESHOLD = 40       # ↓ Valor = esquiva más lejos
DEFAULT_SPEED = 150       # ↑ Valor = más rápido (0-255)
```

---

## 🔧 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| "Permission denied" | `sudo usermod -a -G dialout $USER` + reiniciar |
| Arduino no conecta | `ls /dev/ttyACM*` - verificar puerto |
| LiDAR no detecta | `ls /dev/ttyUSB*` - verificar puerto |
| Motor no gira | Verificar conexiones L298N y batería 12V |
| Servo no se mueve | Verificar PWM pin 9 y alimentación 5V |

---

## 📊 Monitoreo

Los logs del robot muestran:
- Distancias detectadas (Frontal, Izquierda, Derecha)
- Ángulo servo actual
- Velocidad motor actual
- Comandos enviados

---

## 🛑 Parar Emergencia

Presionar **Ctrl+C** en terminal para detener inmediatamente.

---

## 📱 Estructura de Datos (Raspberry Pi ↔ Arduino)

**Comando enviado:**
```
S<ángulo>,M<velocidad>\n
```

**Ejemplos:**
- `S90,M150\n` → Recto a velocidad 150
- `S135,M100\n` → Giro izquierda, velocidad 100
- `S45,M200\n` → Giro derecha, velocidad 200
- `S90,M0\n` → Detener

---

## 📸 Lo que deberías ver al ejecutar:

```
Connecting to LiDAR on /dev/ttyUSB0...
✓ LiDAR connected successfully
Connecting to Arduino on /dev/ttyACM0...
✓ Arduino connected successfully
Starting obstacle avoidance robot...

Obstacles - Front: 120.5cm, Left: 150.0cm, Right: 155.0cm
Command sent: Servo=90°, Motor=150
Obstacles - Front: 45.2cm, Left: 120.0cm, Right: 110.0cm
Command sent: Servo=135°, Motor=100
...
```

---

## 🎯 Siguientes Pasos

1. ✓ Instalación completada
2. ✓ Hardware conectado
3. ✓ Prueba de conexiones exitosa
4. ▶️ **Ejecutar el robot**
5. Calibración y ajustes según necesidad

---

**¡Disfruta tu robot esquivador de obstáculos! 🤖**
