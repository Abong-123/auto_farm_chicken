/**************
 * PID Dimmer + SHT30 + LCD 20x4 + Keypad I2C (PCF8574)
 * NodeMCU / ESP8266
 *
 * Fitur:
 *  - PID identik dengan ESP32-S3 (anti-windup, dt >= 0.1s)
 *  - Kirim data ke server tiap 10 detik (endpoint sama)
 *  - Atur SP, Kp, Ki, Kd, IP server via Keypad
 *  - Simpan konfigurasi ke EEPROM
 *  - LCD 20x4 I2C
 *
 * Keypad:
 *  A  → Set Setpoint
 *  B  → Set Kp
 *  C  → Set Ki
 *  D  → Set Kd
 *  *  → Batal / kembali ke RUN
 *  #  → Konfirmasi input
 *  angka → input nilai
 *  (di mode RUN, tekan * → masuk mode SET_IP)
 *
 *  Contoh: tekan A → ketik "50" → tekan # → setpoint = 50
 **************/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <Wire.h>
#include <Keypad_I2C.h>
#include <Keypad.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_SHT31.h>
#include <EEPROM.h>
#include <RBDdimmer.h>

// =====================
// WIFI
// =====================
const char* ssid     = "IphoneProMax";
const char* password = "password";

// =====================
// I2C PIN
// =====================
#define SDA_PIN D2
#define SCL_PIN D1

// =====================
// LCD 20x4
// =====================
LiquidCrystal_I2C lcd(0x27, 20, 4);

// =====================
// SHT30
// =====================
Adafruit_SHT31 sht31 = Adafruit_SHT31();

// =====================
// KEYPAD via PCF8574 (0x20)
// =====================
const byte ROWS = 4;
const byte COLS = 4;

char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte rowPins[ROWS] = {0, 1, 2, 3};
byte colPins[COLS] = {4, 5, 6, 7};

Keypad_I2C keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS, 0x20, PCF8574, &Wire);

// =====================
// DIMMER
// =====================
#define out1  D5
#define zc1   D6
#define out2  D7
#define zc2   D8

dimmerLamp dimmer1(out1, zc1);
dimmerLamp dimmer2(out2, zc2);

// =====================
// PID SETTING
// =====================
float setpoint = 50.0;
float Kp = 25.0;
float Ki = 1.0;
float Kd = 0.0;

// =====================
// PID VARIABLE
// =====================
float lastError = 0;
float integral  = 0;
unsigned long lastPIDTime = 0;
int pidOutput = 0;

bool autoMode = true;

// =====================
// SERVER
// =====================
String serverIP  = "10.127.138.77";
String serverURL = "";

unsigned long lastSend = 0;

// =====================
// EEPROM CONFIG
// =====================
struct Config {
  float sp, kp, ki, kd;
  char  ip[20];
};

Config cfg;

// =====================
// KEYPAD INPUT STATE
// =====================
String inputBuf = "";

enum Mode { RUN, SET_SP, SET_KP, SET_KI, SET_KD, SET_IP };
Mode currentMode = RUN;

