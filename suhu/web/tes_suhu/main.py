# main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, engine
import models
import schemas
from typing import List, Optional
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Untuk Windows agar tidak error
import matplotlib.pyplot as plt
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import pandas as pd
import os

# Buat folder grafik
app = FastAPI(title="API Kalibrasi SHT30")
os.makedirs("static/grafik", exist_ok=True)
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")



# Dependency database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== FUNGSI BANTU (HELPER) ====================

def calculate_settling_time(temperatures, setpoints, tolerance=0.5):
    """Hitung waktu settling"""
    if len(temperatures) < 10 or not setpoints:
        return 0
    target = setpoints[-1]
    settling_idx = len(temperatures) - 1
    for i in range(len(temperatures) - 1, -1, -1):
        if abs(temperatures[i] - target) > tolerance:
            settling_idx = i
            break
    return (len(temperatures) - 1 - settling_idx) * 10


def calculate_overshoot(temperatures, setpoint):
    """Hitung overshoot"""
    if not temperatures or setpoint <= 0:
        return 0.0
    max_temp = max(temperatures)
    if max_temp <= setpoint:
        return 0.0
    return (max_temp - setpoint) / setpoint * 100


def evaluate_pid_performance(errors, temperatures, setpoints):
    """Evaluasi performa PID"""
    if not errors or not setpoints:
        return {
            "overshoot_percent": 0,
            "steady_state_error": 0,
            "oscillation_detected": "Tidak",
            "rating": "NO_DATA"
        }
    
    target = setpoints[-1] if setpoints else 0
    max_temp = max(temperatures) if temperatures else target
    overshoot = max(0, (max_temp - target) / target * 100) if target > 0 else 0
    steady_error = np.mean(errors[-10:]) if len(errors) >= 10 else np.mean(errors)
    
    oscillation = "Tidak"
    if len(temperatures) > 20:
        last_20 = temperatures[-20:]
        peaks = 0
        for i in range(1, len(last_20) - 1):
            if last_20[i] > last_20[i-1] and last_20[i] > last_20[i+1]:
                peaks += 1
        oscillation = "Ya" if peaks > 3 else "Tidak"
    
    if abs(steady_error) < 0.2 and overshoot < 5:
        rating = "EXCELLENT"
    elif abs(steady_error) < 0.5 and overshoot < 10:
        rating = "GOOD"
    elif abs(steady_error) < 1.0:
        rating = "FAIR"
    else:
        rating = "POOR"
    
    return {
        "overshoot_percent": round(overshoot, 2),
        "steady_state_error": round(steady_error, 3),
        "oscillation_detected": oscillation,
        "rating": rating
    }


def generate_pid_recommendation(performance, kp, ki, kd):
    """Berikan rekomendasi tuning PID"""
    recommendations = []
    
    if performance.get("overshoot_percent", 0) > 10:
        recommendations.append("Overshoot terlalu tinggi -> Turunkan Kp atau Naikkan Kd")
    
    if abs(performance.get("steady_state_error", 0)) > 0.5:
        recommendations.append("Error steady state besar -> Naikkan Ki")
    
    if performance.get("oscillation_detected") == "Ya":
        recommendations.append("Terjadi osilasi -> Turunkan Kp atau Turunkan Ki")
    
    rating = performance.get("rating", "")
    if rating == "EXCELLENT":
        recommendations.append("PID sudah sangat baik! Parameter ini bisa digunakan.")
    elif rating == "GOOD":
        recommendations.append("PID cukup baik. Fine-tuning Kp +-10% untuk hasil optimal.")
    elif rating == "FAIR":
        recommendations.append("PID perlu tuning ulang. Coba metode Ziegler-Nichols.")
    elif rating == "POOR":
        recommendations.append("PID perlu tuning besar-besaran. Mulai dari Kp kecil, Ki=0, Kd=0.")
    
    return recommendations if recommendations else ["Parameter sudah cukup baik."]


