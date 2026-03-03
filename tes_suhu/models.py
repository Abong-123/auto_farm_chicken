from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from database import Base

class Monitoring(Base):
    __tablename__ = "monitorings"

    id = Column(Integer, primary_key=True, index=True)
    suhu = Column(Float)
    kelembapan = Column(Float)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )