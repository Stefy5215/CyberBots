#include <stdio.h>

constexpr uint8_t STBY_PIN = 3;
constexpr uint8_t PWMA_PIN = 4;
constexpr uint8_t AIN1_PIN = 1;
constexpr uint8_t AIN2_PIN = 5;
constexpr uint8_t SERVO_PIN = 0;
constexpr uint32_t COMMAND_TIMEOUT_MS = 1000;

String commandBuffer;
int currentServoAngle = 90;
uint32_t lastCommandMs = 0;
bool watchdogStopped = false;
bool outputsReady = false;
bool motorPwmReady = false;
bool servoAttached = false;

void setServoAngle(int angle) {
  const uint32_t pulseUs = map(angle, 0, 180, 500, 2400);
  const uint32_t duty = (pulseUs * 16383UL) / 20000UL;
  ledcWrite(SERVO_PIN, duty);
}

void stopMotor() {
  if (motorPwmReady) {
    ledcWrite(PWMA_PIN, 0);
  }
  digitalWrite(AIN1_PIN, LOW);
  digitalWrite(AIN2_PIN, LOW);
  digitalWrite(STBY_PIN, LOW);
}

void setMotorSpeed(int speed) {
  speed = constrain(speed, -255, 255);
  if (speed == 0) {
    stopMotor();
    return;
  }

  digitalWrite(STBY_PIN, HIGH);
  if (speed > 0) {
    digitalWrite(AIN1_PIN, HIGH);
    digitalWrite(AIN2_PIN, LOW);
  } else {
    digitalWrite(AIN1_PIN, LOW);
    digitalWrite(AIN2_PIN, HIGH);
  }
  ledcWrite(PWMA_PIN, abs(speed));
}

void processCommand(const String &command) {
  int angle = 0;
  int speed = 0;
  char extra = '\0';
  if (sscanf(command.c_str(), "S%d,M%d%c", &angle, &speed, &extra) != 2 ||
      angle < 0 || angle > 180 || speed < -255 || speed > 255) {
    Serial.println("ERR command");
    return;
  }
  if (!outputsReady) {
    Serial.println("ERR motor pwm init");
    return;
  }

  if (!servoAttached && angle != currentServoAngle) {
    servoAttached = ledcAttach(SERVO_PIN, 50, 14);
    if (!servoAttached) {
      setMotorSpeed(0);
      Serial.println("ERR servo pwm init");
      return;
    }
    setServoAngle(angle);
    currentServoAngle = angle;
    if (speed != 0) {
      delay(300);
    }
  } else if (servoAttached && angle != currentServoAngle) {
    setServoAngle(angle);
    currentServoAngle = angle;
  }
  setMotorSpeed(speed);
  lastCommandMs = millis();
  watchdogStopped = false;

  Serial.print("OK S");
  Serial.print(angle);
  Serial.print(" M");
  Serial.println(speed);
}

void setup() {
  Serial.begin(9600);
  commandBuffer.reserve(32);

  pinMode(STBY_PIN, OUTPUT);
  pinMode(AIN1_PIN, OUTPUT);
  pinMode(AIN2_PIN, OUTPUT);
  digitalWrite(STBY_PIN, LOW);

  motorPwmReady = ledcAttach(PWMA_PIN, 20000, 8);
  outputsReady = motorPwmReady;
  stopMotor();
  if (!outputsReady) {
    Serial.println("ERR motor pwm init");
  }

  lastCommandMs = millis();
  Serial.println("C3 TB6612 ready");
}

void loop() {
  while (Serial.available() > 0) {
    const char value = static_cast<char>(Serial.read());
    if (value == '\n') {
      processCommand(commandBuffer);
      commandBuffer = "";
    } else if (value != '\r' && value >= 32 && value <= 126) {
      if (commandBuffer.length() < 31) {
        commandBuffer += value;
      } else {
        commandBuffer = "";
      }
    }
  }

  if (!watchdogStopped && millis() - lastCommandMs > COMMAND_TIMEOUT_MS) {
    stopMotor();
    watchdogStopped = true;
    Serial.println("STOP watchdog");
  }
}