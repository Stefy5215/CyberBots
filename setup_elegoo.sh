#!/bin/bash
# Instalación automática para Raspberry Pi 5 + Elegoo + LiDAR C1

set -e

echo "=========================================="
echo "Setup - Robot Elegoo + LiDAR C1"
echo "=========================================="

# 1. Actualizar sistema
echo "[1/5] Actualizando sistema..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Instalar dependencias
echo "[2/5] Instalando dependencias..."
sudo apt-get install python3-pip python3-dev libudev-dev -y

# 3. Permisos seriales
echo "[3/5] Configurando permisos seriales..."
sudo usermod -a -G dialout $USER
echo "⚠ Nota: Reinicia sesión para aplicar cambios"

# 4. Librerías Python
echo "[4/5] Instalando librerías Python..."
pip3 install pyserial rplidar-python

# 5. Verificar
echo "[5/5] Verificando..."
python3 -c "import serial; print('✓ pyserial OK')" 2>/dev/null || echo "✗ Error"
python3 -c "from rplidar import RPLidar; print('✓ rplidar OK')" 2>/dev/null || echo "✗ Error"

echo ""
echo "=========================================="
echo "✓ Instalación completada"
echo "=========================================="
echo "Próximos pasos:"
echo "1. Carga: lidar_obstacle_avoidance_elegoo.ino (con DeviceDriverSet.h/cpp)"
echo "2. Ejecuta: python3 lidar_c1_raspberry.py"
