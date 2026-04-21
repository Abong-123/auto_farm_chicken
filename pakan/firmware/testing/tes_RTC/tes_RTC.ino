// koneksi I2C
#include <Wire.h>
// download library RTClib by adafruit
#include <RTClib.h>
// inisiasi jenis RTC
RTC_DS3231 rtc;

// Array nama bulan (Cara 2)
const char* bulan[] = {"Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"};

// Array nama hari (Bonus)
const char* hari[] = {"Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"};

void setup() {
  // serial begin 
  Serial.begin(115200);
  Wire.begin(4, 5);  // SDA = GPIO4 (D2), SCL = GPIO5 (D1)
  // print awal kali
  Serial.println("RTC DS3231 Test");
  // jika RTC gagal begin gagal koneksi I2C maka cetak RTC tidak ditemukan sedari awal
  if (!rtc.begin()) {
    Serial.println("RTC tidak ditemukan!");
    while (1);
  }
  
  // Cek apakah RTC kehilangan daya
  if (rtc.lostPower()) {
    // memeriksa apakah RTC true (batrai copot/habis jika false berarti aman)
    Serial.println("RTC kehilangan daya, setting waktu!");
    // Setting waktu sesuai waktu kompilasi
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
  
  Serial.println("RTC siap digunakan!");
}

void loop() {
  //membaca waktu saat ini
  DateTime now = rtc.now();
  
  // Tampilkan waktu
  Serial.print(now.year(), DEC);
  Serial.print('/');
  Serial.print(bulan[now.month() - 1]);
  Serial.print('/');
  Serial.print(hari[now.dayOfTheWeek()]);
  Serial.print(" ");
  Serial.print(now.hour(), DEC);
  Serial.print(':');
  Serial.print(now.minute(), DEC);
  Serial.print(':');
  Serial.print(now.second(), DEC);
  Serial.println();
  
  delay(1000);
}