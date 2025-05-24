"""
Selenium test configuration and fixtures for Storybench Web UI.
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager


class StorybenchTestConfig:
    """Configuration for Storybench tests."""
    BASE_URL = "http://localhost:5175"
    BACKEND_URL = "http://localhost:8000"
    DEFAULT_TIMEOUT = 10
    LONG_TIMEOUT = 30


@pytest.fixture(scope="session")
def driver_init():
    """Initialize Firefox WebDriver for the test session."""
    firefox_options = Options()
    firefox_options.add_argument("--headless")  # Run in headless mode
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")
    firefox_options.add_argument("--window-size=1920,1080")
    
    # Use webdriver-manager to handle driver installation
    service = Service(GeckoDriverManager().install())
    
    driver = webdriver.Firefox(service=service, options=firefox_options)
    driver.implicitly_wait(StorybenchTestConfig.DEFAULT_TIMEOUT)
    
    yield driver
    
    driver.quit()


@pytest.fixture
def driver(driver_init):
    """Provide a fresh driver instance for each test."""
    driver_init.get(StorybenchTestConfig.BASE_URL)
    yield driver_init
    # Clean up between tests
    driver_init.delete_all_cookies()


@pytest.fixture
def wait(driver):
    """Provide WebDriverWait instance."""
    return WebDriverWait(driver, StorybenchTestConfig.DEFAULT_TIMEOUT)


class BasePage:
    """Base page object with common functionality."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, StorybenchTestConfig.DEFAULT_TIMEOUT)
    
    def get_title(self):
        return self.driver.title
    
    def wait_for_element(self, locator, timeout=None):
        """Wait for element to be present."""
        wait_time = timeout or StorybenchTestConfig.DEFAULT_TIMEOUT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.presence_of_element_located(locator))
    
    def wait_for_clickable(self, locator, timeout=None):
        """Wait for element to be clickable."""
        wait_time = timeout or StorybenchTestConfig.DEFAULT_TIMEOUT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.element_to_be_clickable(locator))
    
    def wait_for_text(self, locator, text, timeout=None):
        """Wait for element to contain specific text."""
        wait_time = timeout or StorybenchTestConfig.DEFAULT_TIMEOUT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.text_to_be_present_in_element(locator, text))
    
    def is_element_present(self, locator):
        """Check if element is present on the page."""
        try:
            self.driver.find_element(*locator)
            return True
        except:
            return False
    
    def take_screenshot(self, name):
        """Take a screenshot for debugging."""
        self.driver.save_screenshot(f"tests/reports/{name}.png")


class DashboardPage(BasePage):
    """Page object for the main dashboard."""
    
    # Locators
    HEADER_TITLE = (By.TAG_NAME, "h1")
    SIDEBAR_NAV = (By.CSS_SELECTOR, "nav")
    CONFIG_LINK = (By.LINK_TEXT, "Configuration")
    PROMPTS_LINK = (By.LINK_TEXT, "Prompts")
    RESULTS_TABLE = (By.CSS_SELECTOR, "table")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".animate-spin")
    
    def navigate_to_config(self):
        """Navigate to configuration page."""
        config_link = self.wait_for_clickable(self.CONFIG_LINK)
        config_link.click()
        return ModelsConfigPage(self.driver)
    
    def navigate_to_prompts(self):
        """Navigate to prompts page."""
        prompts_link = self.wait_for_clickable(self.PROMPTS_LINK)
        prompts_link.click()
        return PromptsPage(self.driver)
    
    def wait_for_page_load(self):
        """Wait for the dashboard to fully load."""
        self.wait_for_element(self.HEADER_TITLE)
        # Wait for loading spinner to disappear if present
        try:
            self.wait.until_not(EC.presence_of_element_located(self.LOADING_SPINNER))
        except TimeoutException:
            pass  # No loading spinner present


class ModelsConfigPage(BasePage):
    """Page object for the models configuration page."""
    
    # Locators
    PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Model Configuration')]")
    GLOBAL_SETTINGS_CARD = (By.XPATH, "//h2[contains(text(), 'Global Settings')]/parent::*")
    TEMPERATURE_INPUT = (By.CSS_SELECTOR, "input[type='number']")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".animate-spin")
    SUCCESS_TOAST = (By.CSS_SELECTOR, ".fixed.bottom-4.right-4.bg-green-600")
    
    def wait_for_page_load(self):
        """Wait for the config page to fully load."""
        self.wait_for_element(self.PAGE_TITLE)
        # Wait for loading to complete
        try:
            self.wait.until_not(EC.presence_of_element_located(self.LOADING_SPINNER))
        except TimeoutException:
            pass
    
    def get_temperature_value(self):
        """Get the current temperature input value."""
        temp_input = self.wait_for_element(self.TEMPERATURE_INPUT)
        return temp_input.get_attribute("value")
    
    def is_global_settings_visible(self):
        """Check if global settings card is visible."""
        return self.is_element_present(self.GLOBAL_SETTINGS_CARD)


class PromptsPage(BasePage):
    """Page object for the prompts management page."""
    
    # Locators
    PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Prompts Management')]")
    PROMPT_SEQUENCES = (By.CSS_SELECTOR, ".card")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".animate-spin")
    SUCCESS_TOAST = (By.CSS_SELECTOR, ".fixed.bottom-4.right-4.bg-green-600")
    
    def wait_for_page_load(self):
        """Wait for the prompts page to fully load."""
        self.wait_for_element(self.PAGE_TITLE)
        # Wait for loading to complete
        try:
            self.wait.until_not(EC.presence_of_element_located(self.LOADING_SPINNER))
        except TimeoutException:
            pass
    
    def get_sequence_count(self):
        """Get the number of prompt sequences displayed."""
        sequences = self.driver.find_elements(*self.PROMPT_SEQUENCES)
        return len(sequences)
    
    def is_success_toast_visible(self):
        """Check if success toast is visible."""
        return self.is_element_present(self.SUCCESS_TOAST)
