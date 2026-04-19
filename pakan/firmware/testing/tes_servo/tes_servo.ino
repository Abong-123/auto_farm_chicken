//library servo bisa di install dengan nama "ESP32Servo" melalui Library Manager
#include <ESP32Servo.h>
// inisiasi servo dan pinnya 
Servo servo1;
int servoPin = 4;

void setup() {
  // 50 Hz = periode 20ms, ini standar untuk semua servo RC
  servo1.setPeriodHertz(50);          // standar servo
  //inisiasi durasi pulse untuk 0 - 180 
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