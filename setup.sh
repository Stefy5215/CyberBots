#!/bin/bash
# Script de instalación automática para Raspberry Pi OS
# Ejecutar en la Raspberry Pi: bash setup.sh

set -e

echo "=========================================="
echo "Instalador - Robot Esquiva Obstáculos"
echo "=========================================="

# Actualizar sistema
echo "[1/5] Actualizando sistema..."
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias
echo "[2/5] Instalando dependencias..."
sudo apt-get install python3-pip python3-dev libudev-dev -y

# Dar permisos seriales
echo "[3/5] Configurando permisos seriales..."
sudo usermod -a -G dialout $USER
echo "⚠ Nota: Debes reiniciar la sesión para que se apliquen los cambios"

# Instalar librerías Python
echo "[4/5] Instalando librerías Python..."
pip3 install pyserial rplidar-python

# Verificar instalación
echo "[5/5] Verificando instalación..."
python3 -c "import serial; print('✓ pyserial OK')" 2>/dev/null || echo "✗ Error en pyserial"
python3 -c "from rplidar import RPLidar; print('✓ rplidar OK')" 2>/dev/null || echo "✗ Error en rplidar"

echo ""
echo "=========================================="
echo "✓ Instalación completada"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo "1. Reinicia sesión: exit (o reconecta SSH)"
echo "2. Carga el código en Arduino"
echo "3. Conecta el hardware"
echo "4. Prueba conexiones: python3 test_connections.py"
echo "5. Ejecuta el robot: python3 lidar_c1_obstacle_avoidance.py"
echo ""
