# coding: utf-8
"""
Import data dari data.json ke endpoint /sampling/input-data
"""

import requests
import json
import time

API_URL = "http://127.0.0.1:8000"
ENDPOINT = "/sampling/input-data"
JSON_FILE = "data.json"

def load_json_data():
    """Load data dari file JSON"""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"📁 Load {len(data)} data dari {JSON_FILE}")
    return data

def import_to_server(data_list):
    """Import data ke server via API"""
    print("\n🚀 MULAI IMPORT DATA KE SERVER")
    print("-" * 60)
    
    success = 0
    failed = 0
    
    for idx, item in enumerate(data_list, 1):
        # Siapkan payload hanya dengan field yang diperlukan
        payload = {
            "time_range": item["time_range"],
            "point_id": item["point_id"],
            "base_temperature": item["base_temperature"],
            "data_1": item["data_1"],
            "data_2": item["data_2"],
            "data_3": item["data_3"],
            "data_4": item["data_4"],
            "data_5": item["data_5"],
            "data_6": item["data_6"],
            "notes": item.get("notes", "")
        }
        
        try:
            response = requests.post(
                f"{API_URL}{ENDPOINT}",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                success += 1
                print(f"  ✅ [{idx:3d}/{len(data_list)}] {item['time_range']} - {item['point_id']}")
            else:
                failed += 1
                print(f"  ❌ [{idx:3d}/{len(data_list)}] Gagal: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n❌ ERROR: Server tidak merespon!")
            print(f"   Pastikan server FastAPI berjalan di {API_URL}")
            return success, failed
        
        except Exception as e:
            failed += 1
            print(f"  ❌ [{idx:3d}/{len(data_list)}] Error: {str(e)[:50]}")
        
        # Delay kecil
        time.sleep(0.05)
    
    return success, failed

def clear_existing_data():
    """Hapus semua data yang ada di server"""
    print("\n🗑️  Menghapus data lama di server...")
    try:
        response = requests.delete(f"{API_URL}/sampling/clear-all", timeout=10)
        if response.status_code == 200:
            print("✅ Data lama berhasil dihapus")
            return True
        else:
            print(f"⚠️  Gagal hapus data: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("📦 IMPORT DATA SAMPLING KE SERVER")
    print("=" * 60)
    
    # Cek server
    try:
        requests.get(f"{API_URL}/docs", timeout=2)
        print("✅ Server FastAPI berjalan")
    except:
        print("❌ Server FastAPI TIDAK berjalan!")
        print("   Jalankan: uvicorn main:app --reload")
        exit(1)
    
    # Load data dari JSON
    try:
        data_list = load_json_data()
    except FileNotFoundError:
        print(f"❌ File {JSON_FILE} tidak ditemukan!")
        print(f"   Pastikan file {JSON_FILE} ada di folder yang sama")
        exit(1)
    
    # Tanya aksi
    print("\n📋 Opsi:")
    print("   1. Import data (tanpa hapus data lama)")
    print("   2. Hapus data lama, lalu import ulang")
    print("   3. Batal")
    
    choice = input("\nPilih opsi (1/2/3): ")
    
    if choice == "1":
        success, failed = import_to_server(data_list)
    elif choice == "2":
        confirm = input("⚠️  Yakin akan menghapus semua data yang ada? (y/n): ")
        if confirm.lower() == 'y':
            clear_existing_data()
            print("\n⏳ Tunggu 1 detik...")
            time.sleep(1)
            success, failed = import_to_server(data_list)
        else:
            print("❌ Dibatalkan")
            exit(0)
    else:
        print("❌ Dibatalkan")
        exit(0)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY IMPORT")
    print("=" * 60)
    print(f"   Total data: {len(data_list)}")
    print(f"   ✅ Berhasil: {success}")
    print(f"   ❌ Gagal: {failed}")
    
    if success == len(data_list):
        print("\n🎉 SEMUA DATA BERHASIL DIIMPORT!")