// =====================
// PID FUNCTION — identik dengan ESP32-S3
// =====================
int computePID(float currentTemp) {
  unsigned long now = millis();
  float dt = (now - lastPIDTime) / 1000.0;

  if (dt < 0.1) return pidOutput;   // sama persis dengan ESP32-S3

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
// EEPROM
// =====================
void saveData() {
  cfg.sp = setpoint;
  cfg.kp = Kp;
  cfg.ki = Ki;
  cfg.kd = Kd;
  serverIP.toCharArray(cfg.ip, 20);
  EEPROM.put(0, cfg);
  EEPROM.commit();
  Serial.println(">> Config saved to EEPROM");
}

void loadData() {
  EEPROM.begin(128);
  EEPROM.get(0, cfg);

  // Validasi data EEPROM
  if (isnan(cfg.sp) || cfg.sp <= 0 || cfg.sp >= 200) {
    Serial.println(">> EEPROM invalid, pakai default");
    return; // gunakan nilai default dari deklarasi di atas
  }

  setpoint = cfg.sp;
  Kp       = cfg.kp;
  Ki       = cfg.ki;
  Kd       = cfg.kd;
  serverIP = String(cfg.ip);
  Serial.println(">> Config loaded from EEPROM");
}

// =====================
// BUILD URL
// =====================
void buildURL() {
  serverURL = "http://" + serverIP + ":8000/pid/log";
}

// =====================
// KEYPAD HANDLER
// =====================
void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;

  Serial.print("KEY: ");
  Serial.println(key);

  // Angka: tambah ke buffer
  if (key >= '0' && key <= '9') {
    inputBuf += key;
    return;
  }

  // Titik desimal (pakai tombol '.' jika ada, atau skip)
  // Keypad 4x4 standar tidak punya '.', tapi kita bisa pakai '#' sbg desimal
  // saat SET mode → dihandle di bawah

  // '*' = titik ('.' ) di semua SET mode, masuk SET_IP saat RUN
  if (key == '*') {
    if (currentMode == RUN) {
      // Masuk mode SET_IP
      currentMode = SET_IP;
      inputBuf = "";
      Serial.println(">> Mode: SET_IP");
    } else if (currentMode == SET_IP) {
      // Di SET_IP: '*' = titik untuk IP (misal 192.168.1.2)
      // Boleh tambah titik lebih dari sekali (IP punya 3 titik)
      inputBuf += '.';
      Serial.print(">> Input IP: "); Serial.println(inputBuf);
    } else {
      // Di SET_SP / KP / KI / KD: '*' = titik desimal, hanya 1x
      if (inputBuf.indexOf('.') == -1) {
        inputBuf += '.';
        Serial.print(">> Input: "); Serial.println(inputBuf);
      }
    }
    return;
  }

  // Konfirmasi '#'
  if (key == '#') {
    if (inputBuf.length() > 0) {
      float val = inputBuf.toFloat();

      switch (currentMode) {
        case SET_SP:
          if (val > 0 && val < 200) {
            setpoint = val;
            integral  = 0;
            lastError = 0;
            Serial.print(">> Setpoint: "); Serial.println(setpoint);
          }
          break;
        case SET_KP:
          Kp = val;
          Serial.print(">> Kp: "); Serial.println(Kp);
          break;
        case SET_KI:
          Ki = val;
          integral = 0;
          Serial.print(">> Ki: "); Serial.println(Ki);
          break;
        case SET_KD:
          Kd = val;
          Serial.print(">> Kd: "); Serial.println(Kd);
          break;
        case SET_IP:
          serverIP = inputBuf;
          buildURL();
          Serial.print(">> Server IP: "); Serial.println(serverIP);
          break;
        default:
          break;
      }

      saveData();
    }

    inputBuf = "";
    currentMode = RUN;
    return;
  }

  // Mode select
  if (key == 'A') { currentMode = SET_SP;  inputBuf = ""; Serial.println(">> SET Setpoint"); }
  if (key == 'B') { currentMode = SET_KP;  inputBuf = ""; Serial.println(">> SET Kp"); }
  if (key == 'C') { currentMode = SET_KI;  inputBuf = ""; Serial.println(">> SET Ki"); }
  if (key == 'D') { currentMode = SET_KD;  inputBuf = ""; Serial.println(">> SET Kd"); }
}

// =====================
// LCD UPDATE
// =====================
unsigned long lastLCD = 0;

void updateLCD(float t) {
  if (millis() - lastLCD < 500) return; // refresh tiap 500ms supaya tidak flicker
  lastLCD = millis();

  lcd.clear();

  if (currentMode == RUN) {
    // Baris 0: Suhu & Setpoint
    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print(t, 1);
    lcd.print("C SP:");
    lcd.print(setpoint, 1);
    lcd.print("C");

    // Baris 1: Kp Ki Kd
    lcd.setCursor(0, 1);
    lcd.print("Kp:");
    lcd.print(Kp, 1);
    lcd.print(" Ki:");
    lcd.print(Ki, 1);
    lcd.print(" Kd:");
    lcd.print(Kd, 1);

    // Baris 2: Output & Mode
    lcd.setCursor(0, 2);
    lcd.print("OUT:");
    lcd.print(pidOutput);
    lcd.print("%  Mode:");
    lcd.print(autoMode ? "AUTO" : "MAN");

    // Baris 3: Server IP
    lcd.setCursor(0, 3);
    lcd.print("SRV:");
    lcd.print(serverIP);
  }
  else {
    lcd.setCursor(0, 0);
    switch (currentMode) {
      case SET_SP:  lcd.print("Set Setpoint (C):"); break;
      case SET_KP:  lcd.print("Set Kp:");           break;
      case SET_KI:  lcd.print("Set Ki:");           break;
      case SET_KD:  lcd.print("Set Kd:");           break;
      case SET_IP:  lcd.print("Set Server IP:");    break;
      default: break;
    }

    lcd.setCursor(0, 1);
    lcd.print("> ");
    lcd.print(inputBuf);
    lcd.print("_");

    lcd.setCursor(0, 3);
    lcd.print("[#]=OK  [*]=titik   ");
  }
}

