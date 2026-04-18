#include <Adafruit_NeoPixel.h>

#define LED_PIN 48
#define LED_COUNT 1

Adafruit_NeoPixel pixel(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  pixel.begin();
}

void loop() {
  // Merah
  pixel.setPixelColor(0, pixel.Color(255,0,0));
  pixel.show();
  delay(1000);

  // Hijau
  pixel.setPixelColor(0, pixel.Color(0,255,0));
  pixel.show();
  delay(1000);

  // Biru
  pixel.setPixelColor(0, pixel.Color(0,0,255));
  pixel.show();
  delay(1000);
}