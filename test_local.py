import requests
import json
from reportlab.pdfgen import canvas

# create a dummy pdf
c = canvas.Canvas("dummy.pdf")
c.drawString(100, 100, "This is a dummy Python Developer resume. Knows AWS and FastAPI.")
c.save()

url = "http://127.0.0.1:8000/api/analyze"
data = {"job_description": "We need a Python developer."}
files = {"resume": ("dummy.pdf", open("dummy.pdf", "rb"), "application/pdf")}

print("Sending POST request to local Uvicorn...")
try:
    response = requests.post(url, data=data, files=files, timeout=60)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Failed to call local API:", e)
