# bulk_insert_sampling.py
import requests
import json
import time

# Konfigurasi
API_URL = "http://127.0.0.1:8000"
ENDPOINT = "/sampling/input-data"

# Data JSON yang akan diinput (cukup copy dari array JSON Anda)
data_list = [
    {
        "time_range": "00-06",
        "point_id": "P-1",
        "base_temperature": 24.4,
        "data_1": 25.8,
        "data_2": 25.8,
        "data_3": 25.3,
        "data_4": 25.8,
        "data_5": 25.7,
        "data_6": 25.8,
        "notes": "titik-1"
    },
    {
        "time_range": "00-06",
        "point_id": "P-2",
        "base_temperature": 24.4,
        "data_1": 29.2,
        "data_2": 29.2,
        "data_3": 29.1,
        "data_4": 29.3,
        "data_5": 29.2,
        "data_6": 30.2,
        "notes": "titik-2"
    },
    {
        "time_range": "00-06",
        "point_id": "P-3",
        "base_temperature": 24.5,
        "data_1": 29.9,
        "data_2": 25.5,
        "data_3": 25.5,
        "data_4": 25.5,
        "data_5": 25.5,
        "data_6": 25.8,
        "notes": "titik-3"
    },
    {
        "time_range": "00-06",
        "point_id": "P-4",
        "base_temperature": 24.4,
        "data_1": 29.3,
        "data_2": 29.4,
        "data_3": 30.1,
        "data_4": 29.9,
        "data_5": 30.2,
        "data_6": 29.3,
        "notes": "titik-4"
    },
    {
        "time_range": "00-06",
        "point_id": "P-5",
        "base_temperature": 24.5,
        "data_1": 29.5,
        "data_2": 29.5,
        "data_3": 29.5,
        "data_4": 29.5,
        "data_5": 30.5,
        "data_6": 29.4,
        "notes": "titik-5"
    },
    {
        "time_range": "06-09",
        "point_id": "P-1",
        "base_temperature": 26.6,
        "data_1": 28.8,
        "data_2": 28.8,
        "data_3": 28.8,
        "data_4": 28.8,
        "data_5": 28.8,
        "data_6": 28.8,
        "notes": "titik-1"
    },
    {
        "time_range": "06-09",
        "point_id": "P-2",
        "base_temperature": 27.3,
        "data_1": 28.8,
        "data_2": 28.6,
        "data_3": 28.6,
        "data_4": 27.4,
        "data_5": 28.6,
        "data_6": 29,
        "notes": "titik-2"
    },
    {
        "time_range": "06-09",
        "point_id": "P-3",
        "base_temperature": 26.3,
        "data_1": 28.3,
        "data_2": 28.1,
        "data_3": 28,
        "data_4": 28.1,
        "data_5": 28,
        "data_6": 28.3,
        "notes": "titik-3"
    },
    {
        "time_range": "06-09",
        "point_id": "P-4",
        "base_temperature": 26.5,
        "data_1": 30.4,
        "data_2": 30.6,
        "data_3": 28.8,
        "data_4": 28.8,
        "data_5": 28.8,
        "data_6": 30.5,
        "notes": "titik-4"
    },
    {
        "time_range": "06-09",
        "point_id": "P-5",
        "base_temperature": 29.2,
        "data_1": 31.5,
        "data_2": 30.6,
        "data_3": 31.4,
        "data_4": 30.4,
        "data_5": 30.4,
        "data_6": 30.5,
        "notes": "titik-5"
    },
    {
        "time_range": "09-12",
        "point_id": "P-1",
        "base_temperature": 29.2,
        "data_1": 30.9,
        "data_2": 31.5,
        "data_3": 30.5,
        "data_4": 30.5,
        "data_5": 32.1,
        "data_6": 32.1,
        "notes": "titik-1"
    },
    {
        "time_range": "09-12",
        "point_id": "P-2",
        "base_temperature": 29.2,
        "data_1": 32.1,
        "data_2": 32.1,
        "data_3": 32.2,
        "data_4": 31.7,
        "data_5": 32.9,
        "data_6": 32.3,
        "notes": "titik-2"
    },
    {
        "time_range": "09-12",
        "point_id": "P-3",
        "base_temperature": 30.4,
        "data_1": 31,
        "data_2": 31.7,
        "data_3": 31.7,
        "data_4": 31.7,
        "data_5": 31.8,
        "data_6": 31.7,
        "notes": "titik-3"
    },
    {
        "time_range": "09-12",
        "point_id": "P-4",
        "base_temperature": 29.3,
        "data_1": 31.3,
        "data_2": 31.3,
        "data_3": 31.4,
        "data_4": 31.2,
        "data_5": 31.3,
        "data_6": 31.2,
        "notes": "titik-4"
    },
    {
        "time_range": "09-12",
        "point_id": "P-5",
        "base_temperature": 30.4,
        "data_1": 32,
        "data_2": 32.1,
        "data_3": 32.1,
        "data_4": 31.9,
        "data_5": 32,
        "data_6": 32.1,
        "notes": "titik-5"
    },
    {
        "time_range": "12-15",
        "point_id": "P-1",
        "base_temperature": 34.8,
        "data_1": 36.4,
        "data_2": 36.4,
        "data_3": 36.4,
        "data_4": 36,
        "data_5": 36.3,
        "data_6": 35,
        "notes": "titik-1"
    },
    {
        "time_range": "12-15",
        "point_id": "P-2",
        "base_temperature": 35,
        "data_1": 35.9,
        "data_2": 35.8,
        "data_3": 35.7,
        "data_4": 35.8,
        "data_5": 35.7,
        "data_6": 35.1,
        "notes": "titik-2"
    },
    {
        "time_range": "12-15",
        "point_id": "P-3",
        "base_temperature": 35.1,
        "data_1": 35.7,
        "data_2": 35.7,
        "data_3": 35.7,
        "data_4": 35.6,
        "data_5": 35.6,
        "data_6": 35.6,
        "notes": "titik-3"
    },
    {
        "time_range": "12-15",
        "point_id": "P-4",
        "base_temperature": 35.2,
        "data_1": 35.9,
        "data_2": 35.9,
        "data_3": 35.6,
        "data_4": 35.9,
        "data_5": 35.7,
        "data_6": 35.7,
        "notes": "titik-4"
    },
    {
        "time_range": "12-15",
        "point_id": "P-5",
        "base_temperature": 35.2,
        "data_1": 36.4,
        "data_2": 36.3,
        "data_3": 36.3,
        "data_4": 36.3,
        "data_5": 36.1,
        "data_6": 35.6,
        "notes": "titik-5"
    },
    {
        "time_range": "15-18",
        "point_id": "P-1",
        "base_temperature": 29.4,
        "data_1": 31.2,
        "data_2": 31,
        "data_3": 30.5,
        "data_4": 31,
        "data_5": 30.4,
        "data_6": 31.1,
        "notes": "titik-1"
    },
    {
        "time_range": "15-18",
        "point_id": "P-2",
        "base_temperature": 29.3,
        "data_1": 31.8,
        "data_2": 31.5,
        "data_3": 31.6,
        "data_4": 31.2,
        "data_5": 31.1,
        "data_6": 31.3,
        "notes": "titik-2"
    },
    {
        "time_range": "15-18",
        "point_id": "P-3",
        "base_temperature": 29.3,
        "data_1": 29.6,
        "data_2": 30.9,
        "data_3": 29.6,
        "data_4": 30.7,
        "data_5": 30.8,
        "data_6": 30,
        "notes": "titik-3"
    },
    {
        "time_range": "15-18",
        "point_id": "P-4",
        "base_temperature": 29.4,
        "data_1": 30.4,
        "data_2": 30.3,
        "data_3": 30.2,
        "data_4": 30.4,
        "data_5": 30.4,
        "data_6": 29.9,
        "notes": "titik-4"
    },
    {
        "time_range": "15-18",
        "point_id": "P-5",
        "base_temperature": 29.4,
        "data_1": 30.7,
        "data_2": 30.7,
        "data_3": 30.9,
        "data_4": 30.9,
        "data_5": 30.5,
        "data_6": 30.9,
        "notes": "titik-5"
    },
    {
        "time_range": "18-00",
        "point_id": "P-1",
        "base_temperature": 29.5,
        "data_1": 29.6,
        "data_2": 29.8,
        "data_3": 29.8,
        "data_4": 29.8,
        "data_5": 29.7,
        "data_6": 29.8,
        "notes": "titik-1"
    },
    {
        "time_range": "18-00",
        "point_id": "P-2",
        "base_temperature": 29.6,
        "data_1": 30.7,
        "data_2": 30.5,
        "data_3": 30.5,
        "data_4": 30.9,
        "data_5": 30.9,
        "data_6": 30.4,
        "notes": "titik-2"
    },
    {
        "time_range": "18-00",
        "point_id": "P-3",
        "base_temperature": 29.6,
        "data_1": 30.6,
        "data_2": 30.4,
        "data_3": 30.4,
        "data_4": 30.2,
        "data_5": 30.3,
        "data_6": 29.8,
        "notes": "titik-3"
    },
    {
        "time_range": "18-00",
        "point_id": "P-4",
        "base_temperature": 29.6,
        "data_1": 30.2,
        "data_2": 30.3,
        "data_3": 30.5,
        "data_4": 30.5,
        "data_5": 30.6,
        "data_6": 30.7,
        "notes": "titik-4"
    },
    {
        "time_range": "18-00",
        "point_id": "P-5",
        "base_temperature": 29.6,
        "data_1": 31.3,
        "data_2": 30.9,
        "data_3": 31,
        "data_4": 31.1,
        "data_5": 31.2,
        "data_6": 31.1,
        "notes": "titik-5"
    }
]

