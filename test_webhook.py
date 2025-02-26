import requests
import json

url = "https://webhook.site/836aad1e-0ef6-4dca-8b23-9bafc9530431"
headers = {"Content-Type": "application/json"}
data = {
    "message": "This is a test webhook from the server."
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.status_code)
print(response.json())
