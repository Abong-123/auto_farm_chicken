#include <ESP32Servo.h>

Servo servo1;
int servoPin = 4;

void setup() {
  servo1.setPeriodHertz(50);          // standar servo
  servo1.attach(servoPin, 500, 2400);
}

void loop() {
  // putar kiri (full speed)
  servo1.write(0);
  delay(1000);

  // berhenti
  servo1.write(90);
  delay(1000);

  // putar kanan (full speed)
  servo1.write(180);
  delay(1000);

  // berhenti lagi
  servo1.write(90);
  delay(1000);
}