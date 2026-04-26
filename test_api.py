import requests
import time
import json

GENSARA_API_KEY = "gk_live_ATCc1WwXYVPKt2nkiM0_8ZzWBSG0LrGwPI6PmQyeJtA"
GENSARA_API_URL = "https://api.gensaralabs.com/api/chat"
PROMPTOS_ID = "0f28cd6c-fe6b-11f0-9b23-baae711029b4"

headers = {
    "Authorization": f"Bearer {GENSARA_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "query": "Say hello world.",
    "promptos_id": PROMPTOS_ID,
    "temperature": 0.2
}

start = time.time()
print("Sending request...")
try:
    response = requests.post(GENSARA_API_URL, headers=headers, json=payload, timeout=60)
    end = time.time()
    print(f"Status Code: {response.status_code}")
    print(f"Time Taken: {end - start:.2f} seconds")
    try:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Raw text:", response.text)
except Exception as e:
    print("Request failed:", e)
