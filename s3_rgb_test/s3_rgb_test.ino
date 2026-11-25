// Simple ESP32-S3 onboard RGB LED test.
// Tries common onboard RGB pins (48, 38) using arduino-esp32 rgbLedWrite().
void setRgb(uint8_t r, uint8_t g, uint8_t b) {
#ifdef RGB_BUILTIN
  rgbLedWrite(RGB_BUILTIN, r, g, b);
#else
  rgbLedWrite(48, r, g, b);
  rgbLedWrite(38, r, g, b);
#endif
}

void setup() {
  // no Serial needed
}

void loop() {
  setRgb(0, 32, 0);   // green
  delay(500);
  setRgb(32, 0, 0);   // red
  delay(500);
  setRgb(0, 0, 32);   // blue
  delay(500);
  setRgb(32, 32, 32); // white
  delay(500);
  setRgb(0, 0, 0);    // off
  delay(500);
}
