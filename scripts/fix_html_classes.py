import re

def fix_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace the <style> block with <link>
    content = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="/index.css" />', content, flags=re.DOTALL)

    replacements = [
        # IDs
        (r'id="shell"', 'id="app"'),
        (r'id="top"', 'id="topbar"'),
        (r'id="side"', 'id="sidebar"'),
        # Classes
        (r'\blogo\b', 'topbar-logo'),
        (r'\blogo-name\b', 'logo-text'),
        (r'\blogo-ver\b', 'logo-version'),
        (r'\btop-stat\b', 'topbar-status'),
        (r'\btop-clock\b', 'topbar-time'),
        (r'\bni\b', 'nav-item'),
        (r'\bon\b', 'active'), # context-sensitive? Yes, button.ni.on -> nav-item active
        (r'\bic\b', 'nav-icon'),
        (r'\bnsec\b', 'nav-section'),
        (r'\bsfooter\b', 'sidebar-footer'),
        (r'\bnb\b', 'nav-badge'),
        (r'\bnb g\b', 'nav-badge green'),
        (r'\bnb o\b', 'nav-badge orange'),
        (r'\bnb c\b', 'nav-badge cyan'),
        (r'\bview\b', 'view'), # unchanged
        (r'\bfullh\b', 'view'), # Make fullh into standard view to match CSS
        (r'\bkrow\b', 'kpi-row'),
        (r'\bkcard\b', 'kpi-card'),
        (r'\bklbl\b', 'kpi-label'),
        (r'\bkval c\b', 'kpi-val cyan'),
        (r'\bkval p\b', 'kpi-val purple'),
        (r'\bkval g\b', 'kpi-val green'),
        (r'\bkval o\b', 'kpi-val orange'),
        (r'\bksub\b', 'kpi-sub'),
        (r'\bkbw\b', 'kpi-bar-wrap'),
        (r'\bkb c\b', 'kpi-bar cyan'),
        (r'\bkb p\b', 'kpi-bar purple'),
        (r'\bkb g\b', 'kpi-bar green'),
        (r'\bkb o\b', 'kpi-bar orange'),
        (r'\bg2\b', 'grid-2'),
        (r'\bg3\b', 'grid-3'),
        (r'\bg-auto\b', 'agent-grid'),
        (r'\bph\b', 'panel-header'),
        (r'\bpt\b', 'panel-title'),
        (r'\bpi\b', 'panel-icon'),
        (r'\bpbadge\b', 'panel-badge'),
        (r'\bpb\b', 'panel-body'),
        (r'\bstbl\b', 'svc-table'),
        (r'\bsrow\b', 'svc-row'),
        (r'\bpill u\b', 'status-pill up'),
        (r'\bpill d\b', 'status-pill down'),
        (r'\bpill w\b', 'status-pill warn'),
        (r'\bpdot\b', 'pill-dot'),
        (r'\bptag\b', 'port-tag'),
        (r'\bplat\b', 'svc-name'),
        (r'\btc\b', 'tag-cyan'),
        (r'\btp\b', 'tag-purple'),
        (r'\btg\b', 'tag-green'),
        (r'\bto\b', 'tag-orange'),
        (r'\btr\b', 'tag-red'),
        (r'\bsbox\b', 'stream-box'),
        (r'\bll\b', 'log-line'),
        (r'\bts\b', 'log-ts'),
        (r'\blt s\b', 'log-txt success'),
        (r'\blt e\b', 'log-txt error'),
        (r'\blt w\b', 'log-txt warn'),
        (r'\blt i\b', 'log-txt info'),
        (r'\blt x\b', 'log-txt system'),
        (r'\blt\b', 'log-txt'),
        (r'\bacard\b', 'agent-card'),
        (r'\badot\b', 'agent-status-dot'),
        (r'\bae\b', 'agent-emoji'),
        (r'\ban\b', 'agent-name'),
        (r'\bdta\b', 'dispatch-input'),
        (r'\bds\b', 'dispatch-select'),
        (r'\bbp\b', 'btn-primary'),
        (r'\bbg\b', 'btn-ghost'),
        (r'\bbc\b', 'btn-cyan'),
    ]

    for old, new in replacements:
        content = re.sub(old, new, content)

    # Specific JS fixes since regex boundaries can miss JS templates
    content = content.replace("class='dot'", "class='pulse-dot'")
    content = content.replace('class="dot"', 'class="pulse-dot"')
    content = content.replace('class="dot err"', 'class="pulse-dot fault"')
    content = content.replace('class="dot warn"', 'class="pulse-dot warn"')
    
    # Fix 'nav-item active' logic in JS
    content = content.replace("classList.remove('on')", "classList.remove('active')") 
    content = content.replace("classList.add('on')", "classList.add('active')")
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    fix_html()
