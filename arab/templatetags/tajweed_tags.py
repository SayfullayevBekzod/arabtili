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
