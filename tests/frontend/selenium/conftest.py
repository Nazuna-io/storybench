# Comprehensive Test Configuration for Storybench
import pytest
import time
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Test Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
DEFAULT_WAIT_TIME = 10
LONG_WAIT_TIME = 30

class TestConfig:
    """Test configuration and utilities"""
    
    @staticmethod
    def wait_for_server(url, timeout=30):
        """Wait for server to be available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/api/health" if "8000" in url else url, timeout=5)
                if response.status_code == 200:
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(1)
        return False
    
    @staticmethod
    def get_firefox_options():
        """Get Firefox options for testing"""
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        
        # Set Firefox preferences for faster testing
        options.set_preference("media.navigator.permission.disabled", True)
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("media.autoplay.default", 5)
        options.set_preference("permissions.default.image", 2)  # Block images for speed
        
        return options

@pytest.fixture(scope="session")
def test_config():
    """Session-wide test configuration"""
    return TestConfig()

@pytest.fixture(scope="session")
def ensure_servers_running(test_config):
    """Ensure both backend and frontend servers are running"""
    print(f"\n🔍 Checking server availability...")
    
    # Check backend
    backend_ready = test_config.wait_for_server(BACKEND_URL, timeout=10)
    if not backend_ready:
        pytest.skip("Backend server not available at http://localhost:8000")
    
    # Check frontend
    frontend_ready = test_config.wait_for_server(FRONTEND_URL, timeout=10)
    if not frontend_ready:
        pytest.skip("Frontend server not available at http://localhost:5175")
    
    print(f"✅ Both servers are running")
    return True

@pytest.fixture
def driver(test_config, ensure_servers_running):
    """Create Firefox WebDriver instance"""
    options = test_config.get_firefox_options()
    driver = webdriver.Firefox(options=options)
    driver.implicitly_wait(DEFAULT_WAIT_TIME)
    driver.set_window_size(1920, 1080)
    yield driver
    driver.quit()

@pytest.fixture
def wait(driver):
    """WebDriverWait instance"""
    return WebDriverWait(driver, DEFAULT_WAIT_TIME)

@pytest.fixture
def long_wait(driver):
    """Longer WebDriverWait for slow operations"""
    return WebDriverWait(driver, LONG_WAIT_TIME)

class PageObject:
    """Base page object for common functionality"""
    
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
        
    def navigate_to(self, path=""):
        """Navigate to a specific path"""
        url = f"{FRONTEND_URL}{path}"
        self.driver.get(url)
        return self
        
    def wait_for_element(self, locator, timeout=DEFAULT_WAIT_TIME):
        """Wait for element to be present"""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))
        
    def wait_for_clickable(self, locator, timeout=DEFAULT_WAIT_TIME):
        """Wait for element to be clickable"""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.element_to_be_clickable(locator))
        
    def wait_for_text(self, locator, text, timeout=DEFAULT_WAIT_TIME):
        """Wait for element to contain specific text"""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.text_to_be_present_in_element(locator, text))
        
    def take_screenshot(self, name):
        """Take screenshot for debugging"""
        screenshot_path = f"tests/reports/screenshots/{name}_{int(time.time())}.png"
        self.driver.save_screenshot(screenshot_path)
        return screenshot_path

class ResultsPage(PageObject):
    """Page object for Results page"""
    
    # Locators
    HEADER = (By.TAG_NAME, "h1")
    STATS_CARDS = (By.CLASS_NAME, "card")
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder*='Search']")
    STATUS_FILTER = (By.CSS_SELECTOR, "select")
    RESULTS_TABLE = (By.TAG_NAME, "table")
    MOBILE_CARDS = (By.CSS_SELECTOR, ".md\\:hidden .space-y-4 > div")
    VIEW_DETAILS_BUTTONS = (By.XPATH, "//button[contains(text(), 'View Details')]")
    PAGINATION = (By.XPATH, "//div[contains(@class, 'flex') and contains(@class, 'items-center') and contains(@class, 'justify-between')]")
    
    def get_page_title(self):
        """Get the page title"""
        return self.wait_for_element(self.HEADER).text
        
    def get_stats_cards_count(self):
        """Get number of stats cards"""
        return len(self.driver.find_elements(*self.STATS_CARDS))
        
    def search_results(self, query):
        """Search for results"""
        search_input = self.wait_for_element(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(query)
        time.sleep(1)  # Wait for debounced search
        return self
        
    def filter_by_status(self, status):
        """Filter results by status"""
        filter_select = self.wait_for_element(self.STATUS_FILTER)
        filter_select.click()
        option = self.driver.find_element(By.XPATH, f"//option[@value='{status}']")
        option.click()
        time.sleep(1)  # Wait for filter to apply
        return self
        
    def click_view_details(self, index=0):
        """Click view details button"""
        buttons = self.driver.find_elements(*self.VIEW_DETAILS_BUTTONS)
        if buttons and len(buttons) > index:
            buttons[index].click()
        return self
        
    def check_responsive_layout(self):
        """Check if responsive layout is working"""
        # Check desktop view
        self.driver.set_window_size(1920, 1080)
        time.sleep(1)
        desktop_table_visible = len(self.driver.find_elements(*self.RESULTS_TABLE)) > 0
        
        # Check mobile view
        self.driver.set_window_size(375, 667)
        time.sleep(1)
        mobile_cards_visible = len(self.driver.find_elements(*self.MOBILE_CARDS)) > 0
        
        # Reset to desktop
        self.driver.set_window_size(1920, 1080)
        time.sleep(1)
        
        return desktop_table_visible, mobile_cards_visible

class EvaluationPage(PageObject):
    """Page object for Evaluation page"""
    
    # Locators
    HEADER = (By.TAG_NAME, "h1")
    START_BUTTON = (By.XPATH, "//button[contains(text(), 'Start') or contains(text(), 'Resume')]")
    STOP_BUTTON = (By.XPATH, "//button[contains(text(), 'Stop')]")
    PROGRESS_BAR = (By.CSS_SELECTOR, ".progress-bar, [role='progressbar']")
    CONSOLE_OUTPUT = (By.CSS_SELECTOR, ".console-output, .bg-gray-900")
    
    def start_evaluation(self):
        """Start an evaluation"""
        button = self.wait_for_clickable(self.START_BUTTON)
        button.click()
        return self
        
    def stop_evaluation(self):
        """Stop an evaluation"""
        button = self.wait_for_clickable(self.STOP_BUTTON)
        button.click()
        return self

class NavigationComponent(PageObject):
    """Navigation component interactions"""
    
    # Locators
    MOBILE_MENU_BUTTON = (By.CSS_SELECTOR, "button[class*='lg:hidden']")
    SIDEBAR = (By.TAG_NAME, "aside")
    RESULTS_LINK = (By.XPATH, "//a[contains(text(), 'Results')]")
    EVALUATION_LINK = (By.XPATH, "//a[contains(text(), 'Run Evaluation') or contains(text(), 'Evaluation')]")
    MODELS_CONFIG_LINK = (By.XPATH, "//a[contains(text(), 'Models')]")
    PROMPTS_CONFIG_LINK = (By.XPATH, "//a[contains(text(), 'Prompts')]")
    
    def toggle_mobile_menu(self):
        """Toggle mobile menu"""
        # Set mobile viewport
        self.driver.set_window_size(375, 667)
        time.sleep(0.5)
        
        menu_button = self.wait_for_clickable(self.MOBILE_MENU_BUTTON)
        menu_button.click()
        time.sleep(0.5)
        return self
        
    def navigate_to_results(self):
        """Navigate to results page"""
        link = self.wait_for_clickable(self.RESULTS_LINK)
        link.click()
        return self
        
    def navigate_to_evaluation(self):
        """Navigate to evaluation page"""
        link = self.wait_for_clickable(self.EVALUATION_LINK)
        link.click()
        return self
