#ifndef DEVICE_DRIVER_SET_H
#define DEVICE_DRIVER_SET_H

#include <Arduino.h>

// Pines del kit Elegoo
#define ULTRASONIC_TRIG_PIN 13
#define ULTRASONIC_ECHO_PIN 12
#define ULTRASONIC_MAX_DISTANCE 200
#define servoPin 10

class DeviceDriverSet_Motor {
public:
  void begin();
  void control(bool direction_A, uint8_t speed_A, bool direction_B, uint8_t speed_B, bool enable);
  
  // Direcciones
  static const bool direction_forward = true;
  static const bool direction_backward = false;

private:
  static const uint8_t PIN_Motor_PWMA = 5;
  static const uint8_t PIN_Motor_PWMB = 6;
  static const uint8_t PIN_Motor_BIN_1 = 8;
  static const uint8_t PIN_Motor_AIN_1 = 7;
  static const uint8_t PIN_Motor_STBY = 3;
};

class DeviceDriverSet_SERVO {
public:
  void begin();
  void setAngle(uint8_t angle);
  
private:
  static const uint8_t PIN_SERVO = 10;
};

#endif
