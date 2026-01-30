
import requests
import json

GOOGLE_AI_API_KEY = 'AIzaSyDQwhqE2-3u5W-feLg3BU0N0SmIAfY6WJw'
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_AI_API_KEY}'

def test_raw_gemini():
    print("Testing RAW Gemini API...")
    payload = {
        'contents': [{
            'parts': [{'text': "Say Hello in Arabic"}]
        }]
    }
    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=15
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_raw_gemini()
