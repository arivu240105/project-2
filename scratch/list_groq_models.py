import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    models = response.json().get("data", [])
    print("Available Groq Models:")
    for model in sorted(models, key=lambda x: x["id"]):
        print(f"- {model['id']} (owned by: {model['owned_by']})")
except Exception as e:
    print(f"Error listing Groq models: {e}")
