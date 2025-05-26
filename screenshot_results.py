#!/usr/bin/env python3
"""
Quick script to take a screenshot of the results page to check padding issues.
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def take_screenshot():
    # Setup Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Loading the results page...")
        driver.get("http://localhost:8000/")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Wait a bit more for Vue to render
        time.sleep(3)
        
        # Try to navigate to results page
        try:
            results_link = driver.find_element(By.LINK_TEXT, "Results")
            results_link.click()
            time.sleep(2)
        except:
            print("Could not find Results link, taking screenshot of current page")
        
        # Take screenshot
        screenshot_path = "/home/todd/storybench/results_page_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Print some debug info
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Check if we can find the sidebar and main content
        try:
            sidebar = driver.find_element(By.CSS_SELECTOR, "aside")
            print(f"Sidebar found with classes: {sidebar.get_attribute('class')}")
        except:
            print("Sidebar not found")
            
        try:
            main_content = driver.find_element(By.CSS_SELECTOR, "main")
            print(f"Main content found with classes: {main_content.get_attribute('class')}")
        except:
            print("Main content not found")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    take_screenshot()
