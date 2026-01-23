from django import template
from django.utils.safestring import mark_safe
import html

register = template.Library()

COLOR_MAP = {
    "emerald": "bg-emerald-500/20 border-emerald-400/30 text-emerald-100",
    "amber": "bg-amber-500/20 border-amber-400/30 text-amber-100",
    "rose": "bg-rose-500/20 border-rose-400/30 text-rose-100",
    "sky": "bg-sky-500/20 border-sky-400/30 text-sky-100",
    "violet": "bg-violet-500/20 border-violet-400/30 text-violet-100",
}

@register.simple_tag
def highlight_arabic(example):
    text = example.arabic_text or ""
    text_esc = html.escape(text)

    marks = list(example.marks.all())
    if not marks:
        return mark_safe(text_esc)

    marks.sort(key=lambda m: (m.start, m.end))
    out = []
    i = 0

    for m in marks:
        s, e = m.start, m.end
        if s < i:
            continue
        out.append(text_esc[i:s])

        color = (m.tag.color if m.tag else "emerald")
        cls = COLOR_MAP.get(color, COLOR_MAP["emerald"])
        segment = text_esc[s:e]
        out.append(f'<span class="px-1 py-0.5 rounded-lg border {cls}">{segment}</span>')
        i = e

    out.append(text_esc[i:])
    return mark_safe("".join(out))


@register.filter
def auto_tajweed(text):
    """
    Automatic regex-based highlighting for basic Tajweed rules.
    Colors:
    - Amber: Ghunna (Nun/Meem Shadda)
    - Sky: Qalqala (Qtbjd + Sukun)
    - Rose: Madd (Madd sign ~ or Dagger Alif)
    """
    if not text:
        return ""
    
    import re

    # 1. Base cleanup (ensure we work on string)
    # We will use simple replacements. 
    # NOTE: Order matters!
    
    # CSS Classes
    c_amber = 'text-amber-400 bg-amber-500/10 rounded px-0.5'
    c_sky = 'text-sky-400 bg-sky-500/10 rounded px-0.5'
    c_rose = 'text-rose-400 bg-rose-500/10 rounded px-0.5'

    # Patterns
    
    # GHUNNA: Nun/Meem + Shadda ( \u0651 )
    # \u0646 = Nun, \u0645 = Meem
    # Regex: ([นม]\u0651) -> but in unicode 
    # Use explicit unicode for safety
    
    # Ghunna (Nun/Meem Shadda) -> Amber
    # Capture group 1: The letter + shadda
    text = re.sub(r'([\u0646\u0645]\u0651)', f'<span class="{c_amber}">\\1</span>', text)
    
    # QALQALA: (Qaf/Ta/Ba/Jim/Dal) + Sukun (\u0652)
    # \u0642=Qaf, \u0637=Ta(Taw), \u0628=Ba, \u062c=Jim, \u062f=Dal
    text = re.sub(r'([\u0642\u0637\u0628\u062c\u062f]\u0652)', f'<span class="{c_sky}">\\1</span>', text)
    
    # MADD: 
    # 1. Madd sign (\u0653) -> Rose
    text = re.sub(r'(\u0653)', f'<span class="{c_rose}">\\1</span>', text)
    
    # 2. Dagger Alif (\u0670) -> Rose
    text = re.sub(r'(\u0670)', f'<span class="{c_rose}">\\1</span>', text)
    
    return mark_safe(text)
