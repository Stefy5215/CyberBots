/*
 * Obstacle Avoidance Robot - Arduino Controller
 * Receives commands from Raspberry Pi and controls:
 * - Servo motor (steering)
 * - 12V DC motor (movement)
 * 
 * Command format: "S<angle>,M<speed>\n"
 */

#if defined(ARDUINO) && ARDUINO >= 100
  #include "Arduino.h"
#else
  #include "WProgram.h"
#endif

#include "Servo.h"

#define SERVO_PIN 9
#define MOTOR_PIN 5
#define MOTOR_DIR_PIN1 7
#define MOTOR_DIR_PIN2 8
#define LED_PIN 13

Servo servo;
int currentServoAngle = 90;
int currentMotorSpeed = 0;
unsigned long lastCommandTime = 0;
const unsigned long COMMAND_TIMEOUT_MS = 500; // stop motors if no command for this many ms
String commandBuffer = "";

void setup() {
  Serial.begin(9600);
  
  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(MOTOR_DIR_PIN1, OUTPUT);
  pinMode(MOTOR_DIR_PIN2, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  servo.attach(SERVO_PIN);
  servo.write(30);
  currentServoAngle = 30;
  
  digitalWrite(MOTOR_DIR_PIN1, LOW);
  digitalWrite(MOTOR_DIR_PIN2, LOW);
  analogWrite(MOTOR_PIN, 0);
  
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("Arduino Ready - Obstacle Avoidance Controller");
  lastCommandTime = millis();
}

void quickForwardTest() {
  servo.write(30);
  currentServoAngle = 30;
  digitalWrite(MOTOR_DIR_PIN1, HIGH);
  digitalWrite(MOTOR_DIR_PIN2, LOW);
  analogWrite(MOTOR_PIN, 200);
  delay(1500);
  digitalWrite(MOTOR_DIR_PIN1, LOW);
  digitalWrite(MOTOR_DIR_PIN2, LOW);
  analogWrite(MOTOR_PIN, 0);
}

void loop() {
  static bool started = false;

  if (!started) {
    started = true;
    servo.write(30);
    currentServoAngle = 30;
    quickForwardTest();
  }

  if (Serial.available() > 0) {
    char inChar = Serial.read();
    
    if (inChar == '\n') {
      processCommand(commandBuffer);
      commandBuffer = "";
    } else if (inChar != '\r') {
      commandBuffer += inChar;
    }
  }

  // Safety: stop motor if no command received recently
  if (millis() - lastCommandTime > COMMAND_TIMEOUT_MS) {
    if (currentMotorSpeed != 0) {
      setMotorSpeed(0);
      currentMotorSpeed = 0;
    }
  }
}

void processCommand(String command) {
  if (command.length() == 0) {
    return;
  }
  
  int servoIndex = command.indexOf('S');
  int motorIndex = command.indexOf('M');
  int commaIndex = command.indexOf(',');
  
  if (servoIndex != -1 && motorIndex != -1 && commaIndex != -1) {
    String angleStr = command.substring(servoIndex + 1, commaIndex);
    String speedStr = command.substring(motorIndex + 1);
    
    int servoAngle = angleStr.toInt();
    int motorSpeed = speedStr.toInt();
    lastCommandTime = millis();
    
    if (servoAngle >= 0 && servoAngle <= 180 && motorSpeed >= -255 && motorSpeed <= 255) {
      if (servoAngle != currentServoAngle) {
        servo.write(servoAngle);
        currentServoAngle = servoAngle;
      }
      
      if (motorSpeed != currentMotorSpeed) {
        setMotorSpeed(motorSpeed);
        currentMotorSpeed = motorSpeed;
      }
      
      Serial.print("OK: S");
      Serial.print(servoAngle);
      Serial.print(" M");
      Serial.println(motorSpeed);
    } else {
      Serial.print("ERR: Invalid values - S");
      Serial.print(servoAngle);
      Serial.print(" M");
      Serial.println(motorSpeed);
    }
  } else {
    Serial.println("ERR: Invalid command format");
  }
}

void setMotorSpeed(int speed) {
  Serial.print("DEBUG: setMotorSpeed(");
  Serial.print(speed);
  Serial.println(")");
  
  if (speed > 0) {
    // Move forward
    Serial.println("DEBUG: Forward - DIR1=HIGH, DIR2=LOW");
    digitalWrite(MOTOR_DIR_PIN1, HIGH);
    digitalWrite(MOTOR_DIR_PIN2, LOW);
    analogWrite(MOTOR_PIN, speed);
    Serial.print("DEBUG: PWM=");
    Serial.print(speed);
    Serial.print(" DIR1=");
    Serial.print(digitalRead(MOTOR_DIR_PIN1));
    Serial.print(" DIR2=");
    Serial.println(digitalRead(MOTOR_DIR_PIN2));
  } else if (speed < 0) {
    // Move backward
    Serial.println("DEBUG: Backward - DIR1=LOW, DIR2=HIGH");
    digitalWrite(MOTOR_DIR_PIN1, LOW);
    digitalWrite(MOTOR_DIR_PIN2, HIGH);
    analogWrite(MOTOR_PIN, abs(speed));
    Serial.print("DEBUG: PWM=");
    Serial.print(abs(speed));
    Serial.print(" DIR1=");
    Serial.print(digitalRead(MOTOR_DIR_PIN1));
    Serial.print(" DIR2=");
    Serial.println(digitalRead(MOTOR_DIR_PIN2));
  } else {
    // Stop
    Serial.println("DEBUG: Stop - DIR1=LOW, DIR2=LOW, PWM=0");
    digitalWrite(MOTOR_DIR_PIN1, LOW);
    digitalWrite(MOTOR_DIR_PIN2, LOW);
    analogWrite(MOTOR_PIN, 0);
    Serial.print("DEBUG: PWM=0 DIR1=");
    Serial.print(digitalRead(MOTOR_DIR_PIN1));
    Serial.print(" DIR2=");
    Serial.println(digitalRead(MOTOR_DIR_PIN2));
  }
  
  digitalWrite(LED_PIN, HIGH);
  delay(50);
  digitalWrite(LED_PIN, LOW);
}
