import re
import os

def apply_apple_theme():
    # Check if index.css exists
    css_path = 'index.css'
    if not os.path.exists(css_path):
        print(f"Error: {css_path} not found")
        return

    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add Inter Font Import if not present
    if "fonts.googleapis.com/css2?family=Inter" not in content:
        content = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');\n" + content

    # REPLACEMENTS
    replaces = [
        # Variables
        (r'--c0: #020409;', '--c0: #000000;'),
        (r'--c1: #070a14;', '--c1: #1c1c1e;'),
        (r'--cyan: #00d4ff;', '--cyan: #0a84ff;'),
        (r'--purple: #8b5cf6;', '--purple: #5e5ce6;'),
        (r'--green: #10b981;', '--green: #30d158;'),
        (r'--red: #ef4444;', '--red: #ff453a;'),
        (r'--orange: #f97316;', '--orange: #ff9f0a;'),
        (r'--yellow: #eab308;', '--yellow: #ffd60a;'),
        (r'--t1: rgba\(255, 255, 255, 0\.93\);', '--t1: rgba(255, 255, 255, 0.96);'),
        (r'--t2: rgba\(255, 255, 255, 0\.55\);', '--t2: rgba(235, 235, 245, 0.6);'),
        (r'--t3: rgba\(255, 255, 255, 0\.28\);', '--t3: rgba(235, 235, 245, 0.3);'),
        (r'--glass: rgba\(8, 12, 24, 0\.88\);', '--glass: rgba(28, 28, 30, 0.7);'),
        (r'--border: rgba\(255, 255, 255, 0\.07\);', '--border: rgba(255, 255, 255, 0.1);'),
        (r'--sans: .*?;', '--sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;'),
        
        # Border Radius Unification
        (r'border-radius: 12px;', 'border-radius: 14px;'),
        (r'border-radius: 14px;', 'border-radius: 16px;'), # Over panel border radiuses
        
        # Apple Specific Adjustments
        (r'background: rgba\(2, 4, 9, 0\.97\);', 'background: rgba(28, 28, 30, 0.65);'),
        (r'backdrop-filter: blur\(20px\);', 'backdrop-filter: saturate(180%) blur(20px);'),
        (r'backdrop-filter: blur\(12px\);', 'backdrop-filter: saturate(180%) blur(20px);'),
        
        # Sidebar Color
        (r'background: rgba\(3, 5, 12, 0\.98\);', 'background: rgba(24, 24, 26, 0.95);'),
        
        # Buttons Style (Pill shape)
        (r'\.btn \{\s*padding: 7px 14px;\s*border-radius: 7px;', '.btn {\n  padding: 6px 16px;\n  border-radius: 99px;'),
        
        # Shadow adjustments (removing neon, switching to soft black shadows)
        (r'box-shadow: 0 4px 24px rgba\(0, 0, 0, 0\.5\);', 'box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);'),
        
        # Remove aggressive outlines/gradients on logo and loader
        (r'background: linear-gradient\(135deg, var\(--cyan\), var\(--purple\)\);', 'background: var(--cyan);'), # Solid colors over gradients
        (r'background: linear-gradient\(90deg, var\(--cyan\), var\(--purple\)\);', 'background: var(--cyan);'),
        (r'background: linear-gradient\(90deg, var\(--purple\), #60a5fa\);', 'background: var(--purple);'),
        (r'background: linear-gradient\(90deg, var\(--green\), var\(--cyan\)\);', 'background: var(--green);'),
        (r'background: linear-gradient\(90deg, var\(--orange\), var\(--yellow\)\);', 'background: var(--orange);'),
        
        # Remove top gradients from cards
        (r'\.kcard::before \{.*?\}', ''),
    ]

    for old, new in replaces:
        content = re.sub(old, new, content, flags=re.DOTALL)

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully applied Apple Theme to {css_path}")

if __name__ == '__main__':
    apply_apple_theme()
