# reset_db.py
from database import engine, Base
import models

print("🗑️  Menghapus semua tabel...")
Base.metadata.drop_all(bind=engine)

print("✨ Membuat ulang tabel dengan struktur terbaru...")
Base.metadata.create_all(bind=engine)

print("✅ Database berhasil direset!")