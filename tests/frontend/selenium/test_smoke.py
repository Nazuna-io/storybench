"""
Simple smoke test for Selenium setup.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.selenium
def test_selenium_basic_connection(driver):
    """Test basic Selenium connection to the frontend."""
    # Just verify we can load the page and find any element
    driver.get("http://localhost:5175")
    
    # Wait for page to load by looking for any content
    wait = WebDriverWait(driver, 10)
    
    # Look for either the Vue app or basic HTML structure
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        success = True
    except:
        success = False
    
    assert success, "Could not load the frontend page"
    
    # Take a screenshot for debugging
    driver.save_screenshot("tests/reports/basic_connection_test.png")
    
    print(f"Page title: {driver.title}")
    print(f"Current URL: {driver.current_url}")
