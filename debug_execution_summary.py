from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Capture console messages
    console_messages = []
    page.on('console', lambda msg: console_messages.append({
        'type': msg.type,
        'text': msg.text
    }))
    
    # Capture page errors
    page_errors = []
    page.on('pageerror', lambda error: page_errors.append(str(error)))
    
    print("Navigating to execution summary page...")
    try:
        page.goto('http://localhost:3000/execution-summary?project=face38d8-24c7-45fd-9d83-c80e959b0e1d&projectName=Evolve', wait_until='networkidle', timeout=30000)
        
        # Wait a bit for any async operations
        page.wait_for_timeout(2000)
        
        # Take screenshot
        page.screenshot(path='execution_summary_debug.png', full_page=True)
        print("Screenshot saved to: execution_summary_debug.png")
        
        # Get page title
        title = page.title()
        print(f"Page title: {title}")
        
        # Check for any visible error messages
        error_elements = page.locator('text=/error/i, text=/failed/i, text=/not found/i').all()
        if error_elements:
            print(f"\nFound {len(error_elements)} error elements on page")
            for elem in error_elements[:5]:  # Show first 5
                print(f"  - {elem.text_content()[:100]}")
        
        # Print console messages
        if console_messages:
            print(f"\n=== Console Messages ({len(console_messages)}) ===")
            for msg in console_messages[-20:]:  # Show last 20
                print(f"[{msg['type']}] {msg['text']}")
        
        # Print page errors
        if page_errors:
            print(f"\n=== Page Errors ({len(page_errors)}) ===")
            for error in page_errors:
                print(f"ERROR: {error}")
        
        # Get page content snippet
        content = page.content()
        if 'Error' in content or 'error' in content:
            print("\n=== Page contains error text ===")
        
        print("\nPage loaded successfully!" if not page_errors else "\nPage loaded with errors!")
        
    except Exception as e:
        print(f"\nFailed to load page: {e}")
        page.screenshot(path='execution_summary_error.png')
        print("Error screenshot saved to: execution_summary_error.png")
    
    finally:
        browser.close()
