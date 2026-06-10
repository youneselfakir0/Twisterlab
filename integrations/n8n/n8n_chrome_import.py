import json
import os
import re
import time
from playwright.sync_api import sync_playwright

def login_and_import():
    url = "http://192.168.0.30:5678"
    workflow_path = "n8n_discord_workflow.json"
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)
    
    with sync_playwright() as p:
        print("🤖 [Web Browser Agent] Lancement de Chrome...")
        browser = p.chromium.launch(headless=False, channel='chrome')
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        # 1. Navigating to n8n
        print("🌐 [Web Browser Agent] Navigation vers n8n...")
        page.goto(url, wait_until="networkidle")
        time.sleep(2)
        
        # 2. Login or Setup
        if "/setup" in page.url or page.locator("text=Set up owner account").is_visible():
            print("🔑 [Web Browser Agent] Création du compte Admin...")
            page.locator("input").nth(0).fill("admin@twisterlab.local")
            page.locator("input").nth(1).fill("Twister")
            page.locator("input").nth(2).fill("Lab")
            page.locator("input").nth(3).fill("TwisterLab2026!")
            time.sleep(1)
            try:
                page.click("button[type='submit']")
            except:
                page.locator("button", has_text=re.compile("Next|Setup", re.IGNORECASE)).first.click()
            time.sleep(3)
            
            if "questionnaire" in page.url.lower() or page.locator("text=Skip").is_visible():
                print("⏭️ [Web Browser Agent] Passage du questionnaire...")
                try:
                    page.locator("button", has_text="Skip").click()
                except:
                    pass
                time.sleep(2)
                
            try:
                get_started = page.locator("button", has_text=re.compile("Get started", re.IGNORECASE))
                if get_started.is_visible():
                    get_started.click()
            except:
                pass

        elif "/signin" in page.url or page.locator("input[type='email']").is_visible():
             print("🔑 [Web Browser Agent] Connexion au compte Admin...")
             page.locator("input[type='email']").fill("admin@twisterlab.local")
             page.locator("input[type='password']").fill("TwisterLab2026!")
             try:
                 page.locator("button[type='submit']").click(timeout=3000)
             except:
                 page.locator("button", has_text=re.compile("Sign in|Login|Next", re.IGNORECASE)).first.click()
             time.sleep(3)

        print("✅ [Web Browser Agent] Dashboard n8n atteint !")
        time.sleep(2)

        # 3. Create the workflow via API context injection!
        print("⚙️ [Web Browser Agent] Injection du workflow dans la base de données...")
        
        # By using page.evaluate with fetch, it automatically uses the browser's authenticated cookies
        api_result = page.evaluate("""(workflowData) => {
            return fetch('/rest/workflows', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(workflowData)
            }).then(r => r.json());
        }""", workflow_data)
        
        if "id" in api_result:
            workflow_id = api_result["id"]
            print(f"✨ [Web Browser Agent] Workflow généré avec succès ! (ID: {workflow_id})")
            
            # 4. Navigate to the new workflow
            new_url = f"{url}/workflow/{workflow_id}"
            print(f"👉 [Web Browser Agent] Ouverture du canevas : {new_url}")
            page.goto(new_url, wait_until="networkidle")
            
            # Highlight to the user
            print("🎉 [Web Browser Agent] Tâche terminée ! Le Workflow est prêt sur votre écran.")
            time.sleep(10) # Laisse le navigateur ouvert 10 secondes pour observer la magie
        else:
            print(f"❌ Erreur lors de l'injection API: {api_result}")
            time.sleep(5)

        context.close()
        browser.close()

if __name__ == "__main__":
    login_and_import()
