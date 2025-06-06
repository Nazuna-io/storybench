
        
        # Check that model string is correct
        assert evaluator.litellm_model == "o4-mini"
        
        # The actual parameter handling is in generate_response
        # which we can't fully test without mocking
    
    def test_api_key_configuration(self, test_config):
        """Test that missing API keys are handled properly."""
        # Test with missing API key
        with pytest.raises(ValueError, match="missing API key"):
            empty_keys = {}
            evaluator = LiteLLMEvaluator(
                name="test-no-key",
                config=test_config,
                api_keys=empty_keys
            )
            # Note: In actual implementation, we might want to check this in setup()
    
    def test_model_info_method(self, test_config, mock_api_keys):
        """Test get_model_info returns correct information."""
        evaluator = LiteLLMEvaluator(
            name="test-evaluator",
            config=test_config,
            api_keys=mock_api_keys
        )
        
        info = evaluator.get_model_info()
        
        assert info["name"] == "test-evaluator"
        assert info["provider"] == "google"
        assert info["model_name"] == "gemini-pro"
        assert info["litellm_model"] == "gemini/gemini-pro"
        assert info["context_size"] == 1000
        assert info["total_tokens_used"] == 0
        assert info["total_cost"] == 0.0


class TestLiteLLMFactory:
    """Test the factory function for creating evaluators."""
    
    def test_create_litellm_evaluator(self):
        """Test factory function creates evaluator correctly."""
        from storybench.evaluators.litellm_evaluator import create_litellm_evaluator
        
        api_keys = {"google": "test-key", "gemini": "test-key"}
        
        evaluator = create_litellm_evaluator(
            name="factory-test",
            provider="google",
            model_name="gemini-pro",
            api_keys=api_keys,
            context_size=32000,
            custom_param="test"
        )
        
        assert isinstance(evaluator, LiteLLMEvaluator)
        assert evaluator.name == "factory-test"
        assert evaluator.provider == "google"
        assert evaluator.model_name == "gemini-pro"
        assert evaluator.config.get("custom_param") == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
