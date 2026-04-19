//mendefinisikan library WiFi dan HTTPClient
#include <WiFi.h>
#include <HTTPClient.h>

//mendefinisikan trigger pin dan echo pin
#define TRIG_PIN 5
#define ECHO_PIN 18

// memasukan nilai variabel ssid dan password
const char* ssid = "Mup";
const char* password = "hai12345";

//tujuan endpoint pengiriman data json
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
    //jika wifi terkoneksi inisiasi HTTPClient
    HTTPClient http;
    //url berasal dari serverName + distance hasil bacaan dari ultrasonic
    String url = serverName + String(distance);

    //mulai mengirim ke url
    http.begin(url);

    // menangkap pesan GET dari server (kode status HTTP)
    int code = http.GET();
    switch(code) {
      case 200:
        Serial.println("✅ 200 OK - Sukses");
        Serial.print("   Response: ");
        Serial.println(http.getString());
        break;
        
      case 201:
        Serial.println("✅ 201 Created - Data tersimpan");
        break;
        
      case 400:
        Serial.println("❌ 400 Bad Request - Cek format parameter 'jarak='");
        break;
        
      case 404:
        Serial.println("❌ 404 Not Found - URL endpoint salah");
        Serial.print("   Cek: ");
        Serial.println(serverName);
        break;
        
      case 405:
        Serial.println("❌ 405 Method Not Allowed - Server butuh POST, bukan GET");
        break;
        
      case 500:
        Serial.println("❌ 500 Internal Server Error - Error di server tujuan");
        break;
        
      case 503:
        Serial.println("❌ 503 Service Unavailable - Server sedang mati/sibuk");
        break;
        
      default:
        if (code >= 200 && code < 300) {
          Serial.print("✅ Sukses dengan kode: ");
          Serial.println(code);
        } else if (code >= 400 && code < 500) {
          Serial.print("❌ Client Error - Kode: ");
          Serial.println(code);
          Serial.println("   Solusi: Periksa URL dan data yang dikirim");
        } else if (code >= 500 && code < 600) {
          Serial.print("❌ Server Error - Kode: ");
          Serial.println(code);
          Serial.println("   Solusi: Coba lagi nanti atau hubungi admin server");
        } else {
          Serial.print("⚠️ Kode tidak dikenal: ");
          Serial.println(code);
        }
        break;
    }

    // response dari GET
    Serial.print("Response: ");
    Serial.println(code);
    // response body
    String payload = http.getString();
    Serial.println(payload);

    http.end();
  }

  delay(5000);
}