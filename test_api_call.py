#!/usr/bin/env python3
"""Test the Results page API call with detailed debugging."""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_results_api_call():
    """Test if the Results page is making the API call correctly."""
    print("🔍 Testing Results page API call...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to results page
        driver.get("http://localhost:8000/#/results")
        
        # Wait for page to load
        time.sleep(2)
        
        print("📄 Page loaded, checking API call...")
        
        # Execute JavaScript to monitor fetch calls
        js_code = """
        // Store original fetch
        const originalFetch = window.fetch;
        window.fetchCalls = [];
        
        // Override fetch to track calls
        window.fetch = function(...args) {
            console.log('Fetch called with:', args);
            window.fetchCalls.push({
                url: args[0],
                options: args[1] || {},
                timestamp: new Date().toISOString()
            });
            
            return originalFetch.apply(this, args)
                .then(response => {
                    console.log('Fetch response:', response.status, response.statusText);
                    return response;
                })
                .catch(error => {
                    console.log('Fetch error:', error);
                    throw error;
                });
        };
        
        return 'Fetch monitoring installed';
        """
        
        result = driver.execute_script(js_code)
        print(f"✅ {result}")
        
        # Wait a bit more for Vue to mount and make API calls
        time.sleep(5)
        
        # Check if any fetch calls were made
        fetch_calls = driver.execute_script("return window.fetchCalls || [];")
        print(f"🌐 Fetch calls made: {len(fetch_calls)}")
        
        for i, call in enumerate(fetch_calls):
            print(f"  {i+1}. URL: {call['url']}")
            print(f"     Time: {call['timestamp']}")
        
        # Try to manually trigger the loadResults function
        print("🔧 Attempting to manually trigger API call...")
        
        manual_call = driver.execute_script("""
        return fetch('http://localhost:8000/api/results')
            .then(response => response.json())
            .then(data => {
                console.log('Manual API call successful:', data.total_count);
                return {
                    success: true,
                    total_count: data.total_count,
                    results_length: data.results.length
                };
            })
            .catch(error => {
                console.log('Manual API call failed:', error);
                return {
                    success: false,
                    error: error.toString()
                };
            });
        """)
        
        # Wait for the promise to resolve
        time.sleep(3)
        
        # Check browser logs for the manual call result
        logs = driver.get_log('browser')
        print(f"🖥️ Browser console logs ({len(logs)} entries):")
        for log in logs[-5:]:  # Show last 5 logs
            print(f"  [{log['level']}] {log['message']}")
        
        # Check current page state
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if "No Results Yet" in page_text:
            print("❌ Page still shows 'No Results Yet'")
        else:
            print("✅ Page no longer shows 'No Results Yet'")
        
        # Check the stats values
        stats_elements = driver.find_elements(By.CSS_SELECTOR, ".text-xl.font-bold")
        print(f"📊 Stats values found: {len(stats_elements)}")
        for i, elem in enumerate(stats_elements):
            print(f"  {i+1}. '{elem.text}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_results_api_call()
