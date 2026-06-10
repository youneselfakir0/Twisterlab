import os
import time
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meta_session")

def setup_meta_session():
    """
    Launches Chrome with a persistent context so the user can log into Instagram and Facebook.
    The cookies/session will be saved in the 'meta_session' folder.
    """
    print(f"📂 Session sera sauvegardée dans : {SESSION_DIR}")
    print("🚀 Lancement du navigateur de configuration...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,  # Must be visible for manual login
            channel="chrome",
            viewport={"width": 1280, "height": 720}
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("\n🌐 Navigation vers Instagram...")
        page.goto("https://www.instagram.com/")
        print("👉 Veuillez vous connecter à Instagram dans le navigateur (si ce n'est pas déjà fait).")
        print("⏳ Le navigateur restera ouvert pendant 3 minutes pour vous laisser le temps (et faire la 2FA)...")
        
        # Give user time to log in to Instagram
        time.sleep(180)
        
        print("\n🌐 Navigation vers Facebook (Optionnel, utile si comptes déliés)...")
        page.goto("https://www.facebook.com/")
        print("👉 Veuillez vous connecter à Facebook (si nécessaire).")
        
        # Give user another minute
        time.sleep(60)
        
        print("\n✅ Temps écoulé. Fermeture et sauvegarde de la session.")
        browser.close()
        
    print(f"\n✨ Session enregistrée avec succès dans {SESSION_DIR} !")
    print("Vous pouvez maintenant utiliser l'agent de publication automatique sans mot de passe.")

if __name__ == "__main__":
    setup_meta_session()
