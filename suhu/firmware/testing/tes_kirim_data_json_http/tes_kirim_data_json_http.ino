#include <ESP8266WiFi.h> //library device
#include <ESP8266HTTPClient.h> //library http request
#include <WiFiClient.h> //client TCP/IP
#include <ArduinoJson.h> //parse Json
#include <DHT.h> // baca dht adafruit dht

// =====================================================
// KONFIGURASI
// =====================================================
#define DHTPIN D4 //define pin dht
#define DHTTYPE DHT11 //define tipe sensor

const char* ssid       = "IphoneProMax";
const char* password   = "password";
const char* serverUrl  = "http://10.216.167.77:8000/suhu/device/1"; // endpoint penerima

const char* DEVICE_ID  = "kandang_01"; //inisiasi device id
const int   INTERVAL   = 60000; // kirim tiap 60 detik

// =====================================================
// STATE LOKAL
// =====================================================
float    setpoint        = 32.0;   // default local
String   setpoint_source = "local";
int      heater_power    = 0;
String   status_device   = "waiting_config";

DHT dht(DHTPIN, DHTTYPE);
WiFiClient wifiClient;
unsigned long lastSend = 0;

// =====================================================
// SETUP
// =====================================================
void setup() {
  Serial.begin(115200);
  dht.begin();

  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
}

// =====================================================
// LOOP
// =====================================================
void loop() {
  if (millis() - lastSend >= INTERVAL) {
    lastSend = millis();
    sendData(); //kirim data setip interval ms
  }
}

// =====================================================
// KIRIM DATA KE SERVER
// =====================================================
void sendData() {
  // DHT11 butuh waktu, baca dua kali biar stabil
  delay(2000);
  float temp = dht.readTemperature();

  // Validasi
  if (isnan(temp) || temp == 0) {
    Serial.println("DHT11 gagal baca, skip.");
    return;
  }

  String condition = "normal";
  if (temp > 38.0) condition = "overheat";
  else if (temp < 25.0) condition = "hipotermia";

  if (setpoint_source == "local") {
    status_device = "waiting_config";
  } else {
    status_device = "running";
  }

  float error = setpoint - temp;
  heater_power = constrain((int)(error * 10), 0, 100);

  // Buat JSON manual — hindari masalah NaN di ArduinoJson
  String jsonStr = "{";
  jsonStr += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  jsonStr += "\"temperature\":" + String(temp, 1) + ",";
  jsonStr += "\"setpoint\":" + String(setpoint, 1) + ",";
  jsonStr += "\"setpoint_source\":\"" + setpoint_source + "\",";
  jsonStr += "\"heater_power\":" + String(heater_power) + ",";
  jsonStr += "\"status\":\"" + status_device + "\",";
  jsonStr += "\"condition\":\"" + condition + "\",";
  jsonStr += "\"timestamp\":" + String(millis() / 1000);
  jsonStr += "}";

  Serial.println("Sending: " + jsonStr);

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi putus, skip.");
    return;
  }

  HTTPClient http;
  http.begin(wifiClient, serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000); // timeout 10 detik

  int httpCode = http.POST(jsonStr);
  String response = http.getString();

  Serial.println("HTTP Code: " + String(httpCode));
  Serial.println("Response: " + response);

  http.end();
}