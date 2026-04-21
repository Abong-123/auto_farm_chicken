from sqlalchemy import Column, Integer, String, Float, Boolean, TIMESTAMP, BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLAlchemyEnum
from database import Base
from datetime import datetime
import uuid
import enum

class UserRole(enum.Enum):
    peternak = "peternak"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole, name="userrole", create_type=False), default=UserRole.peternak)
    password = Column(String(255), nullable=False)
    peternakan = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    
    devices = relationship("Device", back_populates="user")


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {"schema": "suhu"}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("public.users.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    lokasi = Column(String(100))
    created_at = Column(TIMESTAMP, default=datetime.now)
    
    user = relationship("User", back_populates="devices")
    raw_logs = relationship("RawLog", back_populates="device")
    umur_settings = relationship("UmurSetting", back_populates="device")
    send_logs = relationship("SendLog", back_populates="device")


class RawLog(Base):
    __tablename__ = "raw_logs"
    __table_args__ = {"schema": "suhu"}
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), ForeignKey("suhu.devices.device_id", ondelete="CASCADE"), nullable=False)
    temperature = Column(Float)
    setpoint = Column(Float)
    setpoint_source = Column(String(20))  # server, manual, local
    heater_power = Column(Integer)
    status = Column(String(20))           # waiting_config, running
    condition = Column(String(20))        # normal, overheat, hipotermia
    timestamp = Column(BigInteger)        # timestamp dari device
    created_at = Column(TIMESTAMP, default=datetime.now)
    
    device = relationship("Device", back_populates="raw_logs")


class UmurSetting(Base):
    __tablename__ = "umur_settings"
    __table_args__ = {"schema": "suhu"}
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), ForeignKey("suhu.devices.device_id", ondelete="CASCADE"), nullable=False)
    umur_minggu = Column(Integer, nullable=False)
    setpoint_target = Column(Float, nullable=False)
    is_active = Column(Boolean, default=False)
    activated_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.now)
    
    device = relationship("Device", back_populates="umur_settings")
    send_logs = relationship("SendLog", back_populates="umur_setting")


class SendLog(Base):
    __tablename__ = "send_logs"
    __table_args__ = {"schema": "suhu"}
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), ForeignKey("suhu.devices.device_id", ondelete="CASCADE"), nullable=False)
    umur_setting_id = Column(Integer, ForeignKey("suhu.umur_settings.id", ondelete="SET NULL"), nullable=True)
    msg_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    setpoint = Column(Float, nullable=False)
    umur_minggu = Column(Integer, nullable=False)
    start_timestamp = Column(BigInteger, nullable=False)
    status = Column(String(20), default="pending")  # pending, sent, ack, failed
    trigger = Column(String(20), default="manual")  # manual, auto
    sent_at = Column(TIMESTAMP, default=datetime.now)
    acknowledged_at = Column(TIMESTAMP)
    error_message = Column(Text)
    
    device = relationship("Device", back_populates="send_logs")
    umur_setting = relationship("UmurSetting", back_populates="send_logs")