def insert_sampling_data(data_list):
    """Insert multiple sampling data ke server"""
    
    print(f"íº€ Memulai insert {len(data_list)} data ke {API_URL}{ENDPOINT}")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    failed_items = []
    
    for idx, data in enumerate(data_list, 1):
        try:
            # Hapus field yang tidak diperlukan untuk POST (id, avg_heater_temp, delta_temperature, sampling_time)
            clean_data = {
                "time_range": data["time_range"],
                "point_id": data["point_id"],
                "base_temperature": data["base_temperature"],
                "data_1": data["data_1"],
                "data_2": data["data_2"],
                "data_3": data["data_3"],
                "data_4": data["data_4"],
                "data_5": data["data_5"],
                "data_6": data["data_6"],
                "notes": data.get("notes", "")
            }
            
            response = requests.post(
                f"{API_URL}{ENDPOINT}",
                json=clean_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"âœ… [{idx}/{len(data_list)}] Success: {data['time_range']} - {data['point_id']}")
            else:
                failed_count += 1
                failed_items.append({
                    "data": data,
                    "status": response.status_code,
                    "error": response.text
                })
                print(f"âŒ [{idx}/{len(data_list)}] Failed: {data['time_range']} - {data['point_id']} (HTTP {response.status_code})")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.05)
            
        except Exception as e:
            failed_count += 1
            failed_items.append({
                "data": data,
                "error": str(e)
            })
            print(f"âŒ [{idx}/{len(data_list)}] Error: {data['time_range']} - {data['point_id']} - {str(e)}")
    
    print("=" * 60)
    print(f"\ní³Š SUMMARY:")
    print(f"   Total data: {len(data_list)}")
    print(f"   âœ… Success: {success_count}")
    print(f"   âŒ Failed: {failed_count}")
    
    if failed_items:
        print(f"\nâš ï¸  Failed items:")
        for item in failed_items[:5]:  # Show first 5 failures
            print(f"   - {item['data'].get('time_range')} {item['data'].get('point_id')}: {item.get('error', 'Unknown error')}")
    
    return success_count, failed_count, failed_items


if __name__ == "__main__":
    print("í³¦ BULK INSERT SAMPLING DATA")
    print("=" * 60)
    
    # First, check if server is running
    try:
        response = requests.get(f"{API_URL}/docs", timeout=2)
        print("âœ… Server is running")
    except requests.exceptions.ConnectionError:
        print("âŒ Server is not running! Please start the server first:")
        print("   uvicorn main:app --reload")
        exit(1)
    
    # Ask for confirmation
    print(f"\nâš ï¸  Akan menginsert {len(data_list)} data ke database.")
    confirm = input("Lanjutkan? (y/n): ")
    
    if confirm.lower() == 'y':
        insert_sampling_data(data_list)
    else:
        print("âŒ Dibatalkan.")
