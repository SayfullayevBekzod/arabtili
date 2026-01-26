"""Fix O'rtada position to use medial form"""
import re

filepath = r"d:\Work\arab\arab\templates\alphabet\practice.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the O'rtada section specifically and fix it
# Looking for the pattern after "O'rtada" with isolated
pattern = r"(O'rtada</div>\s+<div class=\"arabic-font text-5xl[^>]*>{{ )letter\.isolated(\|default:letter\.arabic }})"
replacement = r"\1letter.medial\2"

content = re.sub(pattern, replacement, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ O'rtada fixed to use medial form")
