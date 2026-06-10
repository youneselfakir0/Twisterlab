import os

files = [
    ("src/twisterlab/api/main.py", "temp_main.py"),
    ("index.html", "temp_index.html"),
    ("index.css", "temp_index.css"),
    ("src/twisterlab/agents/api/security.py", "temp_security.py")
]

for src, dst in files:
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"Fixed {dst}")
