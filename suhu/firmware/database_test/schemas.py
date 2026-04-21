# schemas.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum


# =====================================================
# ENUM
# =====================================================

class UserRoleEnum(str, Enum):
    peternak = "peternak"
    admin = "admin"

class SendLogStatusEnum(str, Enum):
    pending = "pending"
    sent = "sent"
    ack = "ack"
    failed = "failed"

class SetpointSourceEnum(str, Enum):
    server = "server"
    manual = "manual"
    local = "local"

class DeviceStatusEnum(str, Enum):
    waiting_config = "waiting_config"
    running = "running"

class ConditionEnum(str, Enum):
    normal = "normal"
    overheat = "overheat"
    hipotermia = "hipotermia"

class SendLogTriggerEnum(str, Enum):
    manual = "manual"
    auto = "auto"


# =====================================================
# USER
# =====================================================

class UserBase(BaseModel):
    nama: str = Field(..., min_length=2, max_length=100)
    peternakan: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=4)
    role: UserRoleEnum = UserRoleEnum.peternak

class UserLogin(BaseModel):
    nama: str
    password: str

class UserResponse(UserBase):
    id: int
    role: UserRoleEnum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# DEVICE
# =====================================================

class DeviceBase(BaseModel):
    device_id: str = Field(..., max_length=50, pattern="^[a-zA-Z0-9_]+$")
    lokasi: Optional[str] = Field(None, max_length=100)

class DeviceClaim(BaseModel):
    """User mengklaim device yang sudah kirim data"""
    device_id: str
    lokasi: Optional[str] = Field(None, max_length=100)

class DeviceResponse(DeviceBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# RAW LOG (dari microcontroller)
# =====================================================

class RawLogCreate(BaseModel):
    """JSON yang dikirim microcontroller"""
    device_id: str
    temperature: float = Field(..., ge=-50, le=150)
    setpoint: float = Field(..., ge=0, le=100)
    setpoint_source: SetpointSourceEnum
    heater_power: int = Field(..., ge=0, le=100)
    status: DeviceStatusEnum
    condition: ConditionEnum
    timestamp: int  # unix timestamp dari device

class RawLogResponse(BaseModel):
    id: int
    device_id: str
    temperature: float
    setpoint: float
    setpoint_source: str
    heater_power: int
    status: str
    condition: str
    timestamp: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# UMUR SETTING
# =====================================================

class UmurSettingCreate(BaseModel):
    device_id: str
    umur_minggu: int = Field(..., ge=1, le=52)
    setpoint_target: float = Field(..., ge=0, le=100)

class UmurSettingUpdate(BaseModel):
    setpoint_target: float = Field(..., ge=0, le=100)

class UmurSettingResponse(BaseModel):
    id: int
    device_id: str
    umur_minggu: int
    setpoint_target: float
    is_active: bool
    activated_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# SEND LOG (command ke microcontroller)
# =====================================================

class SendLogResponse(BaseModel):
    id: int
    device_id: str
    umur_setting_id: Optional[int] = None
    msg_id: str
    setpoint: float
    umur_minggu: int
    start_timestamp: int
    status: SendLogStatusEnum
    trigger: str
    sent_at: datetime
    acknowledged_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AckReceived(BaseModel):
    """ACK dari microcontroller"""
    msg_id: str
    status: str = "received"


# =====================================================
# DASHBOARD
# =====================================================

class GrafikSuhuResponse(BaseModel):
    jam: str
    suhu_rata_rata: float
    suhu_min: float
    suhu_max: float

class ActiveSettingResponse(BaseModel):
    umur_minggu: int
    setpoint_target: float
    activated_at: datetime
    hari_berjalan: int

class DashboardResponse(BaseModel):
    device: DeviceResponse
    current_temperature: Optional[float] = None
    current_setpoint: Optional[float] = None
    current_setpoint_source: Optional[str] = None
    heater_power: Optional[int] = None
    status: Optional[str] = None
    condition: Optional[str] = None
    active_setting: Optional[ActiveSettingResponse] = None
    grafik_24jam: List[GrafikSuhuResponse] = []
    recent_send_logs: List[SendLogResponse] = []