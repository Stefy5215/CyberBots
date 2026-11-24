#include <stdio.h>

constexpr uint8_t ENA_PIN = 25;
constexpr uint8_t IN1_PIN = 26;
constexpr uint8_t IN2_PIN = 27;
constexpr uint8_t SERVO_PIN = 18;
constexpr uint32_t COMMAND_TIMEOUT_MS = 1000;

String commandBuffer;
int currentServoAngle = -1;
uint32_t lastCommandMs = 0;
bool motorPwmReady = false;
bool servoAttached = false;
bool watchdogStopped = true;

void stopMotor() {
  if (motorPwmReady) {
    ledcWrite(ENA_PIN, 0);
  }
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
}

void setServoAngle(int angle) {
  const uint32_t pulseUs = map(angle, 0, 180, 500, 2400);
  const uint32_t duty = (pulseUs * 16383UL) / 20000UL;
  ledcWrite(SERVO_PIN, duty);
}

void setMotorSpeed(int speed) {
  speed = constrain(speed, -255, 255);
  if (speed == 0) {
    stopMotor();
    return;
  }

  if (speed > 0) {
    digitalWrite(IN1_PIN, HIGH);
    digitalWrite(IN2_PIN, LOW);
  } else {
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, HIGH);
  }
  ledcWrite(ENA_PIN, abs(speed));
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
  if (!motorPwmReady) {
    Serial.println("ERR motor pwm init");
    return;
  }

  if (angle != currentServoAngle) {
    if (!servoAttached) {
      servoAttached = ledcAttach(SERVO_PIN, 50, 14);
      if (!servoAttached) {
        stopMotor();
        Serial.println("ERR servo pwm init");
        return;
      }
    }
    setServoAngle(angle);
    currentServoAngle = angle;
    if (speed != 0) {
      delay(300);
    }
  }

  setMotorSpeed(speed);
  lastCommandMs = millis();
  watchdogStopped = speed == 0;

  Serial.print("OK S");
  Serial.print(angle);
  Serial.print(" M");
  Serial.println(speed);
}

void setup() {
  Serial.begin(9600);
  commandBuffer.reserve(32);

  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);

  motorPwmReady = ledcAttach(ENA_PIN, 20000, 8);
  stopMotor();
  lastCommandMs = millis();
  Serial.println(motorPwmReady ? "ESP32 L298N ready" : "ERR motor pwm init");
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