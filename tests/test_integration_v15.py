"""
Integration tests for StoryBench v1.5
Tests end-to-end functionality and integration between components
"""

import pytest
import os
import sys
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestConfigurationIntegration:
    """Test integration between configuration and evaluator systems."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            'models': {
                'test-model-1': {
                    'enabled': True,
                    'provider': 'openai',
                    'model_name': 'gpt-3.5-turbo',
                    'max_tokens': 1000,
                    'temperature': 0.7
                },
                'test-model-2': {
                    'enabled': False,
                    'provider': 'anthropic',
                    'model_name': 'claude-3-sonnet',
                    'max_tokens': 2000,
                    'temperature': 0.5
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            yield f.name
        
        os.unlink(f.name)
    
    def test_config_to_evaluator_integration(self, temp_config_file):
        """Test loading config and creating evaluators."""
        from storybench.config_loader import ConfigLoader
        
        config_loader = ConfigLoader(config_path=temp_config_file)
        models = config_loader.get_enabled_models()
        
        # Should only get enabled models
        assert len(models) == 1
        assert models[0]['model_name'] == 'gpt-3.5-turbo'
        assert models[0]['provider'] == 'openai'

class TestEvaluatorIntegration:
    """Test integration between different evaluator components."""
    
    @pytest.fixture
    def mock_litellm_response(self):
        """Mock LiteLLM response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test evaluation response"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        return mock_response
    
    @patch('litellm.completion')
    def test_litellm_evaluator_basic_flow(self, mock_completion, mock_litellm_response):
        """Test basic LiteLLM evaluator flow."""
        from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator
        
        mock_completion.return_value = mock_litellm_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            evaluator = LiteLLMEvaluator(
                provider="openai",
                model="gpt-3.5-turbo",
                api_key="test_key"
            )
            
            # Test evaluation
            response = evaluator.evaluate_response(
                response_text="Test response",
                prompt="Test prompt",
                criteria="Test criteria"
            )
            
            assert response is not None
            assert response.content == "Test evaluation response"
    
    def test_backwards_compatibility_adapter(self):
        """Test that the API evaluator adapter works."""
        from storybench.evaluators.api_evaluator_adapter import APIEvaluatorAdapter
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            adapter = APIEvaluatorAdapter(
                provider="openai",
                model="gpt-3.5-turbo"
            )
            
            # Test that it has the expected interface
            assert hasattr(adapter, 'evaluate_response')
            assert adapter.provider == "openai"
            assert adapter.model == "gpt-3.5-turbo"