def generate_comparison_graph(setpoint, results, hours):
    """Generate grafik perbandingan performa PID"""
    if not results:
        return None
    
    top_results = results[:3]
    
    plt.figure(figsize=(12, 6))
    
    labels = [f"Kp={r['kp']}, Ki={r['ki']}, Kd={r['kd']}" for r in top_results]
    rmse_values = [r['rmse'] for r in top_results]
    colors = ['gold', 'silver', '#cd7f32']
    
    bars = plt.bar(labels, rmse_values, color=colors[:len(top_results)], alpha=0.7, edgecolor='black')
    
    for bar, val in zip(bars, rmse_values):
        plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.05,
                f'{val:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.xlabel('Parameter PID', fontsize=12, fontweight='bold')
    plt.ylabel('RMSE (C)', fontsize=12, fontweight='bold')
    plt.title(f'Perbandingan Performa PID pada Setpoint {setpoint}C\n(Data {hours} jam terakhir)', 
             fontsize=14, fontweight='bold')
    plt.xticks(rotation=15, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    filename = f"static/grafik/pid_comparison_sp_{setpoint}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    return f"/{filename}"


def generate_comparison_summary(results, setpoint):
    """Generate ringkasan rekomendasi"""
    if not results:
        return "Tidak ada data untuk dianalisis"
    
    best = results[0]
    
    summary = (
        f"ANALISIS SETPOINT {setpoint}C\n\n"
        f"PARAMETER TERBAIK:\n"
        f"   Kp={best['kp']}, Ki={best['ki']}, Kd={best['kd']}\n"
        f"   -> RMSE: {best['rmse']}C\n"
        f"   -> Settling Time: {best['settling_time_seconds']} detik\n"
        f"   -> Overshoot: {best['overshoot_percent']}%\n\n"
        f"REKOMENDASI:\n"
        f"   Gunakan parameter terbaik untuk setpoint {setpoint}C."
    )
    
    return summary

@app.get("/sampling/dashboard")
def sampling_dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard HTML dengan semua grafik"""
    # Generate grafik dulu
    visualize_result = visualize_sampling(db)
    
    # Cari best overall
    best_overall = db.query(models.SamplingAnalysis).filter(
        models.SamplingAnalysis.rank_in_time_range == 1
    ).order_by(models.SamplingAnalysis.deviation_from_global.asc()).first()
    
    return templates.TemplateResponse("sampling_dashboard.html", {
        "request": request,
        "graphs": visualize_result["graphs"],
        "best_overall": best_overall
    })

# ==================== ENDPOINT 1: INPUT DATA ====================
@app.post("/comparation/input-data", response_model=schemas.ComparationResponse)
def input_data(
    data: schemas.ComparationCreate,
    db: Session = Depends(get_db)
):
    """
    Input data sensor SHT30 (x) dan Hygrometer (y)
    Otomatis menghitung x², y², dan xy
    """
    # Hitung otomatis
    x_2 = data.x ** 2
    y_2 = data.y ** 2
    x_y = data.x * data.y
    
    # Simpan ke database
    db_comparation = models.Comparation(
        x=data.x,
        y=data.y,
        x_2=x_2,
        y_2=y_2,
        x_y=x_y,
        temperature_setpoint=data.temperature_setpoint,
        test_sequence=data.test_sequence
    )
    db.add(db_comparation)
    db.commit()
    db.refresh(db_comparation)
    
    return db_comparation

# ==================== ENDPOINT 2: LIHAT SEMUA DATA ====================
@app.get("/comparation/data", response_model=List[schemas.ComparationResponse])
def get_all_data(db: Session = Depends(get_db)):
    """Lihat semua data yang sudah diinput"""
    return db.query(models.Comparation).all()

# ==================== ENDPOINT 3: HITUNG REGRESI ====================
@app.post("/comparation/calculate-regression")
def calculate_regression(db: Session = Depends(get_db)):
    """
    Hitung regresi linear dari semua data di tabel Comparation
    Simpan hasil ke tabel ComparationResult
    """
    # Ambil semua data
    data = db.query(models.Comparation).all()
    
    if len(data) < 2:
        raise HTTPException(status_code=400, detail="Minimal 2 data untuk regresi")
    
    n = len(data)
    
    # Hitung summasi
    sum_x = sum(d.x for d in data)
    sum_y = sum(d.y for d in data)
    sum_xy = sum(d.x_y for d in data)
    sum_x2 = sum(d.x_2 for d in data)
    sum_y2 = sum(d.y_2 for d in data)
    
    # Hitung b (slope)
    numerator_b = (n * sum_xy) - (sum_x * sum_y)
    denominator_b = (n * sum_x2) - (sum_x ** 2)
    
    if denominator_b == 0:
        raise HTTPException(status_code=400, detail="Denominator nol, tidak bisa hitung regresi")
    
    b = numerator_b / denominator_b
    
    # Hitung a (intercept)
    a = (sum_y - (b * sum_x)) / n
    
    # Hitung R (korelasi)
    numerator_r = (n * sum_xy) - (sum_x * sum_y)
    denominator_r = np.sqrt(((n * sum_x2) - (sum_x ** 2)) * ((n * sum_y2) - (sum_y ** 2)))
    
    if denominator_r == 0:
        r = 0
    else:
        r = numerator_r / denominator_r
    
    # Tentukan status korelasi
    if r >= 0.9:
        correlation_status = "Sangat Bagus (R ≥ 0.9)"
    elif r >= 0.8:
        correlation_status = "Cukup (R 0.8 - 0.9)"
    else:
        correlation_status = "Perlu Cek Sensor / Metode (R < 0.8)"
    
    # Formula regresi
    regression_formula = f"Y = {a:.4f} + {b:.4f}X"
    
    # Buat grafik
    graph_filename = create_graph(data, a, b, r, n)
    
    # Cek apakah sudah ada hasil regresi sebelumnya?
    existing = db.query(models.ComparationResult).first()
    if existing:
        # Update yang lama
        existing.r_value = r
        existing.a_value = a
        existing.b_value = b
        existing.regression_formula = regression_formula
        existing.correlation_status = correlation_status
        existing.graph_url = graph_filename
        existing.data_count = n
        existing.sum_x = sum_x
        existing.sum_y = sum_y
        existing.sum_xy = sum_xy
        existing.sum_x2 = sum_x2
        existing.sum_y2 = sum_y2
        db.commit()
        db.refresh(existing)
        result = existing
    else:
        # Buat baru
        db_result = models.ComparationResult(
            r_value=r,
            a_value=a,
            b_value=b,
            regression_formula=regression_formula,
            correlation_status=correlation_status,
            graph_url=graph_filename,
            data_count=n,
            sum_x=sum_x,
            sum_y=sum_y,
            sum_xy=sum_xy,
            sum_x2=sum_x2,
            sum_y2=sum_y2
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        result = db_result
    
    return {
        "message": "Regresi berhasil dihitung",
        "data_count": n,
        "formula": regression_formula,
        "a": a,
        "b": b,
        "r": r,
        "correlation_status": correlation_status,
        "graph": graph_filename
    }

def create_graph(data, a, b, r, n):
    """Buat grafik regresi"""
    x_vals = [d.x for d in data]
    y_vals = [d.y for d in data]
    
    # Garis regresi
    x_line = np.linspace(min(x_vals), max(x_vals), 100)
    y_line = a + (b * x_line)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(x_vals, y_vals, color='blue', label='Data Aktual', s=50)
    plt.plot(x_line, y_line, color='red', label=f'Regresi: Y = {a:.4f} + {b:.4f}X', linewidth=2)
    plt.plot(x_line, x_line, color='green', linestyle='--', label='Garis Ideal (Y=X)', alpha=0.5)
    
    plt.xlabel('Sensor SHT30 (X)')
    plt.ylabel('Hygrometer (Y)')
    plt.title(f'Kalibrasi Sensor SHT30 vs Hygrometer\nR = {r:.4f} (n={n})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Simpan
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"static/grafik/regression_{timestamp}.png"
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()
    
    return filename

# ==================== ENDPOINT 4: LIHAT HASIL REGRESI ====================
@app.get("/comparation/comparation-result")
def get_regression_result(db: Session = Depends(get_db)):
    """Ambil hasil regresi yang tersimpan"""
    result = db.query(models.ComparationResult).first()
    if not result:
        raise HTTPException(status_code=404, detail="Belum ada hasil regresi. Hitung dulu dengan POST /comparation/calculate-regression")
    return result

# ==================== ENDPOINT 5: HAPUS SEMUA DATA COMPARATION ====================
@app.delete("/comparation/data/all")
def clear_comparation_data(db: Session = Depends(get_db)):
    """Hapus semua data di tabel Comparation"""
    deleted = db.query(models.Comparation).delete()
    db.commit()
    return {"message": f"Berhasil menghapus {deleted} data dari tabel Comparation"}

# ==================== ENDPOINT 6: HAPUS SEMUA DATA COMPARATION_RESULT ====================
@app.delete("/comparation/comparation-result/all")
def clear_regression_result(db: Session = Depends(get_db)):
    """Hapus semua data di tabel ComparationResult"""
    deleted = db.query(models.ComparationResult).delete()
    db.commit()
    return {"message": f"Berhasil menghapus {deleted} data dari tabel ComparationResult"}

# ==================== ENDPOINT 7: AMBIL FORMULA KOREKSI ====================
@app.get("/comparation/get-correction-formula")
def get_correction_formula(db: Session = Depends(get_db)):
    """
    Ambil formula koreksi untuk ESP8266
    Hasil: Y = a + bX
    """
    result = db.query(models.ComparationResult).first()
    if not result:
        raise HTTPException(status_code=404, detail="Belum ada data kalibrasi. Hitung regresi terlebih dahulu.")
    
    return {
        "formula": result.regression_formula,
        "a": result.a_value,
        "b": result.b_value,
        "r_value": result.r_value,
        "correlation_status": result.correlation_status,
        "instruction": f"Gunakan Y = {result.a_value:.4f} + ({result.b_value:.4f} * X_sensor) untuk mengoreksi bacaan SHT30"
    }

# ==================== ENDPOINT SAMPLING DATA ====================

@app.post("/sampling/input-data", response_model=schemas.RoomSamplingResponse)
def input_sampling_data(
    data: schemas.RoomSamplingCreate,
    db: Session = Depends(get_db)
):
    """
    Input data sampling ruangan
    
    Setiap baris mewakili:
    - 1 titik (P1-P6)
    - 1 range waktu (6-9, 9-12, 12-15, 15-18, 18-00, 00-6)
    - Suhu base ruangan (tanpa penghangat)
    - 6 data suhu saat penghangat menyala
    
    Otomatis menghitung:
    - Rata-rata suhu heater (dari data_1 sd data_6)
    - Delta suhu (heater - base)
    """
    # Kumpulkan data heater yang valid (tidak None)
    heater_data = [
        d for d in [
            data.data_1, data.data_2, data.data_3,
            data.data_4, data.data_5, data.data_6
        ] if d is not None
    ]
    
    if not heater_data:
        raise HTTPException(status_code=400, detail="Minimal 1 data heater diperlukan")
    
    # Hitung rata-rata suhu heater
    avg_heater_temp = sum(heater_data) / len(heater_data)
    
    # Hitung delta (kenaikan suhu akibat penghangat)
    delta_temperature = avg_heater_temp - data.base_temperature
    
    # Simpan ke database
    db_sampling = models.RoomSampling(
        time_range=data.time_range,
        point_id=data.point_id,
        base_temperature=data.base_temperature,
        data_1=data.data_1,
        data_2=data.data_2,
        data_3=data.data_3,
        data_4=data.data_4,
        data_5=data.data_5,
        data_6=data.data_6,
        avg_heater_temp=avg_heater_temp,
        delta_temperature=delta_temperature,
        notes=data.notes
    )
    db.add(db_sampling)
    db.commit()
    db.refresh(db_sampling)
    
    return db_sampling


@app.get("/sampling/all-data", response_model=List[schemas.RoomSamplingResponse])
def get_all_sampling_data(db: Session = Depends(get_db)):
    """Lihat semua data sampling yang sudah diinput"""
    return db.query(models.RoomSampling).all()


@app.post("/sampling/analyze")
def analyze_sampling(db: Session = Depends(get_db)):
    """
    Analisis data sampling:
    - Hitung global average delta per time_range
    - Hitung deviasi setiap titik
    - Ranking titik terbaik per time_range
    - Simpan ke tabel SamplingAnalysis
    """
    # Hapus data analisis lama
    db.query(models.SamplingAnalysis).delete()
    db.commit()  # Jangan lupa commit setelah delete
    
    # Ambil semua data sampling
    all_data = db.query(models.RoomSampling).all()
    
    if len(all_data) < 6:
        raise HTTPException(status_code=400, detail="Data kurang. Minimal 6 titik (1 per time_range)")
    
    # Kelompokkan berdasarkan time_range
    time_ranges = ['6-9', '9-12', '12-15', '15-18', '18-00', '00-6']
    results = []
    
    for time_range in time_ranges:
        # Data untuk time_range ini
        data_range = [d for d in all_data if d.time_range == time_range]
        
        if len(data_range) < 6:
            continue  # Belum lengkap 6 titik
        
        # Hitung global average delta untuk time_range ini
        global_avg_delta = sum(d.delta_temperature for d in data_range) / len(data_range)
        
        # Hitung deviasi per titik dan simpan ke database
        point_results = []
        for point_data in data_range:
            deviation = abs(point_data.delta_temperature - global_avg_delta)
            
            # Simpan ke tabel analysis
            analysis = models.SamplingAnalysis(
                time_range=point_data.time_range,
                point_id=point_data.point_id,
                base_temperature=point_data.base_temperature,
                avg_heater_temp=point_data.avg_heater_temp,
                delta_temperature=point_data.delta_temperature,
                global_avg_delta=global_avg_delta,
                deviation_from_global=deviation
            )
            db.add(analysis)
            point_results.append({
                "point_id": point_data.point_id,
                "delta": point_data.delta_temperature,
                "deviation": deviation
            })
        
        # Commit dulu agar data analysis tersimpan
        db.commit()
        
        # Ranking berdasarkan deviasi terkecil
        point_results.sort(key=lambda x: x["deviation"])
        for rank, point in enumerate(point_results, 1):
            # Update analysis dengan ranking - cari ulang setelah commit
            analysis_entry = db.query(models.SamplingAnalysis).filter(
                models.SamplingAnalysis.time_range == time_range,
                models.SamplingAnalysis.point_id == point["point_id"]
            ).first()
            
            if analysis_entry:
                analysis_entry.rank_in_time_range = rank
                analysis_entry.is_most_representative = (rank == 1)
                analysis_entry.recommendation_score = point["deviation"]
                db.add(analysis_entry)
        
        db.commit()  # Commit perubahan ranking
        
        results.append({
            "time_range": time_range,
            "global_avg_delta": global_avg_delta,
            "best_point": point_results[0]["point_id"] if point_results else None,
            "best_deviation": point_results[0]["deviation"] if point_results else None,
            "all_points": point_results
        })
    
    # Cari best point overall
    best_overall = db.query(models.SamplingAnalysis).filter(
        models.SamplingAnalysis.rank_in_time_range == 1
    ).order_by(models.SamplingAnalysis.deviation_from_global.asc()).first()
    
    return {
        "message": "Analisis selesai",
        "total_data_analyzed": len(all_data),
        "recommendations": results,
        "best_time_range": best_overall.time_range if best_overall else None,
        "best_point_overall": best_overall.point_id if best_overall else None,
        "summary": f"REKOMENDASI: Gunakan titik {best_overall.point_id if best_overall else '?'} pada range waktu {best_overall.time_range if best_overall else '?'} karena memiliki deviasi terkecil."
    }

@app.get("/sampling/analysis-check")
def check_analysis(db: Session = Depends(get_db)):
    """Cek isi tabel sampling_analysis"""
    all_analysis = db.query(models.SamplingAnalysis).all()
    
    return {
        "count": len(all_analysis),
        "data": [
            {
                "id": a.id,
                "time_range": a.time_range,
                "point_id": a.point_id,
                "delta": a.delta_temperature,
                "deviation": a.deviation_from_global,
                "rank": a.rank_in_time_range,
                "is_best": a.is_most_representative
            }
            for a in all_analysis
        ]
    }


@app.get("/sampling/best-points")
def get_best_points(db: Session = Depends(get_db)):
    """Ambil semua titik terbaik per range waktu"""
    best_points = db.query(models.SamplingAnalysis).filter(
        models.SamplingAnalysis.is_most_representative == True
    ).order_by(
        models.SamplingAnalysis.time_range
    ).all()
    
    return best_points


@app.delete("/sampling/clear-all")
def clear_sampling_data(db: Session = Depends(get_db)):
    """Hapus semua data sampling dan hasil analisis"""
    deleted_sampling = db.query(models.RoomSampling).delete()
    deleted_analysis = db.query(models.SamplingAnalysis).delete()
    db.commit()
    
    return {
        "message": "Semua data sampling dibersihkan",
        "deleted_count": deleted_sampling,
        "tables_cleared": ["room_sampling", "sampling_analysis"]
    }


@app.get("/sampling/summary")
def get_sampling_summary(db: Session = Depends(get_db)):
    """Ringkasan data sampling per time_range dan point"""
    data = db.query(models.RoomSampling).all()
    
    summary = {}
    for d in data:
        if d.time_range not in summary:
            summary[d.time_range] = {}
        summary[d.time_range][d.point_id] = {
            "base_temp": d.base_temperature,
            "avg_heater": d.avg_heater_temp,
            "delta": d.delta_temperature
        }
    
    return summary

@app.get("/sampling/visualize")
def visualize_sampling(db: Session = Depends(get_db)):
    """
    Generate 6 grafik (per time_range) dari data sampling analysis
    Menampilkan delta temperature per titik vs global average
    """
    # Ambil data dari tabel SamplingAnalysis
    all_data = db.query(models.SamplingAnalysis).order_by(
        models.SamplingAnalysis.time_range,
        models.SamplingAnalysis.rank_in_time_range
    ).all()
    
    if not all_data:
        raise HTTPException(status_code=404, detail="Belum ada data analisis. Jalankan POST /sampling/analyze dulu")
    
    # Kelompokkan berdasarkan time_range
    time_ranges = ['6-9', '9-12', '12-15', '15-18', '18-00', '00-6']
    points = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
    
    generated_files = []
    
    for time_range in time_ranges:
        # Filter data untuk time_range ini
        range_data = [d for d in all_data if d.time_range == time_range]
        
        if len(range_data) < 6:
            continue
        
        # Urutkan berdasarkan point_id (P1-P6)
        range_data.sort(key=lambda x: x.point_id)
        
        # Siapkan data untuk plotting
        point_labels = [d.point_id for d in range_data]
        delta_values = [d.delta_temperature for d in range_data]
        global_avg = range_data[0].global_avg_delta if range_data else 0
        
        # Warna: hijau untuk best point, merah untuk lainnya
        colors = ['#2ecc71' if d.is_most_representative else '#e74c3c' for d in range_data]
        
        # Buat grafik
        plt.figure(figsize=(10, 6))
        
        # Bar chart
        bars = plt.bar(point_labels, delta_values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Garis rata-rata global
        plt.axhline(y=global_avg, color='blue', linestyle='--', linewidth=2, 
                   label=f'Rata-rata Global: {global_avg:.2f}°C')
        
        # Tambahkan nilai di atas bar
        for bar, delta in zip(bars, delta_values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{delta:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Tambahkan deviation di bawah bar (opsional)
        for bar, data in zip(bars, range_data):
            plt.text(bar.get_x() + bar.get_width()/2., -0.5,
                    f'dev: {data.deviation_from_global:.2f}', 
                    ha='center', va='top', fontsize=8, rotation=0, color='gray')
        
        plt.xlabel('Titik Pengukuran', fontsize=12, fontweight='bold')
        plt.ylabel('Delta Temperature (°C)', fontsize=12, fontweight='bold')
        plt.title(f'Distribusi Kenaikan Suhu - Range Waktu {time_range}\n(Penghangat Menyala)', 
                 fontsize=14, fontweight='bold')
        plt.legend(loc='upper right')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Tambahkan keterangan
        best_point = next((d for d in range_data if d.is_most_representative), None)
        if best_point:
            plt.figtext(0.5, 0.02, 
                       f'✅ Titik Terbaik: {best_point.point_id} (deviasi = {best_point.deviation_from_global:.2f}°C) | '
                       f'Rata-rata Delta: {global_avg:.2f}°C',
                       ha='center', fontsize=10, style='italic', 
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Simpan grafik
        filename = f"static/grafik/sampling_{time_range.replace('-', '_')}.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        generated_files.append({
            "time_range": time_range,
            "file_url": f"/static/grafik/sampling_{time_range.replace('-', '_')}.png",
            "global_avg": global_avg,
            "best_point": best_point.point_id if best_point else None,
            "best_deviation": best_point.deviation_from_global if best_point else None
        })
    
    return {
        "message": f"Berhasil membuat {len(generated_files)} grafik",
        "graphs": generated_files,
        "base_url": "http://localhost:8000"
    }


@app.get("/sampling/visualize/{time_range}")
def get_sampling_graph(time_range: str):
    """
    Ambil grafik spesifik berdasarkan time_range
    Contoh: /sampling/visualize/6-9
    """
    # Validasi time_range
    valid_ranges = ['6-9', '9-12', '12-15', '15-18', '18-00', '00-6']
    if time_range not in valid_ranges:
        raise HTTPException(status_code=400, detail=f"Time range harus salah satu dari {valid_ranges}")
    
    filename = f"static/grafik/sampling_{time_range.replace('-', '_')}.png"
    
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail=f"Grafik untuk {time_range} belum dibuat. Jalankan GET /sampling/visualize dulu")
    
    return FileResponse(filename, media_type="image/png")

#---------------------PID--------------------------
@app.post("/pid/log")
def save_pid_log(
    data: schemas.RawLogCreate,
    db: Session = Depends(get_db)
):
    """
    ESP8266 mengirim data PID setiap 10 detik
    Contoh payload:
    {
        "temperature": 31.5,
        "setpoint": 32.0,
        "power": 45,
        "mode": "auto",
        "kp": 8.000,
        "ki": 0.900,
        "kd": 0.000
    }
    """
    # Hitung error
    error = data.setpoint - data.temperature
    
    db_log = models.RawLog(
        temperature=data.temperature,
        setpoint=data.setpoint,
        power=data.power,
        mode=data.mode,
        kp=data.kp,
        ki=data.ki,
        kd=data.kd,
        error=error,
        created_at=datetime.now()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return {
        "message": "Data PID tersimpan",
        "id": db_log.id,
        "error": error,
        "timestamp": db_log.created_at
    }


# ==================== ENDPOINT UNTUK GRAFIK PID ====================
@app.get("/pid/graph")
def generate_pid_graph(
    setpoint: float = Query(..., description="Target suhu (contoh: 35.0)"),  # ← WAJIB
    kp: float = Query(..., description="Nilai Kp"),
    ki: float = Query(..., description="Nilai Ki"),
    kd: float = Query(..., description="Nilai Kd"),
    hours: float = Query(1.0, description="Jam terakhir yang ditampilkan (bisa 0.5 untuk 30 menit)"),
    db: Session = Depends(get_db)
):
    """
    Generate grafik performa PID berdasarkan SETPOINT dan parameter PID
    
    Contoh: /pid/graph?setpoint=35.0&kp=8.0&ki=0.9&kd=0.0&hours=2
    """
    start_time = datetime.now() - timedelta(hours=hours)
    
    # Query dengan filter setpoint + kp + ki + kd
    logs = db.query(models.RawLog).filter(
        models.RawLog.setpoint == setpoint,
        models.RawLog.kp == kp,
        models.RawLog.ki == ki,
        models.RawLog.kd == kd,
        models.RawLog.created_at >= start_time
    ).order_by(models.RawLog.created_at.asc()).all()
    
    if len(logs) < 5:
        raise HTTPException(
            status_code=404, 
            detail=f"Data tidak cukup untuk Setpoint={setpoint}°C, Kp={kp}, Ki={ki}, Kd={kd}. Hanya {len(logs)} data dalam {hours} jam terakhir."
        )
    
    # Siapkan data untuk plotting
    timestamps = [log.created_at for log in logs]
    temperatures = [log.temperature for log in logs]
    setpoints = [log.setpoint for log in logs]
    powers = [log.power for log in logs]
    errors = [log.error for log in logs]
    
    # Buat grafik dengan 3 subplot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # Subplot 1: Temperature vs Setpoint
    ax1.plot(timestamps, temperatures, 'b-', label='Suhu Aktual', linewidth=2)
    ax1.plot(timestamps, setpoints, 'r--', label='Setpoint', linewidth=2)
    ax1.set_ylabel('Suhu (C)', fontsize=12)
    ax1.set_title(f'PID Performance (Setpoint={setpoint}C, Kp={kp}, Ki={ki}, Kd={kd})', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Hitung steady state (10 data terakhir)
    if len(temperatures) > 10:
        steady_state = np.mean(temperatures[-10:])
        steady_error = np.mean(errors[-10:])
        stability = 100 - min(100, abs(steady_error) * 10)
        ax1.axhline(y=steady_state, color='g', linestyle=':', alpha=0.5, 
                   label=f'Steady State: {steady_state:.2f}C')
    else:
        stability = 0
        steady_error = None
    
    # Subplot 2: Power Output
    ax2.plot(timestamps, powers, 'g-', label='Daya PWM (%)', linewidth=2)
    ax2.set_ylabel('Daya (%)', fontsize=12)
    ax2.set_ylim([0, 100])
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # Subplot 3: Error
    ax3.plot(timestamps, errors, 'r-', label='Error (Setpoint - Suhu)', linewidth=2)
    ax3.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax3.axhline(y=0.5, color='orange', linestyle=':', alpha=0.5, label='Toleransi +-0.5C')
    ax3.axhline(y=-0.5, color='orange', linestyle=':', alpha=0.5)
    ax3.set_xlabel('Waktu', fontsize=12)
    ax3.set_ylabel('Error (C)', fontsize=12)
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # Hitung metrik performa
    max_error = max(abs(e) for e in errors) if errors else 0
    rmse = np.sqrt(np.mean(np.square(errors))) if errors else 0
    settling_time = calculate_settling_time(temperatures, setpoints)
    
    # Tambahkan info performa di footer
    info_text = (f"Data Points: {len(logs)} | "
                f"RMSE: {rmse:.3f}C | "
                f"Max Error: {max_error:.2f}C | "
                f"Settling Time: {settling_time:.0f}s | "
                f"Stability Score: {stability:.1f}/100")
    
    if steady_error is not None:
        info_text += f" | Steady Error: {steady_error:.2f}C"
    
    plt.figtext(0.5, 0.01, info_text, ha='center', fontsize=10, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Simpan grafik dengan nama file yang mencakup setpoint
    filename = f"static/grafik/pid_sp_{setpoint}_kp_{kp}_ki_{ki}_kd_{kd}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    # Evaluasi performa
    performance = evaluate_pid_performance(errors, temperatures, setpoints)
    
    return {
        "message": "Grafik PID berhasil dibuat",
        "graph_url": f"/{filename}",
        "parameters": {
            "setpoint": setpoint,
            "kp": kp,
            "ki": ki,
            "kd": kd
        },
        "metrics": {
            "data_points": len(logs),
            "time_range_hours": hours,
            "rmse": round(rmse, 3),
            "max_error": round(max_error, 2),
            "settling_time_seconds": settling_time,
            "stability_score": round(stability, 1)
        },
        "performance_analysis": performance,
        "recommendation": generate_pid_recommendation(performance, kp, ki, kd)
    }

@app.get("/pid/data")
def get_pid_data(
    setpoint: Optional[float] = None,  # ← tambahan filter setpoint
    kp: Optional[float] = None,
    ki: Optional[float] = None,
    kd: Optional[float] = None,
    hours: Optional[float] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Ambil data RAW log PID
    Bisa filter berdasarkan: setpoint, kp, ki, kd, dan hours terakhir
    
    Contoh:
    - Semua data: /pid/data
    - Setpoint 35: /pid/data?setpoint=35
    - Setpoint 35 dengan Kp=8: /pid/data?setpoint=35&kp=8
    - 2 jam terakhir: /pid/data?hours=2
    """
    query = db.query(models.RawLog)
    
    if setpoint is not None:
        query = query.filter(models.RawLog.setpoint == setpoint)
    if kp is not None:
        query = query.filter(models.RawLog.kp == kp)
    if ki is not None:
        query = query.filter(models.RawLog.ki == ki)
    if kd is not None:
        query = query.filter(models.RawLog.kd == kd)
    if hours is not None:
        start_time = datetime.now() - timedelta(hours=hours)
        query = query.filter(models.RawLog.created_at >= start_time)
    
    logs = query.order_by(models.RawLog.created_at.desc()).limit(limit).all()
    
    return logs


# ==================== ENDPOINT UNTUK LIST SEMUA SETPOINT ====================
@app.get("/pid/setpoints")
def get_all_setpoints(db: Session = Depends(get_db)):
    """
    Ambil semua setpoint unik yang pernah direkam
    """
    setpoints = db.query(models.RawLog.setpoint).distinct().order_by(models.RawLog.setpoint).all()
    
    result = []
    for sp in setpoints:
        count = db.query(models.RawLog).filter(models.RawLog.setpoint == sp[0]).count()
        pid_variations = db.query(
            models.RawLog.kp, models.RawLog.ki, models.RawLog.kd
        ).filter(
            models.RawLog.setpoint == sp[0]
        ).distinct().count()
        
        result.append({
            "setpoint": sp[0],
            "data_count": count,
            "pid_variations": pid_variations
        })
    
    return result

# ==================== DELETE ENDPOINT ====================
@app.delete("/pid/clear-all")
def clear_pid_data(db: Session = Depends(get_db)):
    """Hapus semua data PID log"""
    deleted = db.query(models.RawLog).delete()
    db.commit()
    return {"message": f"Berhasil menghapus {deleted} data PID log"}


# Jalankan dengan: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)