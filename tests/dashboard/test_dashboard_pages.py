"""
Dashboard-specific tests for StoryBench v1.5
Tests all dashboard pages and functionality
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

# Add dashboard path
dashboard_path = Path(__file__).parent.parent.parent / "streamlit_dashboard"
sys.path.insert(0, str(dashboard_path))

class TestDataService:
    """Test the dashboard data service."""
    
    @pytest.fixture
    def mock_mongodb(self):
        """Mock MongoDB connection."""
        with patch('data_service.MongoClient') as mock_client:
            mock_db = Mock()
            mock_client.return_value.__getitem__.return_value = mock_db
            
            # Mock responses collection
            mock_responses = [
                {'_id': 'resp1', 'model_name': 'claude-opus-4', 'created_at': '2025-06-01'},
                {'_id': 'resp2', 'model_name': 'gpt-4o', 'created_at': '2025-06-01'},
                {'_id': 'resp3', 'model_name': 'gemini-2.5-pro', 'created_at': '2025-06-01'}
            ]
            
            # Mock evaluations collection
            mock_evaluations = [
                {
                    '_id': 'eval1',
                    'response_id': 'resp1',
                    'evaluation_text': '**creativity**: 4.5\n**coherence**: 4.0\n**character_depth**: 4.2',
                    'created_at': '2025-06-01'
                },
                {
                    '_id': 'eval2', 
                    'response_id': 'resp2',
                    'evaluation_text': '**creativity**: 4.0\n**coherence**: 4.2\n**character_depth**: 3.8',
                    'created_at': '2025-06-01'
                }
            ]
            
            mock_db.responses.find.return_value = mock_responses
            mock_db.response_llm_evaluations.find.return_value = mock_evaluations
            
            yield mock_db
    
    def test_database_stats(self, mock_mongodb):
        """Test database statistics calculation."""
        from data_service import DataService
        
        with patch.dict('os.environ', {'MONGODB_URI': 'mock://test'}):
            service = DataService()
            stats = service.get_database_stats()
            
            assert 'total_responses' in stats
            assert 'unique_models' in stats
            assert 'total_evaluations' in stats
    
    def test_score_extraction_patterns(self):
        """Test various score extraction patterns."""
        from data_service import DataService
        
        service = DataService()
        
        test_cases = [
            ('**creativity**: 4.5', {'creativity': 4.5}),
            ('creativity: 3.2 - Good work', {'creativity': 3.2}), 
            ('Creativity - 4.0 out of 5', {'creativity': 4.0}),
            ('**coherence**: 5', {'coherence': 5.0}),
            ('invalid text', {}),
            ('creativity: 6.0', {}),  # Should reject scores > 5
            ('creativity: 0.5', {})   # Should reject scores < 1
        ]
        
        for text, expected in test_cases:
            result = service.extract_scores_from_evaluation(text)
            assert result == expected, f"Failed for text: {text}"

class TestOverviewPage:
    """Test the overview page functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return pd.DataFrame({
            'model': ['claude-opus-4', 'gpt-4o', 'gemini-2.5-pro'] * 5,
            'creativity': [4.5, 4.0, 4.2] * 5,
            'coherence': [4.0, 4.2, 3.8] * 5,
            'character_depth': [4.3, 3.9, 4.1] * 5
        })
    
    def test_overview_page_import(self):
        """Test that overview page imports correctly."""
        try:
            from pages import overview
            assert hasattr(overview, 'show')
        except ImportError as e:
            pytest.fail(f"Overview page import failed: {e}")

class TestRankingsPage:
    """Test the rankings page functionality."""
    
    def test_radar_chart_creation(self):
        """Test radar chart creation logic."""
        from pages.rankings import create_radar_chart
        
        # Sample model scores
        scores = pd.Series({
            'creativity': 4.5,
            'coherence': 4.0,
            'character_depth': 4.2
        })
        
        fig = create_radar_chart(scores, "test-model")
        
        assert fig is not None
        assert fig.data[0].name == "test-model"
        assert len(fig.data[0].r) == 4  # Should close the radar chart
    
    def test_comparison_radar(self):
        """Test multi-model comparison radar chart."""
        from pages.rankings import create_comparison_radar
        
        model_scores = {
            'model1': pd.Series({'creativity': 4.5, 'coherence': 4.0}),
            'model2': pd.Series({'creativity': 4.0, 'coherence': 4.2})
        }
        
        fig = create_comparison_radar(model_scores, ['model1', 'model2'])
        
        assert fig is not None
        assert len(fig.data) == 2  # Two models

