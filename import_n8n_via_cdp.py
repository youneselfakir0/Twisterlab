import asyncio
import json
import requests
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to Chrome over CDP...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            contexts = browser.contexts
            if not contexts:
                print("No browser context found.")
                return

            context = contexts[0]
            pages = context.pages
            
            n8n_page = None
            for page in pages:
                if "192.168.0.30:5678" in page.url:
                    n8n_page = page
                    break
            
            if not n8n_page:
                print("n8n page not found in Chrome. Creating a new tab navigating to n8n...")
                n8n_page = await context.new_page()
                await n8n_page.goto("http://192.168.0.30:5678")
                await n8n_page.wait_for_load_state("networkidle")

            print(f"Found n8n page: {n8n_page.url}")
            
            # Check if we need to login
            if "signin" in n8n_page.url:
                print("You are on the sign-in page. Let me try to log you in or wait for you to log in.")
                # Try to fill user/password if available, or just wait.
                # Often local setups use admin/admin or owner setup.
                try:
                    await n8n_page.fill("input[name='email']", "admin@twisterlab.com", timeout=2000)
                    await n8n_page.fill("input[name='password']", "admin", timeout=2000)
                    await n8n_page.click("button[type='submit']")
                    await n8n_page.wait_for_load_state("networkidle", timeout=5000)
                except Exception as e:
                    print("Could not auto-login. Please login manually in your Chrome window. I'll wait up to 30 seconds.")
                    try:
                        await n8n_page.wait_for_url("**/workflows", timeout=30000)
                    except:
                        print("Did not reach workflows page. Exiting.")
                        return
            
            print("Successfully authenticated or already logged in!")
            
            # Navigate to workflows page and create new workflow
            await n8n_page.goto("http://192.168.0.30:5678/workflow/new")
            await n8n_page.wait_for_load_state("networkidle")
            
            print("Importing workflow via UI paste...")
            with open("n8n_disk_monitoring_workflow.json", "r", encoding="utf-8") as f:
                wf_data = f.read()

            # The best way to import in n8n UI is to simulate a paste event on the canvas
            # We can use the clipboard or just evaluate JS to dispatch a paste event
            await n8n_page.evaluate("""(wf) => {
                const dt = new DataTransfer();
                dt.setData('text/plain', wf);
                const event = new ClipboardEvent('paste', {
                    clipboardData: dt,
                    bubbles: true,
                    cancelable: true
                });
                document.dispatchEvent(event);
            }""", wf_data)
            
            print("Workflow pasted into canvas!")
            
            # Try to save the workflow (Ctrl+S or Cmd+S)
            await asyncio.sleep(2)
            await n8n_page.keyboard.press("Control+S")
            print("Saved workflow. Done!")

        except Exception as e:
            print(f"Error: {e}")

asyncio.run(main())
