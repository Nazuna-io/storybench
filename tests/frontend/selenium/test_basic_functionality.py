"""
Basic smoke tests for Storybench Web UI.
"""
import pytest
# from .conftest import DashboardPage, ModelsConfigPage, PromptsPage


# @pytest.mark.selenium
# class TestBasicNavigation:
#     """Test basic navigation and page loading."""
#     
#     def test_dashboard_loads(self, driver):
#         """Test that the dashboard loads successfully."""
#         page = DashboardPage(driver)
#         page.wait_for_page_load()
#         
#         title = page.get_title()
#         assert "Storybench" in title or title != ""
#         
#         # Check if main content is visible
#         assert page.is_element_present(page.HEADER_TITLE)
#     
#     def test_navigation_to_config(self, driver):
#         """Test navigation to configuration page."""
#         dashboard = DashboardPage(driver)
#         dashboard.wait_for_page_load()
#         
#         # Navigate to config page
#         config_page = dashboard.navigate_to_config()
#         config_page.wait_for_page_load()
#         
#         # Verify we're on the config page
#         assert config_page.is_element_present(config_page.PAGE_TITLE)
#         assert config_page.is_global_settings_visible()
#     
#     def test_navigation_to_prompts(self, driver):
#         """Test navigation to prompts page."""
#         dashboard = DashboardPage(driver)
#         dashboard.wait_for_page_load()
#         
#         # Navigate to prompts page
#         prompts_page = dashboard.navigate_to_prompts()
#         prompts_page.wait_for_page_load()
#         
#         # Verify we're on the prompts page
#         assert prompts_page.is_element_present(prompts_page.PAGE_TITLE)


@pytest.mark.selenium
class TestModelsConfiguration:
    """Test models configuration functionality."""
    
    def test_config_page_loads_data(self, driver):
        """Test that config page loads with data."""
        dashboard = DashboardPage(driver)
        dashboard.wait_for_page_load()
        
        config_page = dashboard.navigate_to_config()
        config_page.wait_for_page_load()
        
        # Check that temperature input has a value
        temp_value = config_page.get_temperature_value()
        assert temp_value is not None
        assert float(temp_value) >= 0.0


@pytest.mark.selenium
class TestPromptsManagement:
    """Test prompts management functionality."""
    
    def test_prompts_page_loads_sequences(self, driver):
        """Test that prompts page loads with sequences."""
        dashboard = DashboardPage(driver)
        dashboard.wait_for_page_load()
        
        prompts_page = dashboard.navigate_to_prompts()
        prompts_page.wait_for_page_load()
        
        # Check that prompt sequences are loaded
        sequence_count = prompts_page.get_sequence_count()
        assert sequence_count > 0, "No prompt sequences found"
        
        # Check for success toast (indicates data loaded)
        assert prompts_page.is_success_toast_visible()


@pytest.mark.selenium
@pytest.mark.slow
class TestEndToEndWorkflow:
    """Test complete user workflows."""
    
    def test_complete_navigation_flow(self, driver):
        """Test complete navigation through all pages."""
        # Start at dashboard
        dashboard = DashboardPage(driver)
        dashboard.wait_for_page_load()
        
        # Go to config
        config_page = dashboard.navigate_to_config()
        config_page.wait_for_page_load()
        assert config_page.is_global_settings_visible()
        
        # Go back to dashboard by clicking logo or home
        driver.get("http://localhost:5175")
        dashboard.wait_for_page_load()
        
        # Go to prompts
        prompts_page = dashboard.navigate_to_prompts()
        prompts_page.wait_for_page_load()
        assert prompts_page.get_sequence_count() > 0
        
        # Complete workflow successful
        assert True
