import os
import re

def fix_with_regex(path, pattern, replacement):
    if not os.path.exists(path):
        print(f"Not found: {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed: {path}")
    else:
        print(f"No match found in: {path}")

# Fix multiline tags: join {{ \n ... }} into {{ ... }}
# Pattern finds {{ followed by optional space, then newline, then optional space, then content, then }}
multiline_pattern = r'\{\{\s*\n\s*([^}]+)\s*\}\}'
multiline_replacement = r'{{\1}}'

fix_with_regex(r"d:\Work\arab\arab\templates\pages\home.html", multiline_pattern, multiline_replacement)
fix_with_regex(r"d:\Work\arab\arab\templates\pages\leagues.html", multiline_pattern, multiline_replacement)

# Fix spaced tags: { { -> {{ and } } -> }}
spacing_pattern1 = r'\{\s+\{'
spacing_replacement1 = r'{{'
spacing_pattern2 = r'\}\s+\}'
spacing_replacement2 = r'}}'

files_to_fix = [
    r"d:\Work\arab\arab\templates\tajweed\pro_drill.html",
    r"d:\Work\arab\arab\templates\practice\index.html",
    r"d:\Work\arab\arab\templates\pages\home.html",
    r"d:\Work\arab\arab\templates\pages\leagues.html"
]

for f in files_to_fix:
    fix_with_regex(f, spacing_pattern1, spacing_replacement1)
    fix_with_regex(f, spacing_pattern2, spacing_replacement2)

# Specific fix for the broken tag in practice/index.html
# {{ game.xp_total |default: 0 } \n  }
fix_with_regex(r"d:\Work\arab\arab\templates\practice\index.html", 
               r'\{\{\s*game\.xp_total\s*\|default:\s*0\s*\}\s*\n\s*\}', 
               '{{ game.xp_total|default:0 }}')

print("Emergency fixes complete.")
