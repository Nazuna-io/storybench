#!/usr/bin/env python3
"""Simple test to check if Firefox selenium works."""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time

def simple_firefox_test():
    print("🦊 Testing Firefox Selenium...")
    
    options = Options()
    options.add_argument('--headless')
    
    try:
        driver = webdriver.Firefox(options=options)
        print("✅ Firefox driver created")
        
        driver.get("http://localhost:8000/#/results")
        print("✅ Page loaded")
        
        time.sleep(5)
        
        title = driver.title
        print(f"📄 Title: {title}")
        
        # Check for specific text
        page_source = driver.page_source
        if "Evaluation Results" in page_source:
            print("✅ Found 'Evaluation Results'")
        else:
            print("❌ 'Evaluation Results' not found")
            
        if "No Results Yet" in page_source:
            print("❌ Still shows 'No Results Yet'")
        else:
            print("✅ 'No Results Yet' not found (good!)")
        
        # Look for actual numbers in stats
        if '"0"' in page_source or '>0<' in page_source:
            print("❌ Stats still show 0")
        else:
            print("✅ Stats might have real values")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    simple_firefox_test()
