import re

def extract_and_replace():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the style block
    match = re.search(r'<style>(.*?)</style>', content, flags=re.DOTALL)
    if not match:
        print("No style block found")
        return

    css_content = match.group(1)

    # Write to index.css
    with open('index.css', 'w', encoding='utf-8') as f:
        f.write(css_content)

    # Replace in index.html
    new_content = content[:match.start()] + '<link rel="stylesheet" href="/index.css" />' + content[match.end():]
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Success")

if __name__ == '__main__':
    extract_and_replace()
