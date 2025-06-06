"""
Comprehensive test suite for StoryBench v1.5
Tests all major components: configuration, evaluators, pipeline, and dashboard
"""

import pytest
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.config_loader import ConfigLoader
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator
from storybench.evaluators.api_evaluator_adapter import APIEvaluatorAdapter

class TestConfigurationSystem:
    """Test the YAML configuration system."""
    
    def test_config_loader_initialization(self):
        """Test that ConfigLoader initializes correctly."""
        config_loader = ConfigLoader()
        assert config_loader is not None
    
    def test_config_file_exists(self):
        """Test that the config file exists."""
        config_path = Path(__file__).parent.parent / "config" / "models.yaml"
        assert config_path.exists(), "models.yaml configuration file not found"
    
    def test_config_file_structure(self):
        """Test that config file has correct structure."""
        config_path = Path(__file__).parent.parent / "config" / "models.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Test top-level structure
        assert 'models' in config
        assert isinstance(config['models'], dict)
        
        # Test that we have models defined
        assert len(config['models']) > 0
        
        # Test model structure
        for model_name, model_config in config['models'].items():
            assert 'enabled' in model_config
            assert 'provider' in model_config
            assert 'model_name' in model_config
            assert isinstance(model_config['enabled'], bool)

class TestLiteLLMEvaluator:
    """Test the LiteLLM evaluator system."""
    
    @pytest.fixture
    def mock_evaluator(self):
        """Create a mock evaluator for testing."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            evaluator = LiteLLMEvaluator(
                provider="openai",
                model="gpt-3.5-turbo",
                api_key="test_key"
            )
            return evaluator
    
    def test_evaluator_initialization(self, mock_evaluator):
        """Test that LiteLLMEvaluator initializes correctly."""
        assert mock_evaluator is not None
        assert mock_evaluator.provider == "openai"
        assert mock_evaluator.model == "gpt-3.5-turbo"
    
    def test_provider_config_validation(self):
        """Test that provider configurations are valid."""
        valid_providers = ["openai", "anthropic", "google", "deepinfra"]
        
        for provider in valid_providers:
            try:
                evaluator = LiteLLMEvaluator(
                    provider=provider,
                    model="test-model",
                    api_key="test_key"
                )
                assert evaluator.provider == provider
            except Exception as e:
                pytest.fail(f"Provider {provider} failed initialization: {e}")

class TestAPIEvaluatorAdapter:
    """Test the backwards compatibility adapter."""
    
    def test_adapter_initialization(self):
        """Test that the adapter initializes correctly."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            adapter = APIEvaluatorAdapter(
                provider="openai",
                model="gpt-3.5-turbo"
            )
            assert adapter is not None

class TestDataService:
    """Test the dashboard data service."""
    
    @pytest.fixture
    def mock_data_service(self):
        """Create a mock data service."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit_dashboard"))
        from data_service import DataService
        
        with patch('data_service.MongoClient'):
            service = DataService()
            return service
    
    def test_data_service_initialization(self, mock_data_service):
        """Test that DataService initializes correctly."""
        assert mock_data_service is not None
    
    def test_score_extraction(self, mock_data_service):
        """Test score extraction from evaluation text."""
        test_text = """
        Here is the evaluation:
        **creativity**: 4.5 - Great creative concepts
        **coherence**: 3.2 - Mostly coherent narrative
        **character_depth**: 4.0 - Well developed characters
        """
        
        scores = mock_data_service.extract_scores_from_evaluation(test_text)
        
        assert 'creativity' in scores
        assert scores['creativity'] == 4.5
        assert 'coherence' in scores
        assert scores['coherence'] == 3.2
        assert 'character_depth' in scores
        assert scores['character_depth'] == 4.0

class TestDashboardPages:
    """Test dashboard page functionality."""
    
    @pytest.fixture
    def sample_performance_data(self):
        """Create sample performance data for testing."""
        data = {
            'model': ['claude-opus-4', 'gpt-4o', 'gemini-2.5-pro'] * 10,
            'creativity': [4.5, 4.0, 4.2] * 10,
            'coherence': [4.0, 4.2, 3.8] * 10,
            'character_depth': [4.3, 3.9, 4.1] * 10,
            'dialogue_quality': [4.1, 4.0, 3.9] * 10,
            'visual_imagination': [4.4, 3.8, 4.0] * 10,
            'conceptual_depth': [4.2, 4.1, 3.7] * 10,
            'adaptability': [4.0, 4.3, 4.0] * 10,
            'response_id': [f'resp_{i}' for i in range(30)],
            'prompt_name': ['prompt_1', 'prompt_2', 'prompt_3'] * 10,
            'sequence_name': ['sequence_A', 'sequence_B'] * 15
        }
        return pd.DataFrame(data)
    
    def test_provider_extraction(self, sample_performance_data):
        """Test provider extraction logic."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit_dashboard" / "pages"))
        from providers import extract_provider_from_model
        
        test_cases = {
            'claude-opus-4': 'Anthropic',
            'gpt-4o': 'OpenAI',
            'gemini-2.5-pro': 'Google',
            'deepseek-r1': 'DeepInfra',
            'qwen-72b': 'DeepInfra',
            'unknown-model': 'Unknown'
        }
        
        for model, expected_provider in test_cases.items():
            assert extract_provider_from_model(model) == expected_provider
    
    def test_performance_calculations(self, sample_performance_data):
        """Test performance calculation logic."""
        criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                        'visual_imagination', 'conceptual_depth', 'adaptability']
        
        # Test average calculations
        model_averages = sample_performance_data.groupby('model')[criteria_cols].mean()
        
        assert len(model_averages) == 3  # 3 unique models
        assert all(col in model_averages.columns for col in criteria_cols)
        
        # Test overall score calculation
        overall_scores = model_averages.mean(axis=1)
        assert len(overall_scores) == 3
        assert all(1 <= score <= 5 for score in overall_scores)

class TestAutomatedPipeline:
    """Test the automated evaluation pipeline."""
    
    def test_runner_script_exists(self):
        """Test that the automated runner script exists."""
        runner_path = Path(__file__).parent.parent / "run_automated_evaluation.py"
        assert runner_path.exists(), "run_automated_evaluation.py not found"
    
    def test_runner_imports(self):
        """Test that the runner script imports correctly."""
        runner_path = Path(__file__).parent.parent / "run_automated_evaluation.py"
        
        # Read the file and check for key imports
        with open(runner_path, 'r') as f:
            content = f.read()
        
        assert 'from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator' in content
        assert 'from storybench.config_loader import ConfigLoader' in content
        assert 'AutomatedEvaluationRunner' in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
