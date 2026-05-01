/**************
 * PID Dimmer + SHT30 + WiFi Logging
 * ESP32-S3
 **************/

#include <WiFi.h>
#include <HTTPClient.h>
#include <RBDdimmer.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>

#define USE_SERIAL Serial

// =====================
// WIFI & SERVER
// =====================
const char* ssid = "IphoneProMax";
const char* password = "password";

String serverURL = "http://10.127.138.77:8000/pid/log";

unsigned long lastSend = 0;

// =====================
// PIN DIMMER
// =====================
#define outputPin1  5
#define zerocross1  4
#define outputPin2  7
#define zerocross2  6

// =====================
// PIN I2C SHT30
// =====================
#define SDA_PIN 8
#define SCL_PIN 9

Adafruit_SHT31 sht31 = Adafruit_SHT31();

dimmerLamp dimmer1(outputPin1, zerocross1);
dimmerLamp dimmer2(outputPin2, zerocross2);

// =====================
// SETTING PID
// =====================
float setpoint = 50.0;

float Kp = 25.0;
float Ki = 1.0;
float Kd = 0.0;

// =====================
// VARIABEL PID
// =====================
float lastError = 0;
float integral  = 0;
unsigned long lastPIDTime = 0;

bool autoMode = true;
int  manualVal = 0;
int  pidOutput = 0;

// =====================
// PID FUNCTION
// =====================
int computePID(float currentTemp) {
  unsigned long now = millis();
  float dt = (now - lastPIDTime) / 1000.0;

  if (dt < 0.1) return pidOutput;

  lastPIDTime = now;

  float error = setpoint - currentTemp;

  // Integral + anti-windup
  integral += error * dt;
  integral = constrain(integral, -50.0, 50.0);

  // Derivative
  float derivative = (error - lastError) / dt;
  lastError = error;

  float output = (Kp * error) + (Ki * integral) + (Kd * derivative);
  return (int)constrain(output, 0, 99);
}

// =====================
// SERIAL COMMAND
// =====================
void handleSerial() {
  if (!USE_SERIAL.available()) return;

  String input = USE_SERIAL.readStringUntil('\n');
  input.trim();

  if (input == "auto") {
    autoMode = true;
    integral  = 0;
    lastError = 0;
    USE_SERIAL.println(">> Mode: AUTO PID");

  } else if (input == "manual") {
    autoMode = false;
    USE_SERIAL.println(">> Mode: MANUAL");

  } else if (input.startsWith("sp ")) {
    float sp = input.substring(3).toFloat();
    if (sp > 0 && sp < 100) {
      setpoint = sp;
      integral  = 0;
      lastError = 0;
      USE_SERIAL.print(">> Setpoint: ");
      USE_SERIAL.println(setpoint);
    }

  } else if (input.startsWith("kp ")) {
    Kp = input.substring(3).toFloat();
    USE_SERIAL.print(">> Kp: "); USE_SERIAL.println(Kp);

  } else if (input.startsWith("ki ")) {
    Ki = input.substring(3).toFloat();
    integral = 0;
    USE_SERIAL.print(">> Ki: "); USE_SERIAL.println(Ki);

  } else if (input.startsWith("kd ")) {
    Kd = input.substring(3).toFloat();
    USE_SERIAL.print(">> Kd: "); USE_SERIAL.println(Kd);

  } else if (!autoMode) {
    int val = input.toInt();
    if (val >= 0 && val <= 100) {
      manualVal = val;
      dimmer1.setPower(val);
      dimmer2.setPower(val);

      USE_SERIAL.print(">> Manual Power: ");
      USE_SERIAL.print(val);
      USE_SERIAL.println("%");
    }
  }
}

// =====================
// WIFI CONNECT
// =====================
void connectWiFi() {
  WiFi.begin(ssid, password);

  USE_SERIAL.print("Menghubungkan WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    USE_SERIAL.print(".");
  }

  USE_SERIAL.println("\nWiFi terhubung!");
  USE_SERIAL.print("IP: ");
  USE_SERIAL.println(WiFi.localIP());
}

// =====================
// SETUP
// =====================
void setup() {
  USE_SERIAL.begin(115200);
  delay(1000);

  connectWiFi();

  // I2C START
  Wire.begin(SDA_PIN, SCL_PIN);

  // INIT SHT30
  if (!sht31.begin(0x44)) {
    USE_SERIAL.println("ERROR: SHT30 tidak ditemukan!");
    while (1) delay(1);
  }

  // INIT DIMMER
  dimmer1.begin(NORMAL_MODE, ON);
  dimmer2.begin(NORMAL_MODE, ON);

  dimmer1.setPower(0);
  dimmer2.setPower(0);

  lastPIDTime = millis();

  USE_SERIAL.println("=====================================");
  USE_SERIAL.println(" PID Dimmer + SHT30 + WiFi ");
  USE_SERIAL.println("=====================================");
  USE_SERIAL.print("Setpoint: "); USE_SERIAL.println(setpoint);
}

// =====================
// LOOP
// =====================
unsigned long lastRead = 0;

void loop() {
  handleSerial();

  // reconnect WiFi kalau putus
  if (WiFi.status() != WL_CONNECTED) {
    USE_SERIAL.println("WiFi reconnect...");
    connectWiFi();
  }

  // baca sensor tiap 1 detik
  if (millis() - lastRead >= 1000) {
    lastRead = millis();

    float suhu = sht31.readTemperature();

    if (!isfinite(suhu)) {
      USE_SERIAL.println("ERROR: SHT30 tidak terbaca!");
      return;
    }

    // PID
    if (autoMode) {
      pidOutput = computePID(suhu);
      dimmer1.setPower(pidOutput);
      dimmer2.setPower(pidOutput);
    }

    // SERIAL MONITOR
    USE_SERIAL.print("Suhu:");
    USE_SERIAL.print(suhu, 1);
    USE_SERIAL.print("C  SP:");
    USE_SERIAL.print(setpoint, 1);
    USE_SERIAL.print("C  PWR:");
    USE_SERIAL.print(autoMode ? pidOutput : manualVal);
    USE_SERIAL.print("%  Mode:");
    USE_SERIAL.println(autoMode ? "AUTO" : "MANUAL");

    // ==============================
    // KIRIM DATA TIAP 10 DETIK
    // ==============================
    if (millis() - lastSend >= 10000) {
      lastSend = millis();

      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;

        http.begin(serverURL);
        http.addHeader("Content-Type", "application/json");
        http.setTimeout(3000);

        String json = "{";
        json += "\"temperature\":" + String(suhu, 1) + ",";
        json += "\"setpoint\":" + String(setpoint, 1) + ",";
        json += "\"power\":" + String(autoMode ? pidOutput : manualVal) + ",";
        json += "\"mode\":\"" + String(autoMode ? "auto" : "manual") + "\",";
        json += "\"kp\":" + String(Kp, 3) + ",";
        json += "\"ki\":" + String(Ki, 3) + ",";
        json += "\"kd\":" + String(Kd, 3) + ",";
        json += "\"timestamp\":" + String(millis());
        json += "}";

        int httpResponseCode = http.POST(json);

        USE_SERIAL.print("HTTP Response: ");
        USE_SERIAL.println(httpResponseCode);

        http.end();
      }
    }
  }

  delay(10);
}