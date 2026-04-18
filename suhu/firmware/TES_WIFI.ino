#include <WiFi.h>

const char* ssid = "Mup";
const char* password = "hai12345";

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Menghubungkan ke WiFi...");
  WiFi.begin(ssid, password);

  // tunggu sampai connect
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi terhubung!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // cek status koneksi terus
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Masih terhubung ke WiFi");
  } else {
    Serial.println("WiFi terputus!");
  }

  delay(5000);
}