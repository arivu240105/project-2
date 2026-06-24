import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "llama-3.3-70b-specdec",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "temperature": 0.0,
    "stream": False
}

print("Testing with model: llama-3.3-70b-specdec")
response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

print("\nTesting with model: llama-3.3-70b-versatile")
payload["model"] = "llama-3.3-70b-versatile"
response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
