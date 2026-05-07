# seed_sampling_data.py
from database import SessionLocal
import models
import random
from datetime import datetime

db = SessionLocal()

print("🌱 Mulai seeding data sampling...")

# Hapus data lama (opsional)
print("🗑️  Menghapus data lama...")
db.query(models.RoomSampling).delete()
db.query(models.SamplingAnalysis).delete()
db.commit()

# ==================== KONFIGURASI ====================
time_ranges = ['6-9', '9-12', '12-15', '15-18', '18-00', '00-6']
points = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']

# Suhu dasar (base) berdasarkan waktu (simulasi)
base_temperature_by_time = {
    '6-9': 24.0,    # Pagi: masih sejuk
    '9-12': 27.0,   # Menuju siang: mulai panas
    '12-15': 30.0,  # Siang: paling panas
    '15-18': 29.0,  # Sore: mulai turun
    '18-00': 26.0,  # Malam: dingin
    '00-6': 23.0    # Dini hari: paling dingin
}

# Faktor titik (P1-P6) - pengaruh posisi terhadap delta suhu
# P1 = dekat penghangat, P6 = jauh dari penghangat
point_factor = {
    'P1': 1.0,   # Paling dekat penghangat → delta paling besar
    'P2': 0.85,
    'P3': 0.70,
    'P4': 0.55,
    'P5': 0.40,
    'P6': 0.25   # Paling jauh → delta paling kecil
}

# ==================== GENERATE DATA ====================
print("📊 Generating data...")
data_count = 0

for time_range in time_ranges:
    base_temp = base_temperature_by_time[time_range]
    
    for point_id in points:
        # Faktor pengaruh titik terhadap delta
        factor = point_factor[point_id]
        
        # Base delta (kenaikan suhu dari penghangat)
        # Di siang hari, efek penghangat kurang terasa (ruangan sudah panas)
        # Di malam hari, efek penghangat lebih terasa
        if time_range in ['12-15', '15-18']:
            base_delta = 5.0  # Siang: delta lebih kecil karena ruangan sudah panas
        elif time_range in ['18-00', '00-6']:
            base_delta = 8.0  # Malam: delta lebih besar karena ruangan dingin
        else:
            base_delta = 6.5  # Pagi/sore: sedang
        
        # Hitung delta aktual berdasarkan posisi titik
        actual_delta = base_delta * factor
        
        # Suhu heater = base_temp + delta
        heater_base_temp = base_temp + actual_delta
        
        # Generate 6 data dengan variasi acak (simulasi pengukuran)
        variations = [random.uniform(-0.3, 0.3) for _ in range(6)]
        heater_data = [round(heater_base_temp + v, 1) for v in variations]
        
        # Hitung rata-rata heater
        avg_heater = sum(heater_data) / len(heater_data)
        
        # Simpan ke database
        sampling = models.RoomSampling(
            time_range=time_range,
            point_id=point_id,
            base_temperature=round(base_temp, 1),
            data_1=heater_data[0],
            data_2=heater_data[1],
            data_3=heater_data[2],
            data_4=heater_data[3],
            data_5=heater_data[4],
            data_6=heater_data[5],
            avg_heater_temp=round(avg_heater, 2),
            delta_temperature=round(avg_heater - base_temp, 2),
            notes=f"Seed data: {time_range} - {point_id}"
        )
        
        db.add(sampling)
        data_count += 1
        
        print(f"  ✓ {time_range} - {point_id}: base={base_temp:.1f}°C, delta={actual_delta:.2f}°C")

# ==================== COMMIT KE DATABASE ====================
print(f"\n💾 Menyimpan {data_count} data ke database...")
db.commit()

# ==================== TAMPILKAN RINGKASAN ====================
print("\n" + "="*60)
print("📊 RINGKASAN DATA SEEDING")
print("="*60)

# Hitung jumlah data per time_range
print("\n📈 Statistik per time_range:")
for time_range in time_ranges:
    count = db.query(models.RoomSampling).filter(
        models.RoomSampling.time_range == time_range
    ).count()
    print(f"  {time_range}: {count} data (6 titik)")

print("\n📋 Contoh data (5 record pertama):")
samples = db.query(models.RoomSampling).limit(5).all()
for sample in samples:
    print(f"  • {sample.time_range} | {sample.point_id} | "
          f"base={sample.base_temperature}°C | "
          f"avg_heater={sample.avg_heater_temp}°C | "
          f"delta={sample.delta_temperature}°C")

print("\n✅ Seeding selesai!")
print(f"   Total data: {data_count} baris")
print("   Kombinasi: 6 time_range × 6 titik = 36 data")
print("\n🚀 Sekarang jalankan POST /sampling/analyze untuk analisis")

# ==================== FUNGSI TAMBAHAN: EXPORT KE CSV ====================
def export_to_csv(filename="sampling_data_export.csv"):
    """Ekspor semua data ke CSV (opsional)"""
    import csv
    
    data = db.query(models.RoomSampling).all()
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'time_range', 'point_id', 'base_temperature', 
                        'data_1', 'data_2', 'data_3', 'data_4', 'data_5', 'data_6',
                        'avg_heater_temp', 'delta_temperature', 'sampling_time'])
        
        for d in data:
            writer.writerow([
                d.id, d.time_range, d.point_id, d.base_temperature,
                d.data_1, d.data_2, d.data_3, d.data_4, d.data_5, d.data_6,
                d.avg_heater_temp, d.delta_temperature, d.sampling_time
            ])
    
    print(f"📁 Data diekspor ke {filename}")

# Uncomment jika ingin ekspor otomatis
# export_to_csv()

db.close()
print("\n🔒 Database connection closed.")