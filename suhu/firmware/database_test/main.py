# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import requests
import uuid
import time

from database import get_db, engine
import models
import schemas

# Buat semua tabel
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Feeder Temperature API",
    description="Sistem monitoring & kontrol suhu kandang ayam",
    version="1.0.0"
)


# =====================================================
# USER
# =====================================================

@app.post("/users", response_model=schemas.UserResponse, tags=["User"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.nama == user.nama).first()
    if existing:
        raise HTTPException(400, "Nama user sudah ada")

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    db_user = models.User(
        nama=user.nama,
        peternakan=user.peternakan,
        role=models.UserRole[user.role.value],
        password=pwd_context.hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[schemas.UserResponse], tags=["User"])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["User"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User tidak ditemukan")
    return user


# =====================================================
# DEVICE
# =====================================================

@app.get("/suhu/devices/unclaimed", response_model=List[schemas.DeviceResponse], tags=["Device"])
def get_unclaimed_devices(db: Session = Depends(get_db)):
    """
    Daftar device yang belum di-claim user.
    Dipakai untuk dropdown saat user mau daftarkan device.
    """
    return db.query(models.Device).filter(models.Device.user_id == None).all()

@app.get("/suhu/devices/user/{user_id}", response_model=List[schemas.DeviceResponse], tags=["Device"])
def get_user_devices(user_id: int, db: Session = Depends(get_db)):
    """Semua device milik user tertentu"""
    return db.query(models.Device).filter(models.Device.user_id == user_id).all()

@app.post("/suhu/devices/claim/{user_id}", response_model=schemas.DeviceResponse, tags=["Device"])
def claim_device(user_id: int, payload: schemas.DeviceClaim, db: Session = Depends(get_db)):
    """
    User mengklaim device dari list unclaimed.
    Mengisi user_id dan lokasi kandang.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User tidak ditemukan")

    device = db.query(models.Device).filter(models.Device.device_id == payload.device_id).first()
    if not device:
        raise HTTPException(404, "Device tidak ditemukan")
    if device.user_id is not None:
        raise HTTPException(400, "Device sudah dimiliki user lain")

    device.user_id = user_id
    device.lokasi = payload.lokasi
    db.commit()
    db.refresh(device)
    return device

@app.delete("/suhu/devices/{device_id}", tags=["Device"])
def delete_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter(models.Device.device_id == device_id).first()
    if not device:
        raise HTTPException(404, "Device tidak ditemukan")
    db.delete(device)
    db.commit()
    return {"message": f"Device {device_id} dihapus"}


# =====================================================
# RAW LOG (dari microcontroller)
# =====================================================

@app.post("/suhu/device/{channel}", response_model=schemas.RawLogResponse, tags=["Raw Log"])
def receive_raw_log(channel: int, log: schemas.RawLogCreate, db: Session = Depends(get_db)):
    """
    Endpoint untuk microcontroller kirim data tiap 1 menit.
    Channel = nomor slot microcontroller (misal /suhu/device/1).
    Auto-create device jika device_id belum ada.
    """
    # Auto-create device jika belum ada
    device = db.query(models.Device).filter(models.Device.device_id == log.device_id).first()
    if not device:
        device = models.Device(
            device_id=log.device_id,
            user_id=None,
            lokasi=None
        )
        db.add(device)
        db.commit()

    db_log = models.RawLog(
        device_id=log.device_id,
        temperature=log.temperature,
        setpoint=log.setpoint,
        setpoint_source=log.setpoint_source.value,
        heater_power=log.heater_power,
        status=log.status.value,
        condition=log.condition.value,
        timestamp=log.timestamp
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@app.get("/suhu/raw-log/{device_id}", response_model=List[schemas.RawLogResponse], tags=["Raw Log"])
def get_raw_logs(device_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """History raw log untuk device tertentu"""
    return db.query(models.RawLog)\
        .filter(models.RawLog.device_id == device_id)\
        .order_by(models.RawLog.created_at.desc())\
        .limit(limit).all()


# =====================================================
# UMUR SETTING
# =====================================================

@app.post("/suhu/umur-settings", response_model=schemas.UmurSettingResponse, tags=["Umur Setting"])
def create_umur_setting(setting: schemas.UmurSettingCreate, db: Session = Depends(get_db)):
    """Buat setting umur baru untuk device"""
    device = db.query(models.Device).filter(models.Device.device_id == setting.device_id).first()
    if not device:
        raise HTTPException(404, "Device tidak ditemukan")

    existing = db.query(models.UmurSetting).filter(
        models.UmurSetting.device_id == setting.device_id,
        models.UmurSetting.umur_minggu == setting.umur_minggu
    ).first()
    if existing:
        raise HTTPException(400, f"Umur minggu ke-{setting.umur_minggu} sudah ada")

    db_setting = models.UmurSetting(
        device_id=setting.device_id,
        umur_minggu=setting.umur_minggu,
        setpoint_target=setting.setpoint_target
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@app.get("/suhu/umur-settings/{device_id}", response_model=List[schemas.UmurSettingResponse], tags=["Umur Setting"])
def get_umur_settings(device_id: str, db: Session = Depends(get_db)):
    """Semua setting umur untuk device tertentu"""
    return db.query(models.UmurSetting)\
        .filter(models.UmurSetting.device_id == device_id)\
        .order_by(models.UmurSetting.umur_minggu).all()

@app.put("/suhu/umur-settings/{setting_id}", response_model=schemas.UmurSettingResponse, tags=["Umur Setting"])
def update_umur_setting(setting_id: int, payload: schemas.UmurSettingUpdate, db: Session = Depends(get_db)):
    """Edit setpoint target"""
    setting = db.query(models.UmurSetting).filter(models.UmurSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(404, "Setting tidak ditemukan")
    setting.setpoint_target = payload.setpoint_target
    db.commit()
    db.refresh(setting)
    return setting

@app.delete("/suhu/umur-settings/{setting_id}", tags=["Umur Setting"])
def delete_umur_setting(setting_id: int, db: Session = Depends(get_db)):
    """Hapus setting umur"""
    setting = db.query(models.UmurSetting).filter(models.UmurSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(404, "Setting tidak ditemukan")
    db.delete(setting)
    db.commit()
    return {"message": "Setting dihapus"}

@app.put("/suhu/umur-settings/{setting_id}/activate", response_model=schemas.SendLogResponse, tags=["Umur Setting"])
def activate_umur_setting(setting_id: int, db: Session = Depends(get_db)):
    setting = db.query(models.UmurSetting).filter(models.UmurSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(404, "Setting tidak ditemukan")

    db.query(models.UmurSetting).filter(
        models.UmurSetting.device_id == setting.device_id,
        models.UmurSetting.id != setting_id
    ).update({"is_active": False, "activated_at": None})

    setting.is_active = True
    setting.activated_at = datetime.now()

    send_log = models.SendLog(
        device_id=setting.device_id,
        umur_setting_id=setting.id,
        setpoint=setting.setpoint_target,
        umur_minggu=setting.umur_minggu,
        start_timestamp=int(time.time()),
        status="pending",
        trigger="manual"
    )
    db.add(send_log)
    db.commit()
    db.refresh(send_log)

    # Kirim ke NodeMCU via HTTP
    payload = {
        "setpoint": setting.setpoint_target,
        "umur": setting.umur_minggu,
        "msg_id": send_log.msg_id,
        "start_timestamp": send_log.start_timestamp
    }

    NODEMCU_IP = "http://10.216.167.211"  # ganti IP NodeMCU kamu

    try:
        r = requests.post(f"{NODEMCU_IP}/command", json=payload, timeout=5)
        if r.status_code == 200:
            send_log.status = "sent"
        else:
            send_log.status = "failed"
            send_log.error_message = f"NodeMCU response: {r.status_code}"
    except Exception as e:
        send_log.status = "failed"
        send_log.error_message = str(e)

    db.commit()
    db.refresh(send_log)
    return send_log


# =====================================================
# SEND LOG & ACK
# =====================================================

@app.post("/suhu/ack", tags=["Send Log"])
def receive_ack(ack: schemas.AckReceived, db: Session = Depends(get_db)):
    """Microcontroller konfirmasi terima command"""
    send_log = db.query(models.SendLog).filter(models.SendLog.msg_id == ack.msg_id).first()
    if not send_log:
        raise HTTPException(404, "msg_id tidak ditemukan")

    send_log.status = "ack"
    send_log.acknowledged_at = datetime.now()
    db.commit()
    return {"message": "ACK diterima", "msg_id": ack.msg_id}

@app.get("/suhu/send-logs/{device_id}", response_model=List[schemas.SendLogResponse], tags=["Send Log"])
def get_send_logs(device_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """History command yang dikirim ke device"""
    return db.query(models.SendLog)\
        .filter(models.SendLog.device_id == device_id)\
        .order_by(models.SendLog.sent_at.desc())\
        .limit(limit).all()


# =====================================================
# DASHBOARD
# =====================================================

@app.get("/suhu/dashboard/{device_id}", response_model=schemas.DashboardResponse, tags=["Dashboard"])
def get_dashboard(device_id: str, db: Session = Depends(get_db)):
    """Dashboard lengkap untuk satu device"""
    device = db.query(models.Device).filter(models.Device.device_id == device_id).first()
    if not device:
        raise HTTPException(404, "Device tidak ditemukan")

    # Data terkini
    latest = db.query(models.RawLog)\
        .filter(models.RawLog.device_id == device_id)\
        .order_by(models.RawLog.created_at.desc()).first()

    # Setting aktif
    active = db.query(models.UmurSetting).filter(
        models.UmurSetting.device_id == device_id,
        models.UmurSetting.is_active == True
    ).first()

    active_response = None
    if active:
        active_response = schemas.ActiveSettingResponse(
            umur_minggu=active.umur_minggu,
            setpoint_target=active.setpoint_target,
            activated_at=active.activated_at,
            hari_berjalan=(datetime.now() - active.activated_at).days
        )

    # Grafik hari ini (per jam)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    logs_hari_ini = db.query(models.RawLog).filter(
        models.RawLog.device_id == device_id,
        models.RawLog.created_at >= today
    ).all()

    grafik = {}
    for log in logs_hari_ini:
        jam = log.created_at.strftime("%H:00")
        if jam not in grafik:
            grafik[jam] = {"total": 0, "count": 0, "min": 999, "max": -999}
        grafik[jam]["total"] += log.temperature
        grafik[jam]["count"] += 1
        grafik[jam]["min"] = min(grafik[jam]["min"], log.temperature)
        grafik[jam]["max"] = max(grafik[jam]["max"], log.temperature)

    grafik_response = [
        schemas.GrafikSuhuResponse(
            jam=jam,
            suhu_rata_rata=round(data["total"] / data["count"], 1),
            suhu_min=round(data["min"], 1),
            suhu_max=round(data["max"], 1)
        )
        for jam, data in sorted(grafik.items())
    ]

    # Recent send logs
    recent_sends = db.query(models.SendLog)\
        .filter(models.SendLog.device_id == device_id)\
        .order_by(models.SendLog.sent_at.desc()).limit(5).all()

    return schemas.DashboardResponse(
        device=schemas.DeviceResponse.model_validate(device),
        current_temperature=latest.temperature if latest else None,
        current_setpoint=latest.setpoint if latest else None,
        current_setpoint_source=latest.setpoint_source if latest else None,
        heater_power=latest.heater_power if latest else None,
        status=latest.status if latest else None,
        condition=latest.condition if latest else None,
        active_setting=active_response,
        grafik_24jam=grafik_response,
        recent_send_logs=recent_sends
    )