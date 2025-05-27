#!/usr/bin/env python3
"""Firefox Selenium test to debug the Results page issue."""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_results_page_firefox():
    """Debug the Results page using Firefox."""
    print("🦊 Starting Firefox Selenium test for Results page...")
    
    firefox_options = Options()
    firefox_options.add_argument('--headless')
    
    driver = None
    try:
        driver = webdriver.Firefox(options=firefox_options)
        driver.set_page_load_timeout(30)
        
        print("✅ Firefox driver started")
        
        # Navigate to the page
        url = "http://localhost:8000/#/results"
        print(f"🌐 Loading: {url}")
        driver.get(url)
        
        # Wait for Vue app to load
        print("⏳ Waiting for page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "app"))
        )
        
        time.sleep(3)  # Give Vue time to mount
        
        print(f"📄 Page title: '{driver.title}'")
        
        # Check for main heading
        try:
            h1 = driver.find_element(By.XPATH, "//h1[contains(text(), 'Evaluation Results')]")
            print("✅ Found 'Evaluation Results' heading")
        except:
            print("❌ 'Evaluation Results' heading not found")
        
        # Execute JavaScript to check state and make API call
        print("\n🔧 Testing API call via JavaScript...")
        js_test = """
        console.log('=== FIREFOX SELENIUM TEST ===');
        console.log('Location:', window.location.href);
        console.log('Fetch available:', typeof fetch !== 'undefined');
        
        // Make API call
        console.log('Starting manual API call...');
        fetch('http://localhost:8000/api/results')
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);
                return response.json();
            })
            .then(data => {
                console.log('API SUCCESS - Total count:', data.total_count);
                console.log('Results length:', data.results ? data.results.length : 'undefined');
                
                // Try to update the page manually
                const statsElements = document.querySelectorAll('.text-xl.font-bold, .text-2xl.font-bold');
                console.log('Found', statsElements.length, 'stat elements');
                
                return {
                    success: true,
                    total_count: data.total_count,
                    results_count: data.results ? data.results.length : 0
                };
            })
            .catch(error => {
                console.log('API ERROR:', error);
                return {
                    success: false,
                    error: error.toString()
                };
            });
        
        return 'API call initiated';
        """
        
        result = driver.execute_script(js_test)
        print(f"📊 JavaScript result: {result}")
        
        # Wait for API call
        time.sleep(5)
        
        # Check console logs
        print("\n🖥️ Browser console logs:")
        try:
            logs = driver.get_log('browser')
            if logs:
                for log in logs[-10:]:
                    print(f"  [{log['level']}] {log['message']}")
            else:
                print("  No console logs available")
        except Exception as e:
            print(f"  Console logs not available: {e}")
        
        # Check current page state
        print("\n📊 Current page state:")
        
        # Get stats values
        try:
            stats = driver.find_elements(By.CSS_SELECTOR, ".text-xl.font-bold, .text-2xl.font-bold")
            print(f"  Found {len(stats)} stat elements:")
            for i, stat in enumerate(stats):
                text = stat.text.strip()
                if text and text not in ["Storybench"]:
                    print(f"    {i+1}. '{text}'")
        except Exception as e:
            print(f"  Error getting stats: {e}")
        
        # Check for No Results message
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'No Results Yet')]")
            print("❌ Still showing 'No Results Yet'")
        except:
            print("✅ 'No Results Yet' not found")
        
        # Check for results elements
        tables = len(driver.find_elements(By.TAG_NAME, "table"))
        cards = len(driver.find_elements(By.CLASS_NAME, "card"))
        print(f"  Tables: {tables}, Cards: {cards}")
        
        # Take screenshot
        try:
            driver.save_screenshot("/home/todd/storybench/firefox_results_debug.png")
            print("📸 Screenshot saved: firefox_results_debug.png")
        except Exception as e:
            print(f"📸 Screenshot failed: {e}")
        
        # Final check - try to trigger loadResults manually if it exists
        print("\n🔄 Attempting to manually trigger loadResults...")
        try:
            manual_trigger = driver.execute_script("""
                // Try to find and call loadResults if it exists in Vue component
                console.log('Attempting to trigger manual results load...');
                
                // Direct API call and page update
                fetch('http://localhost:8000/api/results')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Manual trigger - got data:', data.total_count, 'results');
                        
                        // Try to find and update the stats manually
                        const totalEvalElement = document.querySelector('.text-2xl.font-bold');
                        if (totalEvalElement && data.total_count) {
                            console.log('Updating stats element with:', data.total_count);
                            totalEvalElement.textContent = data.total_count.toString();
                        }
                    })
                    .catch(error => console.log('Manual trigger error:', error));
                
                return 'Manual trigger attempted';
            """)
            print(f"📋 Manual trigger result: {manual_trigger}")
        except Exception as e:
            print(f"❌ Manual trigger failed: {e}")
        
        time.sleep(3)  # Wait for manual trigger
        
        # Final state check
        print("\n🏁 Final state check:")
        final_stats = driver.find_elements(By.CSS_SELECTOR, ".text-2xl.font-bold")
        for i, stat in enumerate(final_stats):
            text = stat.text.strip()
            if text.isdigit():
                print(f"  Stat {i+1}: '{text}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()
            print("🔒 Firefox closed")

if __name__ == "__main__":
    debug_results_page_firefox()
