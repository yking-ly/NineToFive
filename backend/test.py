import requests
import base64
import mimetypes
import os

URL = "https://script.google.com/macros/s/AKfycbyV_2016LPBRF4jBzxVLi0LLCYAW6Hh1ET37KeEeF-JtyDe0oh9p0JOO26-g4TlpiSCzQ/exec"

def upload_any_file(file_path):
    if not os.path.exists(file_path):
        print("📁 File not found!")
        return

    # Automatically detect the mime type (e.g., application/pdf)
    mime_type, _ = mimetypes.guess_type(file_path)
    file_name = os.path.basename(file_path)

    with open(file_path, "rb") as file:
        file_data = base64.b64encode(file.read()).decode('utf-8')

    payload = {
        "file": file_data,
        "filename": file_name,
        "mimetype": mime_type or "application/octet-stream"
    }

    print(f"📤 Uploading {file_name}...")
    response = requests.post(URL, json=payload)

    if response.status_code == 200:
        res_json = response.json()
        print("✅ Upload Successful!")
        print(f"🔗 Drive Link: {res_json.get('driveUrl')}")
        print(f"🖼️ Thumbnail:  {res_json.get('lh3Thumbnail')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

# Example Usage:
upload_any_file("E:/Downloads/RalphCarvalho.pdf")