class TestCriteriaPage:
    """Test the criteria analysis page."""
    
    @pytest.fixture
    def criteria_data(self):
        """Sample criteria data."""
        np.random.seed(42)  # For reproducible tests
        return pd.DataFrame({
            'model': ['model_a', 'model_b', 'model_c'] * 10,
            'creativity': np.random.normal(4.0, 0.5, 30),
            'coherence': np.random.normal(4.2, 0.3, 30),
            'character_depth': np.random.normal(3.8, 0.4, 30)
        })
    
    def test_criteria_heatmap(self, criteria_data):
        """Test criteria heatmap creation."""
        from pages.criteria import create_criteria_heatmap
        
        fig = create_criteria_heatmap(criteria_data)
        
        assert fig is not None
        assert len(fig.data) == 1  # Should have one heatmap
        assert fig.data[0].type == 'heatmap'
    
    def test_correlation_analysis(self, criteria_data):
        """Test correlation analysis."""
        from pages.criteria import analyze_criteria_correlations
        
        fig = analyze_criteria_correlations(criteria_data)
        
        assert fig is not None
        assert fig.data[0].type == 'heatmap'

class TestProvidersPage:
    """Test the provider comparison page."""
    
    def test_provider_extraction(self):
        """Test provider extraction from model names."""
        from pages.providers import extract_provider_from_model
        
        test_cases = [
            ('claude-opus-4', 'Anthropic'),
            ('claude-3-sonnet', 'Anthropic'),
            ('gpt-4o', 'OpenAI'),
            ('gpt-3.5-turbo', 'OpenAI'),
            ('o4-mini', 'OpenAI'),
            ('gemini-2.5-pro', 'Google'),
            ('gemini-flash', 'Google'),
            ('deepseek-r1', 'DeepInfra'),
            ('qwen-72b', 'DeepInfra'),
            ('llama-70b', 'DeepInfra'),
            ('unknown-model', 'Unknown')
        ]
        
        for model_name, expected_provider in test_cases:
            result = extract_provider_from_model(model_name)
            assert result == expected_provider, f"Failed for {model_name}: got {result}, expected {expected_provider}"
    
    def test_provider_comparison_chart(self):
        """Test provider comparison chart creation."""
        from pages.providers import create_provider_comparison_chart
        
        data = pd.DataFrame({
            'model': ['claude-opus-4', 'gpt-4o', 'gemini-2.5-pro'] * 5,
            'creativity': [4.5, 4.0, 4.2] * 5,
            'coherence': [4.0, 4.2, 3.8] * 5
        })
        
        fig, provider_scores = create_provider_comparison_chart(data)
        
        assert fig is not None
        assert provider_scores is not None
        assert len(provider_scores) == 3  # Three providers

class TestExplorerPage:
    """Test the data explorer page."""
    
    @pytest.fixture
    def explorer_data(self):
        """Sample data for explorer testing."""
        return pd.DataFrame({
            'model': ['model_a', 'model_b'] * 20,
            'creativity': np.random.uniform(1, 5, 40),
            'coherence': np.random.uniform(1, 5, 40),
            'prompt_name': ['prompt_1', 'prompt_2'] * 20,
            'sequence_name': ['seq_a', 'seq_b'] * 20,
            'created_at': pd.date_range('2025-01-01', periods=40)
        })
    
    def test_data_filtering(self, explorer_data):
        """Test data filtering functionality."""
        from pages.explorer import filter_data
        
        filters = {
            'models': ['model_a'],
            'date_range': None,
            'score_ranges': {'creativity': (3.0, 5.0)},
            'sequences': ['seq_a'],
            'prompts': ['prompt_1']
        }
        
        filtered = filter_data(explorer_data, filters)
        
        assert len(filtered) > 0
        assert all(filtered['model'] == 'model_a')
        assert all(filtered['sequence_name'] == 'seq_a')
        assert all(filtered['prompt_name'] == 'prompt_1')
    
    def test_scatter_plot_creation(self, explorer_data):
        """Test scatter plot creation."""
        from pages.explorer import create_scatter_plot
        
        fig = create_scatter_plot(
            explorer_data, 
            'creativity', 
            'coherence', 
            color_col='model'
        )
        
        assert fig is not None
        assert len(fig.data) > 0

class TestProgressPage:
    """Test the progress monitoring page."""
    
    def test_progress_file_detection(self):
        """Test progress file detection logic."""
        from pages.progress import find_progress_files
        
        # This will look for actual progress files in the project
        progress_files = find_progress_files()
        
        # Should return a list (may be empty if no progress files exist)
        assert isinstance(progress_files, list)
    
    @pytest.fixture
    def sample_progress_data(self):
        """Sample progress data."""
        return {
            'start_time': '2025-06-03T10:00:00Z',
            'total_cost': 0.5234,
            'models': {
                'claude-opus-4': {
                    'status': 'completed',
                    'completed': 10,
                    'total': 10,
                    'cost': 0.2000,
                    'start_time': '2025-06-03T10:00:00Z',
                    'end_time': '2025-06-03T10:30:00Z'
                },
                'gpt-4o': {
                    'status': 'in_progress',
                    'completed': 5,
                    'total': 10,
                    'cost': 0.1500,
                    'start_time': '2025-06-03T10:30:00Z'
                }
            }
        }
    
    def test_progress_chart_creation(self, sample_progress_data):
        """Test progress chart creation."""
        from pages.progress import create_progress_chart
        
        fig = create_progress_chart(sample_progress_data)
        
        assert fig is not None
        assert len(fig.data) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
