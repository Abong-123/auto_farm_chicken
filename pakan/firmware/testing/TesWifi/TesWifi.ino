//memasukan library Wifi sudah bawaan
#include <WiFi.h>

//memasukan nama ssid dan passwordnya tipe data character
const char* ssid = "Mup";
const char* password = "hai12345";

void setup() {
  //memilih begin baudrate
  Serial.begin(115200);
  //memberi waktu jeda
  delay(1000);

  Serial.println("Menghubungkan ke WiFi...");
  //memasukan nilai ssid & password pada library dengan WiFi.begin
  WiFi.begin(ssid, password);

  // looping connect, jika tidak terkoneksi beri jeda 500 ms untuk mencetak ..
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  //jika sudah keluar looping (terhubung cetak ini)
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