#!/usr/bin/env python3
"""
Configuración de parámetros del robot
Ajusta estos valores según tus necesidades
"""

# ========================
# CONFIGURACIÓN DE PUERTOS
# ========================
LIDAR_PORT = '/dev/ttyUSB0'           # Puerto del LiDAR
ARDUINO_PORT = '/dev/ttyACM0'         # Puerto del Arduino
ARDUINO_BAUDRATE = 9600               # Velocidad serial Arduino
LIDAR_BAUDRATE = 115200               # Velocidad serial LiDAR

# ========================
# PARÁMETROS DEL SERVO
# ========================
SERVO_CENTER = 90          # Posición central (grados)
SERVO_LEFT = 135           # Ángulo máximo izquierda
SERVO_RIGHT = 45           # Ángulo máximo derecha
SERVO_TURN_ANGLE = 30      # Ángulo para giros suaves

# ========================
# PARÁMETROS DEL MOTOR
# ========================
MOTOR_MIN = 0              # Velocidad mínima (PWM)
MOTOR_MAX = 255            # Velocidad máxima (PWM)
DEFAULT_SPEED = 150        # Velocidad por defecto
MOTOR_SLOW = 100           # Velocidad lenta (giros)
MOTOR_FAST = 200           # Velocidad rápida

# ========================
# UMBRALES DE DISTANCIA
# ========================
FRONT_THRESHOLD = 50       # Distancia frontal para detectar obstáculo (cm)
SIDE_THRESHOLD = 40        # Distancia lateral para detectar obstáculo (cm)
FRONT_CRITICAL = 30        # Distancia crítica (frena urgente)
SAFE_DISTANCE = 100        # Distancia segura para avanzar

# ========================
# RANGO DE ÁNGULOS
# ========================
ANGLE_RANGE = 30           # Rango de ángulos para zona frontal (±30°)
FRONT_START = 330          # Ángulo inicio zona frontal
FRONT_END = 30             # Ángulo fin zona frontal
LEFT_START = 70            # Ángulo inicio zona izquierda
LEFT_END = 110             # Ángulo fin zona izquierda
RIGHT_START = 250          # Ángulo inicio zona derecha
RIGHT_END = 290            # Ángulo fin zona derecha

# ========================
# PARÁMETROS DE TIEMPO
# ========================
LIDAR_SCAN_RATE = 50       # Hz (escaneos por segundo)
COMMAND_INTERVAL = 0.2     # Segundos entre comandos
EMERGENCY_TIMEOUT = 2.0    # Timeout para detener robot (segundos)

# ========================
# MODO DEBUG
# ========================
DEBUG = True               # Mostrar información de depuración
VERBOSE = False            # Mostrar todos los detalles
LOG_FILE = None            # None = sin archivo, o ruta para archivo de log

# ========================
# CONSTANTES INTERNAS
# ========================
MM_TO_CM = 10              # Conversión milímetros a centímetros
DEGREES_PER_ANGLE = 1      # Resolución angular LiDAR

class RobotConfig:
    """Clase para gestionar configuración del robot"""
    
    @staticmethod
    def get_servo_angle(direction):
        """
        Obtener ángulo del servo según dirección
        direction: 'CENTER', 'LEFT', 'RIGHT'
        """
        angles = {
            'CENTER': SERVO_CENTER,
            'LEFT': SERVO_LEFT,
            'RIGHT': SERVO_RIGHT,
            'SLIGHT_LEFT': SERVO_CENTER + SERVO_TURN_ANGLE,
            'SLIGHT_RIGHT': SERVO_CENTER - SERVO_TURN_ANGLE,
        }
        return angles.get(direction, SERVO_CENTER)
    
    @staticmethod
    def get_motor_speed(speed_level):
        """
        Obtener velocidad del motor
        speed_level: 'OFF', 'SLOW', 'NORMAL', 'FAST'
        """
        speeds = {
            'OFF': 0,
            'SLOW': MOTOR_SLOW,
            'NORMAL': DEFAULT_SPEED,
            'FAST': MOTOR_FAST,
        }
        return speeds.get(speed_level, 0)
    
    @staticmethod
    def is_front_obstacle(distance):
        """Detectar obstáculo frontal"""
        return distance < FRONT_THRESHOLD
    
    @staticmethod
    def is_front_critical(distance):
        """Detectar obstáculo crítico frontal"""
        return distance < FRONT_CRITICAL
    
    @staticmethod
    def is_side_obstacle(distance):
        """Detectar obstáculo lateral"""
        return distance < SIDE_THRESHOLD
    
    @staticmethod
    def is_safe(distance):
        """Verificar si la distancia es segura"""
        return distance >= SAFE_DISTANCE

# ========================
# PERFILES DE CONDUCCIÓN
# ========================
PROFILES = {
    'cautious': {
        'front_threshold': 80,
        'side_threshold': 60,
        'speed': 100,
    },
    'normal': {
        'front_threshold': 50,
        'side_threshold': 40,
        'speed': 150,
    },
    'aggressive': {
        'front_threshold': 30,
        'side_threshold': 25,
        'speed': 200,
    },
}

if __name__ == '__main__':
    print("Configuración del Robot - Obstacle Avoidance")
    print("=" * 50)
    print(f"Puerto LiDAR: {LIDAR_PORT}")
    print(f"Puerto Arduino: {ARDUINO_PORT}")
    print(f"Velocidad por defecto: {DEFAULT_SPEED}/255")
    print(f"Umbral frontal: {FRONT_THRESHOLD}cm")
    print(f"Umbral lateral: {SIDE_THRESHOLD}cm")
    print(f"Debug: {'Activo' if DEBUG else 'Desactivo'}")
