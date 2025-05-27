#!/usr/bin/env python3
"""Selenium test to debug the Results page issue."""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

def test_results_page():
    """Test the Results page using Selenium."""
    print("🔍 Testing Results page with Selenium...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = None
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print("✅ Chrome driver initialized")
        
        # Navigate to the Results page
        url = "http://localhost:8000/#/results"
        print(f"🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait a bit for the page to load
        time.sleep(3)
        
        # Check page title
        title = driver.title
        print(f"📄 Page title: {title}")
        
        # Get page source to check if Vue app loaded
        page_source = driver.page_source
        print(f"📝 Page source length: {len(page_source)} characters")
        
        # Check if Vue app div exists
        try:
            app_div = driver.find_element(By.ID, "app")
            print("✅ Vue app div found")
        except NoSuchElementException:
            print("❌ Vue app div not found")
        
        # Look for Results page specific elements
        try:
            # Wait for results page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            # Check for the Results page heading
            h1_elements = driver.find_elements(By.TAG_NAME, "h1")
            print(f"📋 Found {len(h1_elements)} h1 elements:")
            for i, h1 in enumerate(h1_elements):
                print(f"  {i+1}. '{h1.text}'")
            
            # Look for results table or cards
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"📊 Found {len(tables)} table elements")
            
            # Look for result cards (mobile view)
            cards = driver.find_elements(By.CLASS_NAME, "card")
            print(f"📱 Found {len(cards)} card elements")
            
            # Check for loading spinner
            spinners = driver.find_elements(By.CLASS_NAME, "animate-spin")
            print(f"⏳ Found {len(spinners)} loading spinners")
            
            # Check for "No Results" message
            no_results_messages = driver.find_elements(By.XPATH, "//*[contains(text(), 'No Results')]")
            print(f"🚫 Found {len(no_results_messages)} 'No Results' messages")
            
        except TimeoutException:
            print("⏰ Timeout waiting for page elements")
        
        # Check browser console logs
        print("\n🖥️ Browser console logs:")
        try:
            logs = driver.get_log('browser')
            if logs:
                for log in logs[-10:]:  # Show last 10 logs
                    level = log['level']
                    message = log['message']
                    print(f"  [{level}] {message}")
            else:
                print("  No console logs found")
        except Exception as e:
            print(f"  Could not retrieve console logs: {e}")
        
        # Check network requests
        print("\n🌐 Checking if API call is being made...")
        try:
            # Execute JavaScript to check if fetch is being called
            js_result = driver.execute_script("""
                return {
                    location: window.location.href,
                    userAgent: navigator.userAgent,
                    fetch_available: typeof fetch !== 'undefined'
                };
            """)
            print(f"  Current URL: {js_result['location']}")
            print(f"  Fetch available: {js_result['fetch_available']}")
        except Exception as e:
            print(f"  JavaScript execution failed: {e}")
        
        # Take a screenshot for debugging
        try:
            screenshot_path = "/home/todd/storybench/selenium_results_debug.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"📸 Could not save screenshot: {e}")
        
        # Get final page source for analysis
        final_source = driver.page_source
        
        # Look for specific text that should be on the Results page
        if "Evaluation Results" in final_source:
            print("✅ Found 'Evaluation Results' text")
        else:
            print("❌ 'Evaluation Results' text not found")
        
        if "Total Evaluations" in final_source:
            print("✅ Found 'Total Evaluations' text")
        else:
            print("❌ 'Total Evaluations' text not found")
        
        # Save page source for analysis
        with open("/home/todd/storybench/selenium_page_source.html", "w") as f:
            f.write(final_source)
        print("💾 Page source saved to selenium_page_source.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Selenium test: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()
            print("🔒 Browser driver closed")

if __name__ == "__main__":
    success = test_results_page()
    if success:
        print("\n✅ Selenium test completed")
    else:
        print("\n❌ Selenium test failed")
