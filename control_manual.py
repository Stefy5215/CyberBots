#!/usr/bin/env python3
"""Control Manual del Robot"""
import serial
import time
import sys

class ManualControl:
    def __init__(self, arduino_port='/dev/ttyACM0', baudrate=9600):
        try:
            self.arduino = serial.Serial(arduino_port, baudrate, timeout=1)
            time.sleep(2)
            print("✓ Arduino conectado")
            self.servo_angle = 90
            self.motor_speed = 0
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)
    
    def send_command(self, servo, motor):
        try:
            command = f"S{servo},M{motor}\n"
            self.arduino.write(command.encode())
            self.servo_angle = servo
            self.motor_speed = motor
            print(f"✓ Servo={servo}° Motor={motor}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def forward(self):
        self.send_command(90, 180)
    
    def left(self):
        self.send_command(135, 150)
    
    def right(self):
        self.send_command(45, 150)
    
    def stop(self):
        self.send_command(90, 0)
    
    def print_menu(self):
        print("\n" + "="*40)
        print("CONTROL MANUAL - Robot")
        print("="*40)
        print("f - Adelante | l - Izquierda")
        print("r - Derecha  | s - Parar")
        print("? - Menú     | q - Salir")
        print("="*40)
    
    def run(self):
        self.print_menu()
        while True:
            try:
                cmd = input("Comando > ").lower().strip()
                if cmd == 'f':
                    self.forward()
                elif cmd == 'l':
                    self.left()
                elif cmd == 'r':
                    self.right()
                elif cmd == 's':
                    self.stop()
                elif cmd == '?':
                    self.print_menu()
                elif cmd == 'q':
                    self.stop()
                    break
            except KeyboardInterrupt:
                self.stop()
                break
        
        self.arduino.close()
        print("✓ Desconectado")

if __name__ == '__main__':
    control = ManualControl()
    control.run()
