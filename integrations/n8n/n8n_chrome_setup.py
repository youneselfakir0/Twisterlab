import json
import os
import re
import time
from playwright.sync_api import sync_playwright

def setup_n8n():
    url = "http://192.168.0.30:5678"
    
    with sync_playwright() as p:
        print("Launching Chrome visibly for you...")
        browser = p.chromium.launch(headless=False, channel='chrome')
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        # 1. Navigating to n8n setup
        print("Navigating to n8n...")
        page.goto(url, wait_until="networkidle")
        time.sleep(2)  # Give it a moment to load and render the UI
        
        # Check if we are on the setup page
        if "/setup" in page.url or page.locator("input[type='email']").is_visible():
            print("Filling owner account details...")
            # Use reliable selectors to fill form
            inputs = page.locator("input")
            
            # n8n uses names or ids often: email, firstName, lastName, password
            try:
                page.fill("input[name='email']", "admin@twisterlab.local")
                page.fill("input[name='firstName']", "Twister")
                page.fill("input[name='lastName']", "Lab")
                page.fill("input[name='password']", "TwisterLab2026!")
            except Exception:
                # Fallback to general input orders (typically 4 fields)
                page.locator("input").nth(0).fill("admin@twisterlab.local")
                page.locator("input").nth(1).fill("Twister")
                page.locator("input").nth(2).fill("Lab")
                page.locator("input").nth(3).fill("TwisterLab2026!")

            time.sleep(1)
            # Find the submit button
            print("Clicking Next/Setup...")
            try:
                page.click("button[type='submit']")
            except:
                page.locator("button", has_text=re.compile("Next|Setup", re.IGNORECASE)).first.click()
            time.sleep(3)
        
        # 2. Skip Questionnaire if present
        if "questionnaire" in page.url.lower() or "survey" in page.url.lower() or page.locator("text=Skip").is_visible():
            print("Skipping questionnaire...")
            try:
                page.locator("button", has_text="Skip").click()
            except:
                pass
            time.sleep(2)
        else:
            print("No onboarding questionnaire detected or bypassed automatically.")

        # 3. Handle Welcome Modal if present
        try:
            get_started = page.locator("button", has_text=re.compile("Get started|Let's go", re.IGNORECASE))
            if get_started.is_visible():
                print("Closing welcome modal...")
                get_started.click()
                time.sleep(1)
        except:
            pass
            
        print("Successfully reached n8n dashboard!")
        
        # We will keep the browser open for 5 seconds to let you see it, then optionally inject the workflow via API
        time.sleep(5)
        context.close()
        browser.close()

if __name__ == "__main__":
    setup_n8n()
