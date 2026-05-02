/**************
 *  RobotDyn Dimmer - ESP32-S3 Version
 *  Dimmer 1: ZC -> GPIO4 | OUT -> GPIO5
 *  Dimmer 2: ZC -> GPIO6 | OUT -> GPIO7
 **************/

// ============================================================
// BAGIAN 1: INCLUDE LIBRARY DAN DEFINE PIN
// ============================================================

// Memasukkan library RBDdimmer.h untuk mengontrol modul dimmer
// Library ini menangani deteksi zero-crossing dan pengaturan phase cut
#include <RBDdimmer.h>

// Memberi nama alias "USE_SERIAL" untuk objek Serial bawaan ESP32
// Ini memudahkan jika nanti ingin ganti ke Serial1, Serial2, dll
#define USE_SERIAL  Serial

// ----- PIN UNTUK DIMMER 1 -----
#define outputPin1  5   // OUT dimmer 1 (GPIO5) - pin yang mengirim sinyal TRIAC
#define zerocross1  4   // ZC dimmer 1 (GPIO4) - pin deteksi zero crossing dari listrik AC

// ----- PIN UNTUK DIMMER 2 -----
#define outputPin2  7   // OUT dimmer 2 (GPIO7)
#define zerocross2  6   // ZC dimmer 2 (GPIO6)

// ============================================================
// BAGIAN 2: MEMBUAT OBJEK DIMMER
// ============================================================

// Membuat objek dimmer untuk lampu 1
// Parameter: (pin_OUT, pin_ZC)
dimmerLamp dimmer1(outputPin1, zerocross1);

// Membuat objek dimmer untuk lampu 2
dimmerLamp dimmer2(outputPin2, zerocross2);

// Variabel untuk menyimpan nilai kecerahan yang diminta (0-100)
int outVal = 0;

// Variabel untuk menyimpan nilai sebelumnya, supaya tidak update terus-menerus
// Diinisialisasi -1 karena nilai 0-100 valid, -1 berarti "belum pernah diset"
int prevVal = -1;

// ============================================================
// BAGIAN 3: FUNGSI SETUP (dijalankan sekali di awal)
// ============================================================

void setup() {
  // Memulai komunikasi serial dengan kecepatan 115200 baud
  USE_SERIAL.begin(115200);
  
  // Loop kecil: tunggu sampai port serial benar-benar siap
  // (terutama penting untuk board yang pakai USB native seperti ESP32-S3)
  while (!USE_SERIAL) delay(10);

  // --- INISIALISASI DIMMER 1 ---
  // begin(NORMAL_MODE, ON) -> mode normal (bukan inverse), dan dimmer aktif (ON)
  dimmer1.begin(NORMAL_MODE, ON);
  dimmer1.setPower(0);   // Mulai dengan kecerahan 0% (mati)

  // --- INISIALISASI DIMMER 2 ---
  dimmer2.begin(NORMAL_MODE, ON);
  dimmer2.setPower(0);   // Mulai dengan kecerahan 0% (mati)

  // --- CETAK MENU PETUNJUK KE SERIAL MONITOR ---
  USE_SERIAL.println("================================");
  USE_SERIAL.println("  RobotDyn 2x Dimmer ESP32-S3  ");
  USE_SERIAL.println("  D1: ZC=GPIO4 | OUT=GPIO5     ");
  USE_SERIAL.println("  D2: ZC=GPIO6 | OUT=GPIO7     ");
  USE_SERIAL.println("================================");
  USE_SERIAL.println("Masukkan nilai 0 - 100 :");
}

// ============================================================
// BAGIAN 4: FUNGSI BANTUAN (PRINT DENGAN FORMAT RAPI)
// ============================================================

// Fungsi ini mencetak nilai kecerahan dengan format yang rapi
// Contoh output: "lampValue ->  50%"  (ada spasi biar lurus)
void printPower(int val) {
  USE_SERIAL.print("lampValue -> ");
  
  // Jika nilai kurang dari 100, tambahkan 1 spasi di depan
  if (val < 100) USE_SERIAL.print(" ");
  // Jika nilai kurang dari 10, tambahkan 1 spasi lagi (total 2 spasi)
  if (val < 10)  USE_SERIAL.print(" ");
  
  USE_SERIAL.print(val);      // Cetak angkanya
  USE_SERIAL.println("%");     // Cetak simbol persen lalu pindah baris
}

// ============================================================
// BAGIAN 5: FUNGSI LOOP (dijalankan terus-menerus)
// ============================================================

void loop() {
  // --------------------------------------------------------
  // STEP 1: BACA INPUT DARI SERIAL MONITOR
  // --------------------------------------------------------
  
  // Cek apakah ada data yang masuk dari serial
  if (USE_SERIAL.available()) {
    
    // parseInt() membaca angka dari serial (sampai menemukan non-angka)
    // Contoh: jika user kirim "75", maka buf = 75
    int buf = USE_SERIAL.parseInt();
    
    // Bersihkan buffer serial dari sisa karakter (seperti newline, spasi, dll)
    // Supaya tidak mengganggu pembacaan berikutnya
    while (USE_SERIAL.available()) USE_SERIAL.read();

    // Validasi: apakah angka yang dimasukkan antara 0 sampai 100?
    if (buf >= 0 && buf <= 100) {
      outVal = buf;   // Simpan nilai yang valid
    } else {
      // Jika angka di luar range, kasih peringatan
      USE_SERIAL.println("Input tidak valid! Masukkan 0 - 100");
    }
  }

  // --------------------------------------------------------
  // STEP 2: UPDATE DIMMER (HANYA JIKA NILAI BERUBAH)
  // --------------------------------------------------------
  
  // Cek apakah nilai kecerahan yang sekarang (outVal) berbeda dengan sebelumnya (prevVal)
  // Ini penting agar tidak terus-menerus mengirim perintah setPower ke dimmer
  // (menghemat prosesor dan mengurangi noise di jalur kontrol)
  if (outVal != prevVal) {
    
    // Set kedua dimmer ke nilai kecerahan yang sama
    // Catatan: Kedua lampu akan menyala dengan intensitas IDENTIK
    dimmer1.setPower(outVal);
    dimmer2.setPower(outVal);

    // Cetak informasi ke serial monitor
    USE_SERIAL.print("Dimmer 1 & 2 -> ");
    printPower(outVal);

    // Update nilai sebelumnya sama dengan nilai sekarang
    // Supaya di loop berikutnya tidak update lagi jika nilainya sama
    prevVal = outVal;
  }

  // --------------------------------------------------------
  // STEP 3: DELAY SINGKAT
  // --------------------------------------------------------
  
  // Delay 10ms agar loop tidak terlalu cepat dan memberi waktu ke proses lain
  // Delay ini aman karena pengaturan dimmer sudah ditangani oleh interrupt 
  // dari library RBDdimmer (zero-crossing detection)
  delay(10);
}