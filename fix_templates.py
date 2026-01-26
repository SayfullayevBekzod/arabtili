# Script to fix remaining template tags

import os
import re

BASE = r"d:\Work\arab\arab\templates"

fixes = [
    # practice.html - Alohida
    {
        "file": os.path.join(BASE, "alphabet", "practice.html"),
        "old": """        <div class="arabic-font text-5xl font-black text-white group-hover:scale-110 transition duration-500">{{
          letter.isolated|default:letter.arabic }}</div>""",
        "new": """        <div class="arabic-font text-5xl font-black text-white group-hover:scale-110 transition duration-500">{{ letter.isolated|default:letter.arabic }}</div>"""
    },
    # practice.html - O'rtada (change to medial)
    {
        "file": os.path.join(BASE, "alphabet", "practice.html"),
        "old": """        <div class="arabic-font text-5xl font-black text-white group-hover:scale-110 transition duration-500">{{
          letter.isolated|default:letter.arabic }}</div>""",
        "new": """        <div class="arabic-font text-5xl font-black text-white group-hover:scale-110 transition duration-500">{{ letter.medial|default:letter.arabic }}</div>""",
        "index": 1  # Second occurrence
    }
]

for fix in fixes:
    filepath = fix["file"]
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "index" in fix:
        # Replace nth occurrence
        parts = content.split(fix["old"])
        if len(parts) > fix["index"] + 1:
            parts[fix["index"]] += fix["new"]
            content = fix["old"].join(parts[:fix["index"]]) + fix["old"].join(parts[fix["index"]+1:])
    else:
        content = content.replace(fix["old"], fix["new"])
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

print("All template tags fixed!")
