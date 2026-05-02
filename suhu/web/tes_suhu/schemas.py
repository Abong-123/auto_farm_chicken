# schemas.py
from pydantic import BaseModel as PydanticBaseModel
from datetime import datetime
from typing import Optional, List

# Base models untuk request/response
class ComparationBase(PydanticBaseModel):
    x: float          # Bacaan SHT30
    y: float          # Bacaan Hygrometer
    temperature_setpoint: Optional[float] = None
    test_sequence: Optional[int] = None

class ComparationCreate(ComparationBase):
    pass  # Auto-calculate x², y², xy di backend

class ComparationResponse(ComparationBase):
    id: int
    x_2: float
    y_2: float
    x_y: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Untuk input manual via Swagger
class ComparationManualInput(PydanticBaseModel):
    x: float
    y: float
    temperature_setpoint: Optional[float] = None

# Untuk hasil regresi
class ComparationResultBase(PydanticBaseModel):
    r_value: float
    a_value: float
    b_value: float
    correlation_status: str
    data_count: int

class ComparationResultResponse(ComparationResultBase):
    id: int
    regression_formula: str
    graph_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class RoomSamplingBase(PydanticBaseModel):
    time_range: str        # '6-9', '9-12', '12-15', '15-18', '18-00', '00-6'
    point_id: str          # 'P1' - 'P6'
    base_temperature: float  # Suhu dasar ruangan
    
    # 6 data pengukuran saat penghangat menyala
    data_1: Optional[float] = None
    data_2: Optional[float] = None
    data_3: Optional[float] = None
    data_4: Optional[float] = None
    data_5: Optional[float] = None
    data_6: Optional[float] = None
    
    notes: Optional[str] = None

class RoomSamplingCreate(RoomSamplingBase):
    pass

class RoomSamplingResponse(RoomSamplingBase):
    id: int
    avg_heater_temp: Optional[float] = None
    delta_temperature: Optional[float] = None
    sampling_time: datetime
    
    class Config:
        from_attributes = True


# ==================== SCHEMA ANALISIS ====================
class PointAnalysisResult(PydanticBaseModel):
    """Hasil analisis per titik per range waktu"""
    time_range: str
    point_id: str
    base_temperature: float
    avg_heater_temp: float
    delta_temperature: float
    global_avg_delta: float
    deviation: float
    rank: int
    is_representative: bool

class TimeRangeAnalysis(PydanticBaseModel):
    """Analisis per range waktu"""
    time_range: str
    global_avg_delta: float
    best_point: str
    best_point_deviation: float
    all_points: List[PointAnalysisResult]

class OverallAnalysisResponse(PydanticBaseModel):
    """Response analisis keseluruhan"""
    message: str
    total_data_analyzed: int
    recommendations: List[TimeRangeAnalysis]
    best_time_range: str
    best_point_overall: str
    summary: str

# ==================== SCHEMA DELETE ====================
class DeleteResponse(PydanticBaseModel):
    message: str
    deleted_count: int
    tables_cleared: List[str]


# schemas.py - Tambahkan ini

class RawLogBase(PydanticBaseModel):
    temperature: float
    setpoint: float  # ← sudah ada, pastikan tidak hilang
    power: float
    mode: Optional[str] = 'auto'
    kp: float
    ki: float
    kd: float

class RawLogCreate(RawLogBase):
    pass

class RawLogResponse(RawLogBase):
    id: int
    error: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PIDGraphRequest(PydanticBaseModel):
    """Parameter untuk generate grafik PID"""
    setpoint: float  # ← WAJIB!
    kp: float
    ki: float
    kd: float
    hours: Optional[float] = 1.0

class PIDCompareRequest(PydanticBaseModel):
    """Parameter untuk compare PID di setpoint yang sama"""
    setpoint: float  # ← WAJIB!
    hours: Optional[float] = 2.0