import os

path = r'c:\Users\Administrator\Documents\twisterlab\src\twisterlab\agents\real\real_maestro_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

r1_old = '    TRADING = "trading"\n    UNKNOWN = "unknown"'
r1_new = '    TRADING = "trading"\n    DOCUMENTATION = "documentation"\n    UNKNOWN = "unknown"'
if r1_old in content:
    content = content.replace(r1_old, r1_new)

r2_old = '''        # INTELLIGENCE tasks
        elif any(kw in task_lower for kw in ["veille", "news", "intelligence", "market", "competitor", "watch", "rss", "browse"]):
            category = TaskCategory.INTELLIGENCE
            keywords = ["intelligence", "watch"]
            suggested_requirements.extend(["browse", "summarize", "translate", "create_page", "n8n_trigger_webhook", "archive_result"])'''

r2_new = r2_old + '''
        
        # DOCUMENTATION tasks
        elif any(kw in task_lower for kw in ["notion", "write", "log", "document", "page", "documentation", "report", "rapport"]):
            category = TaskCategory.DOCUMENTATION
            keywords = ["documentation", "notion"]
            suggested_requirements.extend(["create_page", "list_pages", "summarize"])'''

if r2_old in content:
    content = content.replace(r2_old, r2_new)

r3_old = '''            steps.append({"order": 5, "requirement": "translate", "params": {"text": "{{step_4_result}}", "target_language": "french"}, "purpose": "Localize findings for dashboard"})
            steps.append({"order": 6, "requirement": "create_page", "params": {"title": f"Rapport Trading {symbol}", "content": "{{step_5_result}}"}, "purpose": "Publish report to workspace"})'''

r3_new = r3_old + '''
        
        elif category == TaskCategory.DOCUMENTATION:
            steps.append({"order": 3, "requirement": "summarize", "params": {"text": "{{step_2_result}}"}, "purpose": "Structure documentation content"})
            steps.append({"order": 4, "requirement": "create_page", "params": {"title": "Documentation Maestro", "content": "{{step_3_result}}"}, "purpose": "Create Notion page"})'''

if r3_old in content:
    content = content.replace(r3_old, r3_new)

content = content.replace('\n# test edit', '')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
