from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo
import models
import schemas
from database import engine, get_db
import threading
from datetime import timezone, timedelta
from starlette.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_data(request: Request, db: Session = Depends(get_db)):
    data = db.query(models.Monitoring)\
        .order_by(models.Monitoring.timestamp.desc())\
        .limit(20)\
        .all()
    
    data = list(reversed(data))
    wib = timezone(timedelta(hours=7))
    for item in data:
        if item.timestamp.tzinfo is None:
            item.timestamp = item.timestamp.replace(tzinfo=timezone.utc)
        item.timestamp = item.timestamp.astimezone(wib)
        
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data
        }
    )

@app.post("/monitoring")
def create_monitoring(monitoring: schemas.MonitoringCreate, db: Session = Depends(get_db)):
    new_monitoring = models.Monitoring(
        suhu = monitoring.suhu,
        kelembapan = monitoring.kelembapan
    )

    db.add(new_monitoring)
    db.commit()
    db.refresh(new_monitoring)
    new_monitoring.timestamp = new_monitoring.timestamp.astimezone(
        ZoneInfo("Asia/Jakarta")
    )
    return new_monitoring

@app.get("/monitoring")
def get_monitoring(db: Session = Depends(get_db)):
    return db.query(models.Monitoring).all()


@app.delete("/monitoring/{monitoring_id}")
def delete_monitoring(monitoring_id: int, db: Session = Depends(get_db)):
        data = db.query(models.Monitoring).filter(models.Monitoring.id == monitoring_id).first()

        if not data:
            return {"error": "data tidak ditemukan"}
        
        db.delete(data)
        db.commit()

        return {"message": "berhasil dihapus"}