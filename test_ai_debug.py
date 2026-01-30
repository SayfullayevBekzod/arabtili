
import os
import django
import sys

# Setup Django
sys.path.append('d:\\Work\\arab')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.ai_service import call_gemini_api, parse_json_from_response

def test_ai():
    print("Testing Gemini API...")
    prompt = "Arab tilida 'Salom' so'zining tarjimasini JSON formatda bersangiz. Faqat JSON: {'word': '...', 'translation': '...'}"
    response = call_gemini_api(prompt)
    print(f"Raw Response: {response}")
    
    if not response:
        print("FAIL: No response from Gemini.")
        return
        
    data = parse_json_from_response(response)
    print(f"Parsed Data: {data}")
    
    if data:
        print("SUCCESS: API and Parser are working.")
    else:
        print("FAIL: Could not parse JSON.")

if __name__ == "__main__":
    test_ai()
