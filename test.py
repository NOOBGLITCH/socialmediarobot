import os
import requests

API_KEY = os.getenv("GEMINI_API_KEY")  # export GEMINI_API_KEY="AIza..."
MODEL = "gemini-2.5-flash-lite"

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not set. Please run: export GEMINI_API_KEY=your_key")

URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

print(f"✅ Connected to {MODEL}. Type your messages below. (Ctrl+C to quit)\n")

while True:
    try:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        payload = {
            "contents": [
                {"parts": [{"text": user_input}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500
            }
        }

        resp = requests.post(URL, json=payload, headers={"Content-Type": "application/json"})
        if resp.status_code != 200:
            print(f"❌ Error {resp.status_code}: {resp.text}")
            continue

        data = resp.json()
        # Extract model reply
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"Gemini: {text}\n")
        except Exception as e:
            print("⚠️ Could not parse response:", data)

    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        break