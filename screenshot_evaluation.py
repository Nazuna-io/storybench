#!/usr/bin/env python3
"""
Take a screenshot of the evaluation page to see the issues.
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def take_evaluation_screenshot():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Loading the main page...")
        driver.get("http://localhost:8000/")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        
        # Navigate to evaluation page
        print("Navigating to evaluation page...")
        try:
            eval_link = driver.find_element(By.LINK_TEXT, "Run Evaluation")
            eval_link.click()
            time.sleep(3)
        except Exception as e:
            print(f"Could not find 'Run Evaluation' link: {e}")
            # Try alternative navigation
            try:
                driver.get("http://localhost:8000/evaluation")
                time.sleep(3)
            except Exception as e2:
                print(f"Could not navigate to evaluation page: {e2}")
        
        # Take screenshot
        screenshot_path = "/home/todd/storybench/evaluation_page_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Look for key elements mentioned in the issue
        try:
            resume_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Resume') or contains(text(), 'resume')]")
            print(f"Found resume element: {resume_btn.text}")
        except:
            print("No resume button found")
            
        try:
            eval_control = driver.find_element(By.XPATH, "//*[contains(text(), 'Evaluation Control') or contains(text(), 'evaluation control')]")
            print(f"Found evaluation control: {eval_control.text}")
        except:
            print("No evaluation control found")
            
        try:
            console_output = driver.find_element(By.XPATH, "//*[contains(text(), 'waiting for evaluation') or contains(text(), 'Console')]")
            print(f"Found console output: {console_output.text}")
        except:
            print("No console output found")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    take_evaluation_screenshot()