// =====================
// WIFI
// =====================
void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi terhubung!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// =====================
// KIRIM DATA KE SERVER
// =====================
void sendToServer(float suhu) {
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClient client;
  HTTPClient http;

  http.begin(client, serverURL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000);

  String json = "{";
  json += "\"temperature\":" + String(suhu, 1) + ",";
  json += "\"setpoint\":"    + String(setpoint, 1) + ",";
  json += "\"power\":"       + String(pidOutput) + ",";
  json += "\"mode\":\"auto\",";
  json += "\"kp\":"          + String(Kp, 3) + ",";
  json += "\"ki\":"          + String(Ki, 3) + ",";
  json += "\"kd\":"          + String(Kd, 3) + ",";
  json += "\"timestamp\":"   + String(millis());
  json += "}";

  int code = http.POST(json);

  Serial.print("HTTP Response: ");
  Serial.println(code);

  http.end();
}

// =====================
// SETUP
// =====================
void setup() {
  Serial.begin(115200);
  delay(500);

  // I2C
  Wire.begin(SDA_PIN, SCL_PIN);

  // LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("PID Dimmer v1.0");

  // Keypad
  keypad.begin();

  // SHT30
  if (!sht31.begin(0x44)) {
    Serial.println("ERROR: SHT30 tidak ditemukan!");
    lcd.setCursor(0, 1);
    lcd.print("SHT30 ERROR!");
    while (1) delay(1);
  }

  // Load config EEPROM
  loadData();
  buildURL();

  // WiFi DULU — sama persis urutan ESP32-S3
  // (dimmer pakai interrupt, harus init SETELAH WiFi stack selesai)
  lcd.setCursor(0, 1);
  lcd.print("Connecting WiFi...");
  connectWiFi();

  lcd.setCursor(0, 1);
  lcd.print("WiFi OK!          ");
  delay(1000);

  // Dimmer SETELAH WiFi — interrupt tidak akan direset WiFi stack
  dimmer1.begin(NORMAL_MODE, ON);
  dimmer2.begin(NORMAL_MODE, ON);
  dimmer1.setPower(0);
  dimmer2.setPower(0);

  // lastPIDTime SETELAH semua init selesai
  lastPIDTime = millis();

  Serial.println("=====================================");
  Serial.println(" PID Dimmer + SHT30 + ESP8266 ");
  Serial.println("=====================================");
  Serial.print("Setpoint : "); Serial.println(setpoint);
  Serial.print("Kp       : "); Serial.println(Kp);
  Serial.print("Ki       : "); Serial.println(Ki);
  Serial.print("Kd       : "); Serial.println(Kd);
  Serial.print("Server   : "); Serial.println(serverURL);
}

// =====================
// LOOP
// =====================
unsigned long lastRead = 0;

void loop() {

  // Handle keypad setiap iterasi
  handleKeypad();

  // Reconnect WiFi kalau putus
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi reconnect...");
    connectWiFi();
  }

  // Baca sensor tiap 1 detik
  if (millis() - lastRead >= 1000) {
    lastRead = millis();

    float suhu_raw = sht31.readTemperature();

    if (!isfinite(suhu_raw)) {
      Serial.println("ERROR: SHT30 gagal baca!");
      return;
    }

    // Kalibrasi SHT30 — regresi linear dari 8 titik pengukuran
    // Formula: Y = -8.1500 + (1.2533 * X_sensor)
    // R = 0.9727 (Sangat Bagus)
    float suhu = -8.1500 + (1.2533 * suhu_raw);

    // PID — identik dengan ESP32-S3
    if (autoMode) {
      pidOutput = computePID(suhu);

      dimmer1.setPower(pidOutput);
      dimmer2.setPower(pidOutput);
    }

    // Serial Monitor
    Serial.print("Raw:");
    Serial.print(suhu_raw, 1);
    Serial.print("C  Cal:");
    Serial.print(suhu, 1);
    Serial.print("C  SP:");
    Serial.print(setpoint, 1);
    Serial.print("C  PWR:");
    Serial.print(pidOutput);
    Serial.print("%  Mode:");
    Serial.println(autoMode ? "AUTO" : "MANUAL");

    // Kirim ke server tiap 10 detik
    if (millis() - lastSend >= 10000) {
      lastSend = millis();
      sendToServer(suhu);
    }

    // Update LCD
    updateLCD(suhu);
  }

  delay(10);
}
