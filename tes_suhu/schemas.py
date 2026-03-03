from pydantic import BaseModel

class MonitoringCreate(BaseModel):
    suhu: float
    kelembapan: float