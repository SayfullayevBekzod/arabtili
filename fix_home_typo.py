import os

# 1. Fix home.html typo
home_path = r"d:\Work\arab\arab\templates\pages\home.html"
with open(home_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix broken tag split
if "{% elifa" in content:
    content = content.replace("{% elifa", "{% elif")
    print("Fixed elifa typo.")

# Fix likely split lines that caused it (aggressive join)
# Searching for the specific broken pattern seen in screenshots
broken_pattern = "{% elif\n            mp.mission.mission_type"
fixed_pattern = "{% elif mp.mission.mission_type"
if broken_pattern in content:
    content = content.replace(broken_pattern, fixed_pattern)
    print("Fixed split elif tag.")

with open(home_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Home page fixed.")
