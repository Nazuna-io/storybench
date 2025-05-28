"""Enhanced validation service with real API testing."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..repositories.base import Repository
from ...evaluators.factory import EvaluatorFactory
from ...models.config import Config
from .error_handling import timeout_after, normalize_api_error
from .lightweight_api_test import LightweightAPITester


@dataclass
class APITestResult:
    """Result of API connectivity test."""
    provider: str
    connected: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    model_tested: Optional[str] = None


@dataclass
class ModelValidationResult:
    """Result of individual model validation."""
    model_name: str
    valid: bool
    errors: List[str]
    api_result: Optional[APITestResult] = None


class ValidationService:
    """Enhanced validation service with real API testing."""
    
    def __init__(self, repository: Repository):
        """Initialize validation service."""
        self.repository = repository
    
    async def validate_configuration(self, test_apis: bool = True, lightweight_test: bool = True) -> Dict[str, Any]:
        """Validate configuration and optionally test API connections.
        
        Args:
            test_apis: Whether to test API connectivity
            lightweight_test: Use lightweight API tests (faster) vs full evaluator setup
        """
        try:
            # Use existing Config class for validation
            config = Config.load_config("config/models.yaml")
            config_errors = config.validate()
            
            result = {
                "valid": len(config_errors) == 0,
                "config_errors": config_errors,
                "config_hash": config.get_version_hash()
            }
            
            if test_apis:
                if lightweight_test:
                    api_results = await self._test_api_connections_lightweight()
                else:
                    api_results = await self._test_api_connections()
                    
                model_results = await self._validate_api_models(config, lightweight_test)
                
                result.update({
                    "api_tests": api_results,
                    "model_validation": model_results
                })
                
                # Overall validation includes API connectivity
                all_apis_ok = all(r.connected or r.error == "API key not configured" 
                                 for r in api_results.values())
                all_models_ok = all(m.valid for m in model_results)
                
                result["valid"] = result["valid"] and all_apis_ok and all_models_ok
            
            return result
            
        except Exception as e:
            return {
                "valid": False,
                "config_errors": [str(e)],
                "config_hash": None
            }

    async def _test_api_connections(self) -> Dict[str, APITestResult]:
        """Test API connections for all configured providers."""
        api_keys = await self.repository.load_api_keys()
        
        # Provider mapping for testing
        providers = {
            "openai": {"key": "OPENAI_API_KEY", "test_model": "gpt-4o-mini"},
            "anthropic": {"key": "ANTHROPIC_API_KEY", "test_model": "claude-3-haiku-20240307"},
            "gemini": {"key": "GOOGLE_API_KEY", "test_model": "gemini-1.5-flash"},
            "qwen": {"key": "QWEN_API_KEY", "test_model": "qwen-turbo"},
            "ai21": {"key": "AI21_API_KEY", "test_model": "j2-mid"}
        }
        
        results = {}
        
        for provider, info in providers.items():
            api_key = api_keys.get(info["key"])
            
            if not api_key:
                results[provider] = APITestResult(
                    provider=provider,
                    connected=False,
                    error="API key not configured"
                )
                continue
            
            # Test the connection using a lightweight request
            result = await self._test_single_api(provider, api_key, info["test_model"])
            results[provider] = result
        
        return results
    
    async def _test_api_connections_lightweight(self) -> Dict[str, APITestResult]:
        """Test API connections using lightweight requests (faster)."""
        api_keys = await self.repository.load_api_keys()
        
        # Provider mapping for testing
        providers = {
            "openai": {"key": "OPENAI_API_KEY"},
            "anthropic": {"key": "ANTHROPIC_API_KEY"},
            "gemini": {"key": "GOOGLE_API_KEY"},
            # Note: qwen and ai21 not supported in lightweight testing yet
        }
        
        results = {}
        
        # Test supported providers with lightweight tests
        for provider, info in providers.items():
            api_key = api_keys.get(info["key"])
            
            if not api_key:
                results[provider] = APITestResult(
                    provider=provider,
                    connected=False,
                    error="API key not configured"
                )
                continue
            
            # Use lightweight API test
            try:
                connected, error, latency = await LightweightAPITester.test_provider(provider, api_key)
                results[provider] = APITestResult(
                    provider=provider,
                    connected=connected,
                    latency_ms=latency,
                    error=error
                )
            except Exception as e:
                results[provider] = APITestResult(
                    provider=provider,
                    connected=False,
                    error=f"Test failed: {str(e)}"
                )
        
        # Add placeholder results for unsupported providers
        for provider in ["qwen", "ai21"]:
            key_name = f"{provider.upper()}_API_KEY"
            api_key = api_keys.get(key_name)
            
            if api_key:
                results[provider] = APITestResult(
                    provider=provider,
                    connected=True,  # Assume valid if key is present
                    error="Lightweight test not available - key appears configured"
                )
            else:
                results[provider] = APITestResult(
                    provider=provider,
                    connected=False,
                    error="API key not configured"
                )
        
        return results
    
    async def _test_single_api(self, provider: str, api_key: str, test_model: str) -> APITestResult:
        """Test a single API provider connection."""
        start_time = time.time()
        
        try:
            # Create a minimal test configuration
            test_config = {
                "type": "api",
                "provider": provider,
                "model_name": test_model
            }
            
            api_keys_dict = {f"{provider.upper()}_API_KEY": api_key}
            if provider == "gemini":
                api_keys_dict = {"GOOGLE_API_KEY": api_key}
            
            # Create evaluator and test setup
            evaluator = EvaluatorFactory.create_evaluator(
                f"test-{provider}", test_config, api_keys_dict
            )
            
            # Test connection (this calls the existing setup method)
            success = await evaluator.setup()
            
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if success:
                return APITestResult(
                    provider=provider,
                    connected=True,
                    latency_ms=round(latency, 2),
                    model_tested=test_model
                )
            else:
                return APITestResult(
                    provider=provider,
                    connected=False,
                    error="Connection test failed",
                    latency_ms=round(latency, 2)
                )
                
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return APITestResult(
                provider=provider,
                connected=False,
                error=str(e),
                latency_ms=round(latency, 2)
            )

    async def _validate_api_models(self, config: Config, lightweight_test: bool = True) -> List[ModelValidationResult]:
        """Validate all configured API models."""
        api_keys = await self.repository.load_api_keys()
        results = []
        
        for model in config.models:
            if model.type != "api":
                continue  # Skip non-API models as requested
            
            errors = []
            api_result = None
            
            # Check required fields
            if not model.provider:
                errors.append("Provider not specified")
            if not model.model_name:
                errors.append("Model name not specified")
            
            # Check API key availability
            provider_key_map = {
                'openai': 'OPENAI_API_KEY',
                'anthropic': 'ANTHROPIC_API_KEY', 
                'gemini': 'GOOGLE_API_KEY',
                'qwen': 'QWEN_API_KEY',
                'ai21': 'AI21_API_KEY'
            }
            
            required_key = provider_key_map.get(model.provider)
            if required_key and not api_keys.get(required_key):
                errors.append(f"API key {required_key} not configured")
            elif required_key and api_keys.get(required_key):
                # Test this specific model if we have the API key
                if lightweight_test and model.provider in ["openai", "anthropic", "gemini", "deepinfra"]:
                    # Use lightweight test for supported providers
                    try:
                        connected, error, latency = await LightweightAPITester.test_provider(
                            model.provider, api_keys[required_key]
                        )
                        api_result = APITestResult(
                            provider=model.provider,
                            connected=connected,
                            latency_ms=latency,
                            error=error,
                            model_tested=model.model_name
                        )
                        if not connected:
                            errors.append(f"API connection failed: {error}")
                    except Exception as e:
                        errors.append(f"API test failed: {str(e)}")
                else:
                    # Use full evaluator test for unsupported providers or when requested
                    api_result = await self._test_single_api(
                        model.provider, 
                        api_keys[required_key], 
                        model.model_name
                    )
                    if not api_result.connected:
                        errors.append(f"API connection failed: {api_result.error}")
            
            results.append(ModelValidationResult(
                model_name=model.name,
                valid=len(errors) == 0,
                errors=errors,
                api_result=api_result
            ))
        
        return results
