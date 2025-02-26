import requests
import json

url = "http://127.0.0.1:8080/v1/ffmpeg/compose"
headers = {"Content-Type": "application/json"}
data = {
    "inputs": [
        {
            "file_url": "https://example.com/input1.mp4",
            "options": [{"option": "-i"}]
        }
    ],
    "outputs": [
        {
            "options": [
                {"option": "-c:v", "argument": "libx264"},
                {"option": "-pix_fmt", "argument": "yuv420p"}
            ]
        }
    ],
    "webhook_url": "https://webhook.site/836aad1e-0ef6-4dca-8b23-9bafc9530431"
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.status_code)
print(response.json())
