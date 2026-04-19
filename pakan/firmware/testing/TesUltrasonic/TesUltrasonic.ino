//mendefinisikan pin trigger & echo
#define TRIG_PIN 5
#define ECHO_PIN 18

void setup() {
  //menentukan baudrate serial
  Serial.begin(115200);
  //mendefinisikan pin termasuk output (mengeluarkan tegangan) atau input (menerima tegangan)
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void loop() {
  // trigger di set LOW terlebih dahulu untuk membersihkan noise bagian dari loop
  digitalWrite(TRIG_PIN, LOW);
  //trigger diberi jeda 2uS
  delayMicroseconds(2);
  // trigger diberikan tegangan 
  digitalWrite(TRIG_PIN, HIGH);
  //sesuai standar minimal trigger akan aktif selama 10 uS untuk nantinya mengaktifkan suara ultrasonic
  delayMicroseconds(10);
  //trigger kembali di setting low
  digitalWrite(TRIG_PIN, LOW);

  // baca echo dimana echo akan membaca suara yang terpantul akibat adanya objek. jadi durasi pin echo high selama berapa uS
  long duration = pulseIn(ECHO_PIN, HIGH);

  // hitung jarak (cm) dimana 0.034 adalah nilai kecepatan suara di udara pada suhu ruang (~340 m/s) diubah ke cm/µs, karena bolak balik dibagi 2, tipe data bisa float atau mau digenapkan jadi int
  float distance = duration * 0.034 / 2;

  //cetak jarak
  Serial.print("Jarak: ");
  //cetak nilai distrance
  Serial.print(distance);
  Serial.println(" cm");

  //delay untuk looping
  delay(500);
}