"""
Google AI (Gemini) integration for generating Arabic learning content.
"""
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import time
from django.core.cache import cache

from .models import UserGamification

GOOGLE_AI_API_KEY = 'AIzaSyDQwhqE2-3u5W-feLg3BU0N0SmIAfY6WJw'
# Try 2.0 Flash first, fallback to 1.5 Flash if needed
GEMINI_API_URL_2_0 = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_AI_API_KEY}'
GEMINI_API_URL_1_5 = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_AI_API_KEY}'


def call_gemini_api(prompt: str, retries=3, delay=1) -> str:
    """Call Google Gemini API with retries and exponential backoff for 429s."""
    
    # Check cache first to save quota
    cache_key = f"gemini_resp_{hash(prompt)}"
    cached_val = cache.get(cache_key)
    if cached_val:
        return cached_val

    for attempt in range(retries):
        try:
            # Alternate between 2.0 and 1.5 to maximize quota
            url = GEMINI_API_URL_2_0 if attempt % 2 == 0 else GEMINI_API_URL_1_5
            
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{
                        'parts': [{'text': prompt}]
                    }],
                    'generationConfig': {
                        'temperature': 0.7,
                        'maxOutputTokens': 2048,
                    }
                },
                timeout=30
            )
            
            if response.status_code == 429:
                print(f"Gemini 429 (Quota Exceeded) - Attempt {attempt+1}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2 # Exponential backoff
                continue
                
            response.raise_for_status()
            data = response.json()
            
            # Extract text from response
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    text = candidate['content']['parts'][0].get('text', '')
                    if text:
                        # Cache for 1 hour
                        cache.set(cache_key, text, 3600)
                        return text
            return ''
        except Exception as e:
            print(f"Gemini API error (Attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                return ''
    return ''


def parse_json_from_response(text: str) -> dict:
    """Extract JSON from Gemini response text, handling markdown code blocks."""
    try:
        # Remove markdown code blocks if present
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
            
        # Try to find JSON in the response
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
        
        # Try array format
        start = text.find('[')
        end = text.rfind(']') + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Text was: {text[:100]}...")
    return {}


@login_required
@require_http_methods(["GET"])
def generate_exam_questions(request):
    """Generate exam questions using AI."""
    # Get user level from gamification if not in query
    level = request.GET.get('level')
    if not level:
        try:
            gamification = UserGamification.objects.get(user=request.user)
            level = str(gamification.level)
        except UserGamification.DoesNotExist:
            level = '1'
            
    count = int(request.GET.get('count', '10'))
    
    prompt = f"""
    Arab tilini o'rganuvchilar uchun {count} ta imtihon savoli yarating. Daraja: {level}
    
    Savol turlari:
    1. multiple_choice - 4 ta variant, to'g'ri javob indeksi (0-3)
    2. listening - Tinglab javob berish (4 ta arabcha variant)
    3. matching - Harflarni talaffuz bilan moslashtirish
    4. writing - Harf yozish (faqat instruction va arabic)
    5. pronunciation - Talaffuz qilish (faqat instruction va arabic)
    
    JSON formatda javob bering:
    {{
        "questions": [
            {{
                "type": "multiple_choice",
                "instruction": "Savolning o'zbekcha izohi",
                "arabic": "عربي",
                "options": ["A variant", "B variant", "C variant", "D variant"],
                "correct": 0
            }},
            {{
                "type": "listening",
                "instruction": "Nimani eshitdingiz?",
                "options": ["أ", "ب", "ت", "ث"],
                "correct": 1
            }},
            {{
                "type": "matching",
                "instruction": "Harflarni moslang",
                "leftItems": ["أ", "ب", "ت"],
                "rightItems": ["Ta", "Alif", "Ba"],
                "correctPairs": [[0, 1], [1, 2], [2, 0]]
            }},
            {{
                "type": "writing",
                "instruction": "Bu harfni yozing",
                "arabic": "ج"
            }},
            {{
                "type": "pronunciation",
                "instruction": "Bu so'zni o'qing",
                "arabic": "مَرْحَبًا"
            }}
        ]
    }}
    
    Faqat JSON qaytaring, boshqa matn yo'q.
    """
    
    response_text = call_gemini_api(prompt)
    data = parse_json_from_response(response_text)
    
    if data and 'questions' in data:
        return JsonResponse({'success': True, 'questions': data['questions']})
    
    # Fallback to default questions
    return JsonResponse({
        'success': False, 
        'message': 'AI limitga yetdi yoki xatolik yuz berdi. Iltimos keyinroq urinib ko\'ring.', 
        'questions': []
    })


@login_required
@require_http_methods(["GET"])
def generate_quiz_questions(request):
    """Generate daily quiz questions using AI."""
    count = int(request.GET.get('count', '5'))
    
    prompt = f"""
    Arab tilini o'rganuvchilar uchun {count} ta oddiy test savoli yarating.
    Har bir savol:
    - O'zbekcha savol
    - 4 ta variant (arabcha va o'zbekcha aralash)
    - To'g'ri javob indeksi (0-3)
    
    JSON formatda:
    {{
        "questions": [
            {{
                "question": "Savol matni",
                "options": ["Variant A", "Variant B", "Variant C", "Variant D"],
                "correct": 0
            }}
        ]
    }}
    
    Savollar quyidagi mavzulardan bo'lsin:
    - Harflar nomi
    - So'z tarjimasi
    - Salomlashish iboralari
    - Rasqamlar
    - Ranglar
    
    Faqat JSON qaytaring.
    """
    
    response_text = call_gemini_api(prompt)
    data = parse_json_from_response(response_text)
    
    if data and 'questions' in data:
        return JsonResponse({'success': True, 'questions': data['questions']})
    
    return JsonResponse({
        'success': False, 
        'message': 'AI band. Standart savollar yuklanmoqda...',
        'questions': []
    })


@login_required
@require_http_methods(["GET"])
def generate_letter_examples(request):
    """Generate example words for an Arabic letter."""
    letter = request.GET.get('letter', 'أ')
    letter_name = request.GET.get('name', 'Alif')
    
    prompt = f"""
    Arab harfi "{letter}" ({letter_name}) uchun 5 ta misol so'z va iborani yarating.
    
    Har bir misol uchun:
    - Arabcha so'z (harakat bilan)
    - Transliteratsiya (lotin harflarida)
    - O'zbekcha tarjima
    - Qaysi o'rinda harf kelishi (bosh, o'rta, oxir)
    
    JSON formatda:
    {{
        "letter": "{letter}",
        "examples": [
            {{
                "arabic": "كِتَابٌ",
                "transliteration": "kitaabun",
                "meaning": "kitob",
                "position": "o'rta"
            }}
        ],
        "tip": "Bu harfni to'g'ri talaffuz qilish uchun maslahat"
    }}
    
    Faqat JSON qaytaring.
    """
    
    response_text = call_gemini_api(prompt)
    data = parse_json_from_response(response_text)
    
    if data and 'examples' in data:
        return JsonResponse({'success': True, **data})
    
    return JsonResponse({'success': False, 'examples': []})


@login_required
@require_http_methods(["GET"])
def generate_vocabulary(request):
    """Generate vocabulary words for a topic."""
    topic = request.GET.get('topic', 'umumiy')
    count = int(request.GET.get('count', '10'))
    
    prompt = f"""
    Arab tili lug'ati uchun "{topic}" mavzusida {count} ta so'z yarating.
    
    Har bir so'z uchun:
    - Arabcha (harakat bilan)
    - Transliteratsiya
    - O'zbekcha ma'no
    - Ruscha ma'no
    - Qo'shimcha izoh
    
    JSON formatda:
    {{
        "topic": "{topic}",
        "words": [
            {{
                "arabic": "كِتَابٌ",
                "transliteration": "kitaabun",
                "meaning_uz": "kitob",
                "meaning_ru": "книга",
                "note": "Ism, erkak jinsi"
            }}
        ]
    }}
    
    Mavzular: oila, maktab, uy, ovqat, hayvonlar, ranglar, raqamlar, salomlashish, savdo, safar
    
    Faqat JSON qaytaring.
    """
    
    response_text = call_gemini_api(prompt)
    data = parse_json_from_response(response_text)
    
    if data and 'words' in data:
        return JsonResponse({'success': True, **data})
    
    return JsonResponse({'success': False, 'words': []})


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat(request):
    """General AI chat for learning assistance."""
    try:
        body = json.loads(request.body)
        user_message = body.get('message', '')
        
        if not user_message:
            return JsonResponse({'success': False, 'message': 'Xabar bo\'sh'})
        
        prompt = f"""
        Siz arab tilini o'rgatuvchi AI yordamchisiz. Foydalanuvchi savoliga javob bering.
        Javobingiz qisqa, tushunarli va foydali bo'lsin.
        Agar arab so'zlari bo'lsa, transliteratsiya va tarjima qo'shing.
        
        Foydalanuvchi savoli: {user_message}
        
        O'zbekcha javob bering.
        """
        
        response_text = call_gemini_api(prompt)
        
        if response_text:
            return JsonResponse({'success': True, 'response': response_text})
        
        return JsonResponse({'success': False, 'message': 'AI javob bermadi'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
