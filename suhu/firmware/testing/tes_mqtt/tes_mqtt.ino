#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// ========== KONFIGURASI ==========
const char* ssid = "Ngunjuk kopi";
const char* password = "ngunjukkopi";

const char* mqtt_server = "192.168.1.9";  // IP Ubuntu Anda
const char* mqtt_topic = "led/control";    // Topic untuk kontrol LED

// ========== PIN DEFINISI ==========
const int LED_PIN = LED_BUILTIN;  // GPIO2 untuk NodeMCU (aktif LOW)

// ========== VARIABEL GLOBAL ==========
WiFiClient espClient;
PubSubClient client(espClient);
bool ledState = false;  // false = mati, true = menyala

// ========== SETUP ==========
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n=================================");
  Serial.println("ESP8266 MQTT LED Controller");
  Serial.println("=================================");
  
  // Setup LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);  // Matikan LED (aktif LOW)
  Serial.println("LED Internal siap (aktif LOW)");
  
  // Connect WiFi
  connectWiFi();
  
  // Setup MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  
  // Connect MQTT
  connectMQTT();
}

// ========== CONNECT WIFI ==========
void connectWiFi() {
  Serial.print("\nMenghubungkan ke WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi BERHASIL!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi GAGAL! Cek SSID/Password");
  }
}

// ========== CONNECT MQTT ==========
void connectMQTT() {
  Serial.print("\nMenghubungkan ke MQTT Broker...");
  
  int attempts = 0;
  while (!client.connected() && attempts < 10) {
    String clientId = "ESP8266_LED_" + String(ESP.getChipId());
    
    if (client.connect(clientId.c_str())) {
      Serial.println(" ✅ CONNECTED!");
      Serial.print("MQTT Broker: ");
      Serial.println(mqtt_server);
      
      // Subscribe ke topic kontrol LED
      client.subscribe(mqtt_topic);
      Serial.print("Subscribe ke topic: ");
      Serial.println(mqtt_topic);
      
      // Kirim pesan status awal
      client.publish("led/status", "ESP8266 online, LED MATI");
      Serial.println("Status awal: LED MATI");
      
    } else {
      Serial.print(".");
      attempts++;
      delay(2000);
    }
  }
  
  if (!client.connected()) {
    Serial.println("\n❌ MQTT GAGAL!");
    Serial.print("Error code: ");
    Serial.println(client.state());
  }
}

// ========== MQTT CALLBACK (Menerima Pesan) ==========
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("\n=================================");
  Serial.print("📨 PESAN MASUK!");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Pesan: ");
  
  // Konversi payload ke string
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
    Serial.print((char)payload[i]);
  }
  Serial.println();
  
  // Proses perintah berdasarkan topic
  if (String(topic) == mqtt_topic) {
    if (message == "nyala") {
      digitalWrite(LED_PIN, LOW);   // LED menyala (aktif LOW)
      ledState = true;
      Serial.println("💡 LED Internal: MENYALA");
      
      // Kirim konfirmasi
      client.publish("led/status", "LED NYALA");
      
    } 
    else if (message == "mati") {
      digitalWrite(LED_PIN, HIGH);  // LED mati (aktif LOW)
      ledState = false;
      Serial.println("💡 LED Internal: MATI");
      
      // Kirim konfirmasi
      client.publish("led/status", "LED MATI");
      
    }
    else if (message == "status") {
      String statusMsg = ledState ? "LED NYALA" : "LED MATI";
      client.publish("led/status", statusMsg.c_str());
      Serial.print("Status dikirim: ");
      Serial.println(statusMsg);
    }
    else {
      Serial.print("⚠️ Perintah tidak dikenal: ");
      Serial.println(message);
      client.publish("led/status", "Perintah tidak dikenal! Gunakan: nyala, mati, status");
    }
  }
  
  Serial.println("=================================");
}

// ========== LOOP UTAMA ==========
void loop() {
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();
  
  // Kirim heartbeat setiap 30 detik (opsional)
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 30000) {
    lastHeartbeat = millis();
    if (client.connected()) {
      String statusMsg = ledState ? "LED NYALA" : "LED MATI";
      client.publish("led/heartbeat", statusMsg.c_str());
      Serial.print("💓 Heartbeat: ");
      Serial.println(statusMsg);
    }
  }
}