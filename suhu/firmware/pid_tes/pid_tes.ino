/**************
 *  PID Dimmer + DHT11 - ESP32-S3
 *  DHT11  -> GPIO15
 *  ZC1    -> GPIO4  | OUT1 -> GPIO5
 *  ZC2    -> GPIO6  | OUT2 -> GPIO7
 **************/

#include <RBDdimmer.h>
#include <DHT.h>

#define USE_SERIAL  Serial

// Pin
#define outputPin1  5
#define zerocross1  4
#define outputPin2  7
#define zerocross2  6
#define DHTPIN      15
#define DHTTYPE     DHT11

DHT dht(DHTPIN, DHTTYPE);
dimmerLamp dimmer1(outputPin1, zerocross1);
dimmerLamp dimmer2(outputPin2, zerocross2);

// =====================
//  SETTING - UBAH INI
// =====================
float setpoint = 50.0;  // target suhu °C

float Kp = 8.0;   // mulai dari sini, tuning manual
float Ki = 0.9;
float Kd = 0.0;

// =====================
//  VARIABEL PID
// =====================
float lastError = 0;
float integral  = 0;
unsigned long lastPIDTime = 0;

bool autoMode = true;
int  manualVal = 0;
int  pidOutput = 0;

// =====================
//  FUNGSI PID
// =====================
int computePID(float currentTemp) {
  unsigned long now = millis();
  float dt = (now - lastPIDTime) / 1000.0;
  if (dt < 0.1) return pidOutput; // terlalu cepat, skip
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
//  BACA SERIAL
// =====================
void handleSerial() {
  if (!USE_SERIAL.available()) return;

  String input = USE_SERIAL.readStringUntil('\n');
  input.trim();

  if (input == "auto") {
    autoMode = true;
    integral  = 0;
    lastError = 0;
    USE_SERIAL.println(">> Mode: OTOMATIS PID");

  } else if (input == "manual") {
    autoMode = false;
    USE_SERIAL.println(">> Mode: MANUAL - ketik 0-100");

  } else if (input.startsWith("sp ")) {
    // contoh ketik: sp 30
    float sp = input.substring(3).toFloat();
    if (sp > 0 && sp < 100) {
      setpoint = sp;
      integral  = 0;
      lastError = 0;
      USE_SERIAL.print(">> Setpoint: ");
      USE_SERIAL.print(setpoint);
      USE_SERIAL.println(" C");
    }

  } else if (input.startsWith("kp ")) {
    // contoh ketik: kp 3.5
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
      dimmer1.setPower(manualVal);
      dimmer2.setPower(manualVal);
      USE_SERIAL.print(">> Manual: ");
      USE_SERIAL.print(manualVal);
      USE_SERIAL.println("%");
    }
  }
}

// =====================
//  SETUP
// =====================
void setup() {
  USE_SERIAL.begin(115200);
  while (!USE_SERIAL) delay(10);

  dht.begin();

  dimmer1.begin(NORMAL_MODE, ON);
  dimmer1.setPower(0);
  dimmer2.begin(NORMAL_MODE, ON);
  dimmer2.setPower(0);

  lastPIDTime = millis();

  USE_SERIAL.println("=====================================");
  USE_SERIAL.println("   PID Dimmer + DHT11  ESP32-S3     ");
  USE_SERIAL.println("=====================================");
  USE_SERIAL.print  ("   Setpoint awal : ");
  USE_SERIAL.print  (setpoint); USE_SERIAL.println(" C");
  USE_SERIAL.print  ("   Kp="); USE_SERIAL.print(Kp);
  USE_SERIAL.print  (" Ki="); USE_SERIAL.print(Ki);
  USE_SERIAL.print  (" Kd="); USE_SERIAL.println(Kd);
  USE_SERIAL.println("-------------------------------------");
  USE_SERIAL.println(" Perintah serial:");
  USE_SERIAL.println("   auto       -> mode PID otomatis");
  USE_SERIAL.println("   manual     -> mode manual");
  USE_SERIAL.println("   sp 30      -> setpoint 30 C");
  USE_SERIAL.println("   kp 3.5     -> ubah Kp");
  USE_SERIAL.println("   ki 0.1     -> ubah Ki");
  USE_SERIAL.println("   kd 0.05    -> ubah Kd");
  USE_SERIAL.println("   0-100      -> power manual");
  USE_SERIAL.println("=====================================");
}

// =====================
//  LOOP
// =====================
unsigned long lastRead = 0;

void loop() {
  handleSerial();

  // DHT11 butuh minimal 1 detik antar baca
  if (millis() - lastRead >= 1000) {
    lastRead = millis();

    float suhu     = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(suhu) || isnan(humidity)) {
      USE_SERIAL.println("ERROR: DHT11 tidak terbaca! Cek kabel.");
      return;
    }

    if (autoMode) {
      pidOutput = computePID(suhu);
      dimmer1.setPower(pidOutput);
      dimmer2.setPower(pidOutput);
    }

    // Print status
    USE_SERIAL.print("Suhu:");
    USE_SERIAL.print(suhu, 1);
    USE_SERIAL.print("C  Hum:");
    USE_SERIAL.print(humidity, 0);
    USE_SERIAL.print("%  SP:");
    USE_SERIAL.print(setpoint, 1);
    USE_SERIAL.print("C  PWR:");
    USE_SERIAL.print(autoMode ? pidOutput : manualVal);
    USE_SERIAL.print("%  ERR:");
    USE_SERIAL.print(setpoint - suhu, 2);
    USE_SERIAL.print("  Mode:");
    USE_SERIAL.println(autoMode ? "AUTO" : "MANUAL");
  }

  delay(10);
}