from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLAlchemyEnum
from database import Base
from datetime import datetime
import uuid
import enum

class Comparation(Base):
    __tablename__ = "comparations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) #id
    x = Column(Float, nullable=False)	#bacaan SHT30
    y = Column(Float, nullable=False)	#bacaan hygrometer
    x_2 = Column(Float, nullable=False)	#X^2
    y_2 = Column(Float, nullable=False)	#Y^2
    x_y = Column(Float, nullable=False)	#X*Y
    created_at = Column(DateTime, default=datetime.now)	#tracking waktu

    temperature_setpoint = Column(Float, nullable=True)	#30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50
    test_sequence = Column(Integer, nullable=True)


class ComparationResult(Base):
    __tablename__ = "comparation_results"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    r_value = Column(Float, nullable=False)        # BUKAN 'r' saja
    a_value = Column(Float, nullable=False)        # BUKAN 'a' saja
    b_value = Column(Float, nullable=False)        # BUKAN 'b' saja
    regression_formula = Column(String(100), nullable=False)  # BUKAN 'y'
    correlation_status = Column(String(50), nullable=True)
    correlation_status = Column(String(50), nullable=True)
    graph_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    data_count = Column(Integer, nullable=False)
    sum_x = Column(Float, nullable=True)
    sum_y = Column(Float, nullable=True)
    sum_xy = Column(Float, nullable=True)
    sum_x2 = Column(Float, nullable=True)
    sum_y2 = Column(Float, nullable=True)


class RoomSampling(Base):
    __tablename__ = "room_sampling"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Kategorisasi (per baris sudah mencakup 1 titik + 1 range waktu)
    time_range = Column(String(10), nullable=False)     # '6-9', '9-12', '12-15', '15-18', '18-00', '00-6'
    point_id = Column(String(5), nullable=False)        # 'P1', 'P2', 'P3', 'P4', 'P5', 'P6'
    
    # Suhu dasar ruangan (tanpa penghangat)
    base_temperature = Column(Float, nullable=False)    # Suhu ambient saat itu
    
    # 6 data saat penghangat menyala (cukup 6 data, tidak perlu 8)
    data_1 = Column(Float, nullable=True)
    data_2 = Column(Float, nullable=True)
    data_3 = Column(Float, nullable=True)
    data_4 = Column(Float, nullable=True)
    data_5 = Column(Float, nullable=True)
    data_6 = Column(Float, nullable=True)
    
    # Hasil hitung otomatis
    avg_heater_temp = Column(Float, nullable=True)      # Rata-rata dari data_1 - data_6
    delta_temperature = Column(Float, nullable=True)    # avg_heater_temp - base_temperature
    
    # Metadata
    sampling_time = Column(DateTime, default=datetime.now)  # Waktu input data
    notes = Column(String(200), nullable=True)


# ==================== TABLE 4: SAMPLING ANALYSIS (HASIL ANALISIS) ====================
class SamplingAnalysis(Base):
    __tablename__ = "sampling_analysis"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    time_range = Column(String(10), nullable=False)
    point_id = Column(String(5), nullable=False)
    
    # Statistik
    base_temperature = Column(Float, nullable=False)
    avg_heater_temp = Column(Float, nullable=False)
    delta_temperature = Column(Float, nullable=False)
    
    # Analisis per range waktu (global)
    global_avg_delta = Column(Float, nullable=True)     # Rata-rata delta dari semua titik di range waktu yang sama
    deviation_from_global = Column(Float, nullable=True) # |delta_temperature - global_avg_delta|
    
    # Ranking
    rank_in_time_range = Column(Integer, nullable=True)  # 1 = deviasi terkecil
    is_most_representative = Column(Boolean, default=False)
    
    # Rekomendasi
    recommendation_score = Column(Float, nullable=True)  # Semakin kecil semakin baik
    analyzed_at = Column(DateTime, default=datetime.now)

class RawLog(Base):
    __tablename__ = "raw_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    temperature = Column(Float, nullable=False)
    setpoint = Column(Float, nullable=False, index=True)  # ← tambah index untuk filter cepat
    power = Column(Float, nullable=False)
    mode = Column(String(50), nullable=True)
    kp = Column(Float, nullable=False, index=True)        # ← index
    ki = Column(Float, nullable=False, index=True)        # ← index
    kd = Column(Float, nullable=False, index=True)        # ← index
    error = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)  # ← index untuk time range