class TestPipelineIntegration:
    """Test the automated evaluation pipeline integration."""
    
    @pytest.fixture
    def mock_progress_file(self):
        """Create a mock progress file."""
        progress_data = {
            'start_time': '2025-06-03T10:00:00Z',
            'total_cost': 0.1234,
            'models': {
                'test-model': {
                    'status': 'completed',
                    'completed': 5,
                    'total': 5,
                    'cost': 0.1234,
                    'start_time': '2025-06-03T10:00:00Z',
                    'end_time': '2025-06-03T10:30:00Z'
                }
            },
            'config': {
                'dry_run': False,
                'force_rerun': False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_progress.json', delete=False) as f:
            json.dump(progress_data, f)
            yield f.name
        
        os.unlink(f.name)
    
    def test_progress_file_structure(self, mock_progress_file):
        """Test progress file structure and parsing."""
        with open(mock_progress_file, 'r') as f:
            progress_data = json.load(f)
        
        # Verify required fields
        assert 'start_time' in progress_data
        assert 'models' in progress_data
        assert 'total_cost' in progress_data
        
        # Verify model structure
        for model_name, model_info in progress_data['models'].items():
            assert 'status' in model_info
            assert 'completed' in model_info
            assert 'total' in model_info
            assert 'cost' in model_info

class TestDashboardIntegration:
    """Test integration between dashboard and data sources."""
    
    @pytest.fixture
    def mock_database_data(self):
        """Mock database with realistic data structure."""
        responses = [
            {
                '_id': 'resp_1',
                'model_name': 'claude-opus-4',
                'prompt_name': 'creative_story',
                'sequence_name': 'storytelling',
                'created_at': '2025-06-01T10:00:00Z',
                'text': 'Generated story response...'
            },
            {
                '_id': 'resp_2', 
                'model_name': 'gpt-4o',
                'prompt_name': 'creative_story',
                'sequence_name': 'storytelling',
                'created_at': '2025-06-01T10:05:00Z',
                'text': 'Another story response...'
            }
        ]
        
        evaluations = [
            {
                '_id': 'eval_1',
                'response_id': 'resp_1',
                'evaluating_llm_model': 'gemini-2.5-pro',
                'evaluation_text': '''
                **creativity**: 4.5 - Excellent creative concepts
                **coherence**: 4.0 - Well structured narrative
                **character_depth**: 4.2 - Rich character development
                **dialogue_quality**: 4.1 - Natural conversations
                **visual_imagination**: 4.3 - Vivid imagery
                **conceptual_depth**: 4.0 - Good thematic depth
                **adaptability**: 4.2 - Follows prompt well
                ''',
                'created_at': '2025-06-01T10:30:00Z'
            },
            {
                '_id': 'eval_2',
                'response_id': 'resp_2', 
                'evaluating_llm_model': 'gemini-2.5-pro',
                'evaluation_text': '''
                **creativity**: 4.0 - Good creative elements
                **coherence**: 4.2 - Very coherent
                **character_depth**: 3.8 - Decent characters
                **dialogue_quality**: 4.0 - Solid dialogue
                **visual_imagination**: 3.9 - Good imagery
                **conceptual_depth**: 4.1 - Strong themes
                **adaptability**: 4.3 - Excellent prompt following
                ''',
                'created_at': '2025-06-01T10:35:00Z'
            }
        ]
        
        return responses, evaluations
    
    @patch('data_service.MongoClient')
    def test_dashboard_data_service_integration(self, mock_mongo, mock_database_data):
        """Test full dashboard data service integration."""
        responses, evaluations = mock_database_data
        
        # Setup mock database
        mock_db = Mock()
        mock_mongo.return_value.__getitem__.return_value = mock_db
        mock_db.responses.find.return_value = responses
        mock_db.response_llm_evaluations.find.return_value = evaluations
        
        # Test data service
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "streamlit_dashboard"))
        from data_service import DataService
        
        with patch.dict(os.environ, {'MONGODB_URI': 'mock://test'}):
            service = DataService()
            
            # Test database stats
            stats = service.get_database_stats()
            assert stats['total_responses'] == 2
            assert stats['unique_models'] == 2
            assert stats['total_evaluations'] == 2
            
            # Test performance data
            performance_df = service.get_model_performance_data()
            assert len(performance_df) == 2
            assert 'creativity' in performance_df.columns
            assert 'coherence' in performance_df.columns
            
            # Verify score extraction worked
            assert performance_df.iloc[0]['creativity'] == 4.5
            assert performance_df.iloc[1]['creativity'] == 4.0

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def temp_project_structure(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config directory and file
            config_dir = temp_path / "config"
            config_dir.mkdir()
            
            config_data = {
                'models': {
                    'test-model': {
                        'enabled': True,
                        'provider': 'openai',
                        'model_name': 'gpt-3.5-turbo',
                        'max_tokens': 100,
                        'temperature': 0.7
                    }
                }
            }
            
            with open(config_dir / "models.yaml", 'w') as f:
                yaml.dump(config_data, f)
            
            yield temp_path
    
    def test_config_loading_workflow(self, temp_project_structure):
        """Test the complete configuration loading workflow."""
        from storybench.config_loader import ConfigLoader
        
        config_path = temp_project_structure / "config" / "models.yaml"
        config_loader = ConfigLoader(config_path=str(config_path))
        
        # Test loading
        models = config_loader.get_enabled_models()
        assert len(models) == 1
        
        model_config = models[0]
        assert model_config['model_name'] == 'gpt-3.5-turbo'
        assert model_config['provider'] == 'openai'
        assert model_config['enabled'] is True

class TestErrorHandling:
    """Test error handling across the system."""
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file."""
        from storybench.config_loader import ConfigLoader
        
        with pytest.raises(FileNotFoundError):
            ConfigLoader(config_path="/nonexistent/path/config.yaml")
    
    def test_invalid_config_structure(self):
        """Test handling of invalid configuration structure."""
        from storybench.config_loader import ConfigLoader
        
        invalid_config = "invalid: yaml: structure: ["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            f.flush()
            
            with pytest.raises(yaml.YAMLError):
                ConfigLoader(config_path=f.name)
        
        os.unlink(f.name)
    
    def test_dashboard_missing_data(self):
        """Test dashboard behavior with missing data."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "streamlit_dashboard"))
        
        with patch('data_service.MongoClient') as mock_mongo:
            # Setup empty database
            mock_db = Mock()
            mock_mongo.return_value.__getitem__.return_value = mock_db
            mock_db.responses.find.return_value = []
            mock_db.response_llm_evaluations.find.return_value = []
            
            from data_service import DataService
            
            with patch.dict(os.environ, {'MONGODB_URI': 'mock://test'}):
                service = DataService()
                
                stats = service.get_database_stats()
                assert stats['total_responses'] == 0
                
                performance_df = service.get_model_performance_data()
                assert performance_df.empty

class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets in dashboard."""
        # Create large synthetic dataset
        import numpy as np
        
        large_data = pd.DataFrame({
            'model': np.random.choice(['model_a', 'model_b', 'model_c'], 10000),
            'creativity': np.random.uniform(1, 5, 10000),
            'coherence': np.random.uniform(1, 5, 10000),
            'response_id': [f'resp_{i}' for i in range(10000)]
        })
        
        # Test groupby operations (common in dashboard)
        model_averages = large_data.groupby('model')[['creativity', 'coherence']].mean()
        
        assert len(model_averages) == 3
        assert not model_averages.isnull().any().any()
    
    def test_memory_efficiency(self):
        """Test memory efficiency of data processing."""
        import sys
        
        # Create moderately large dataset
        data = pd.DataFrame({
            'model': ['test_model'] * 1000,
            'creativity': [4.0] * 1000,
            'coherence': [4.0] * 1000
        })
        
        # Measure memory usage (basic check)
        initial_size = sys.getsizeof(data)
        
        # Process data (typical dashboard operations)
        grouped = data.groupby('model').mean()
        processed_size = sys.getsizeof(grouped)
        
        # Grouped data should be much smaller
        assert processed_size < initial_size

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
