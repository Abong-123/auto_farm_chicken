import requests
import random
import time

API_URL = "http://localhost:8000/monitoring"

while True:
    data = {
        "suhu": round(random.uniform(28, 35), 2),
        "kelembapan": round(random.uniform(60, 85), 2)
    }

    try:
        r = requests.post(API_URL, json=data)
        print("Sent:", data, "| Status:", r.status_code)
    except Exception as e:
        print("Error:", e)

    time.sleep(600)