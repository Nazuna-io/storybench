#!/usr/bin/env python3
"""Direct Selenium test to debug the Results page issue thoroughly."""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_results_page():
    """Debug the Results page step by step."""
    print("🔍 Starting comprehensive Results page debug...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print("✅ Chrome driver started")
        
        # Navigate to the page
        url = "http://localhost:8000/#/results"
        print(f"🌐 Loading: {url}")
        driver.get(url)
        
        # Wait for Vue app to load
        print("⏳ Waiting for Vue app to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "app"))
        )
        
        time.sleep(3)  # Give Vue time to mount
        
        # Check if page loaded correctly
        title = driver.title
        print(f"📄 Page title: '{title}'")
        
        # Look for specific elements
        try:
            h1 = driver.find_element(By.XPATH, "//h1[contains(text(), 'Evaluation Results')]")
            print("✅ Found 'Evaluation Results' heading")
        except:
            print("❌ 'Evaluation Results' heading not found")
        
        # Get all console logs
        print("\n🖥️ All browser console logs:")
        try:
            all_logs = driver.get_log('browser')
            if all_logs:
                for i, log in enumerate(all_logs):
                    print(f"  {i+1}. [{log['level']}] {log['message']}")
            else:
                print("  No console logs found")
        except Exception as e:
            print(f"  Could not get console logs: {e}")
        
        # Execute JavaScript to check Vue state and trigger API call
        print("\n🔧 Executing comprehensive JavaScript debug...")
        js_debug = """
        const debug = {
            vue_available: typeof Vue !== 'undefined',
            location: window.location.href,
            vue_app_exists: !!document.getElementById('app'),
            fetch_available: typeof fetch !== 'undefined'
        };
        
        console.log('=== STORYBENCH DEBUG START ===');
        console.log('Debug info:', debug);
        
        // Try to manually call the API
        console.log('Making manual API call...');
        fetch('http://localhost:8000/api/results')
            .then(response => {
                console.log('API Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('API Response data:', data);
                console.log('Total results:', data.total_count);
                console.log('Results array length:', data.results ? data.results.length : 'undefined');
            })
            .catch(error => {
                console.log('API Error:', error);
            });
        
        console.log('=== STORYBENCH DEBUG END ===');
        
        return debug;
        """
        
        debug_result = driver.execute_script(js_debug)
        print(f"📊 JavaScript debug result: {debug_result}")
        
        # Wait for API call to complete
        time.sleep(5)
        
        # Get updated console logs
        print("\n🖥️ Console logs after manual API call:")
        try:
            new_logs = driver.get_log('browser')
            if new_logs:
                # Show only logs from the last few seconds
                for log in new_logs[-10:]:
                    print(f"  [{log['level']}] {log['message']}")
            else:
                print("  No new console logs")
        except Exception as e:
            print(f"  Could not get new console logs: {e}")
        
        # Check if the page content changed
        print("\n📋 Checking page content...")
        
        # Look for stats values
        try:
            stats = driver.find_elements(By.CSS_SELECTOR, ".text-xl.font-bold, .text-2xl.font-bold")
            print(f"📊 Found {len(stats)} stat elements:")
            for i, stat in enumerate(stats):
                text = stat.text.strip()
                if text and text != "Storybench":
                    print(f"  {i+1}. '{text}'")
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
        
        # Check for "No Results Yet" message
        try:
            no_results = driver.find_element(By.XPATH, "//*[contains(text(), 'No Results Yet')]")
            print("❌ Still showing 'No Results Yet' message")
        except:
            print("✅ 'No Results Yet' message not found (good!)")
        
        # Check for results table or cards
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            cards = driver.find_elements(By.CLASS_NAME, "card")
            print(f"📊 Found {len(tables)} tables and {len(cards)} cards")
        except Exception as e:
            print(f"❌ Error checking for results: {e}")
        
        # Take a fresh screenshot
        try:
            driver.save_screenshot("/home/todd/storybench/debug_results_after_fix.png")
            print("📸 Screenshot saved: debug_results_after_fix.png")
        except Exception as e:
            print(f"📸 Could not save screenshot: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()
            print("🔒 Browser closed")

if __name__ == "__main__":
    debug_results_page()
