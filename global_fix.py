import os
import re
import django
import sys

# Configure Django
sys.path.append(r"d:\Work\arab")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Letter

def fix_templates():
    base_dir = r"d:\Work\arab\arab\templates"
    count = 0
    
    # Regex for multi-line {{ ... }}
    # Meaning: {{ followed by anything (including newlines) until }}
    # We want to collapse whitespace inside {{ }}
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".html"):
                continue
                
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 1. Fix {% elifa typo if exists
            if "{% elifa" in content:
                content = content.replace("{% elifa", "{% elif")
                print(f"Fixed elifa typo in {file}")

            # 2. Fix multi-line tags {{ \n ... }}
            # Pattern: {{ followed by capture group including newlines, then }}
            def replacer(match):
                inner = match.group(1)
                # Replace newlines and extra spaces with single space
                clean_inner = re.sub(r'\s+', ' ', inner).strip()
                return "{{" + " " + clean_inner + " " + "}}"

            # Match {{ ... }} spanning multiple lines
            # (?s) enables dot matching newline
            content = re.sub(r'\{\{(.*?)\}\}', replacer, content, flags=re.DOTALL)
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed tags in {file}")
                count += 1
                
    print(f"Total files fixed: {count}")

def check_letters():
    print("\nChecking Letter Data:")
    letters = Letter.objects.all()
    params = ['isolated', 'initial', 'medial', 'final', 'svg_path']
    
    for l in letters:
        issues = []
        for p in params:
            val = getattr(l, p)
            if not val or len(str(val)) < 5:
                # If standard form is missing, it might use arabic char, which is fine
                # But svg_path must be long
                if p == 'svg_path':
                    issues.append(f"Missing/Short SVG ({len(str(val)) if val else 0})")
        
        if issues:
            print(f"- {l.name}: {', '.join(issues)}")
            
    # Auto-fill missing SVG if possible (placeholder logic)
    # Note: We can't strictly generate SVG paths, but we can report them
    
if __name__ == '__main__':
    fix_templates()
    check_letters()
