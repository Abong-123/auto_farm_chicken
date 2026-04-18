#include <WiFi.h>
#include <HTTPClient.h>

#define TRIG_PIN 5
#define ECHO_PIN 18

const char* ssid = "Mup";
const char* password = "hai12345";

String serverName = "http://103.30.194.110/feeder/jumlah_pakan?jarak=";

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");
}

void loop() {
  // trigger ultrasonic
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);
  float distance = duration * 0.034 / 2;

  Serial.print("Jarak: ");
  Serial.println(distance);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String url = serverName + String(distance);
    http.begin(url);

    int code = http.GET();

    Serial.print("Response: ");
    Serial.println(code);

    String payload = http.getString();
    Serial.println(payload);

    http.end();
  }

  delay(5000);
}