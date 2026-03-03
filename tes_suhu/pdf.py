import psycopg2
from fpdf import FPDF

# Koneksi ke database
conn = psycopg2.connect(
    host="localhost",
    database="appdb",
    user="abong",
    password="password"
)
cur = conn.cursor()

# Query data dari tabel monitorings
cur.execute("SELECT id, suhu, timestamp FROM monitorings ORDER BY id")
rows = cur.fetchall()

# Inisialisasi PDF
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

def header_table():
    pdf.set_font("Arial", "B", 12)
    pdf.cell(20, 10, "ID", 1, 0, "C")
    pdf.cell(30, 10, "Suhu", 1, 0, "C")
    pdf.cell(80, 10, "Timestamp", 1, 1, "C")

# Buat halaman dan header awal
pdf.add_page()
header_table()

pdf.set_font("Arial", "", 12)
line_height = 8

for i, row in enumerate(rows):
    if pdf.get_y() > 270:  # Kalau posisi vertikal mendekati bawah halaman, buat halaman baru
        pdf.add_page()
        header_table()
    pdf.cell(20, line_height, str(row[0]), 1)
    pdf.cell(30, line_height, str(row[1]), 1)
    pdf.cell(80, line_height, str(row[2]), 1)
    pdf.ln(line_height)

# Simpan PDF
pdf.output("laporan_monitorings1.pdf")

cur.close()
conn.close()

print("PDF laporan_monitorings.pdf berhasil dibuat!")