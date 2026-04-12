#include "DeviceDriverSet.h"
#include <Servo.h>
#include <Arduino.h>

// Variables globales para servo
Servo servoMotor;

// ============ DeviceDriverSet_Motor ============
void DeviceDriverSet_Motor::begin() {
  pinMode(PIN_Motor_PWMA, OUTPUT);
  pinMode(PIN_Motor_PWMB, OUTPUT);
  pinMode(PIN_Motor_BIN_1, OUTPUT);
  pinMode(PIN_Motor_AIN_1, OUTPUT);
  pinMode(PIN_Motor_STBY, OUTPUT);
  digitalWrite(PIN_Motor_STBY, HIGH);
}

void DeviceDriverSet_Motor::control(bool direction_A, uint8_t speed_A, bool direction_B, uint8_t speed_B, bool enable) {
  if (enable) {
    digitalWrite(PIN_Motor_AIN_1, direction_A ? HIGH : LOW);
    analogWrite(PIN_Motor_PWMA, speed_A);
    digitalWrite(PIN_Motor_BIN_1, direction_B ? HIGH : LOW);
    analogWrite(PIN_Motor_PWMB, speed_B);
    digitalWrite(PIN_Motor_STBY, HIGH);
  } else {
    digitalWrite(PIN_Motor_STBY, LOW);
    analogWrite(PIN_Motor_PWMA, 0);
    analogWrite(PIN_Motor_PWMB, 0);
  }
}

// ============ DeviceDriverSet_SERVO ============
void DeviceDriverSet_SERVO::begin() {
  servoMotor.attach(PIN_SERVO);
  servoMotor.write(90);
  delay(500);
}

void DeviceDriverSet_SERVO::setAngle(uint8_t angle) {
  if (angle >= 0 && angle <= 180) {
    servoMotor.write(angle);
  }
}
