/*
 * Robot Esquiva Obstáculos con LiDAR C1 - Elegoo Smart Car
 * Compatible con: Raspberry Pi 5 + Elegoo Kit Car + LiDAR C1
 * 
 * Formato de comando desde Raspberry Pi: "S<ángulo>,M<velocidad>\n"
 * Ejemplo: "S90,M70\n" (servo 90°, velocidad 70)
 */

#include "DeviceDriverSet.h"

DeviceDriverSet_Motor motor;
DeviceDriverSet_SERVO servo;

// Configuración de velocidades
const uint8_t SPD_SLOW = 40;      // Velocidad lenta
const uint8_t SPD_NORMAL = 70;    // Velocidad normal
const uint8_t SPD_FAST = 120;     // Velocidad rápida
const uint8_t SPD_TURN = 170;     // Velocidad para giros

// Variables de estado
int currentServoAngle = 90;
uint8_t currentMotorSpeed = 0;
String commandBuffer = "";
unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 5000;  // 5 segundos

// Control de LED
const uint8_t LED_PIN = 13;

void setup() {
  Serial.begin(9600);
  
  // Inicializar componentes
  motor.begin();
  servo.begin();
  pinMode(LED_PIN, OUTPUT);
  
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("[ELEGOO] Sistema listo - Esperando comandos LiDAR");
  lastCommandTime = millis();
}

void loop() {
  // Leer comandos seriales
  handleSerial();
  
  // Watchdog: detener si no hay comandos
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT) {
    stopRobot();
    lastCommandTime = millis();
  }
}

void handleSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    lastCommandTime = millis();
    
    if (c == '\n' || c == '\r') {
      if (commandBuffer.length() > 0) {
        processCommand(commandBuffer);
        commandBuffer = "";
      }
    } else if (c >= 32 && c <= 126) {  // Caracteres válidos
      commandBuffer += c;
      if (commandBuffer.length() > 20) {
        commandBuffer = "";  // Evitar buffer overflow
      }
    }
  }
}

void processCommand(String cmd) {
  // Formato: "S<ángulo>,M<velocidad>"
  // Ejemplo: "S90,M70"
  
  int servoIdx = cmd.indexOf('S');
  int motorIdx = cmd.indexOf('M');
  
  if (servoIdx != -1 && motorIdx != -1) {
    int commaIdx = cmd.indexOf(',');
    
    String servoStr = cmd.substring(servoIdx + 1, commaIdx);
    String motorStr = cmd.substring(motorIdx + 1);
    
    int servoAngle = servoStr.toInt();
    int motorSpeed = motorStr.toInt();
    
    // Validar rangos
    if (servoAngle >= 0 && servoAngle <= 180 && motorSpeed >= 0 && motorSpeed <= 255) {
      // Actualizar servo
      if (servoAngle != currentServoAngle) {
        servo.setAngle(servoAngle);
        currentServoAngle = servoAngle;
      }
      
      // Actualizar motor
      setMotorSpeed(motorSpeed);
      
      // Feedback
      Serial.print("[CMD] S");
      Serial.print(servoAngle);
      Serial.print(" M");
      Serial.println(motorSpeed);
      
      blinkLED();
    } else {
      Serial.println("[ERR] Valores fuera de rango");
    }
  } else {
    Serial.println("[ERR] Formato inválido");
  }
}

void setMotorSpeed(uint8_t speed) {
  if (speed == 0) {
    stopRobot();
  } else if (speed <= 127) {
    // Marcha adelante
    motor.control(
      DeviceDriverSet_Motor::direction_forward, speed,
      DeviceDriverSet_Motor::direction_forward, speed,
      true
    );
  } else {
    // Marcha atrás (velocidades > 127)
    motor.control(
      DeviceDriverSet_Motor::direction_backward, 255 - speed,
      DeviceDriverSet_Motor::direction_backward, 255 - speed,
      true
    );
  }
  currentMotorSpeed = speed;
}

void stopRobot() {
  motor.control(
    DeviceDriverSet_Motor::direction_forward, 0,
    DeviceDriverSet_Motor::direction_forward, 0,
    false
  );
  currentMotorSpeed = 0;
}

void blinkLED() {
  digitalWrite(LED_PIN, HIGH);
  delay(30);
  digitalWrite(LED_PIN, LOW);
}
