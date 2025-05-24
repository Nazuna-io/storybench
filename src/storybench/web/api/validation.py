"""API endpoints for configuration validation."""

from fastapi import APIRouter, HTTPException, Depends
import asyncio
import time
from typing import Dict, Any

from ..models.requests import ValidationRequest
from ..models.responses import ValidationResponse, ValidationErrorDetail, APIValidationResult, ModelValidationResult
from ..services.config_service import ConfigService
from ..repositories.file_repository import FileRepository


router = APIRouter()

# Dependency to get config service
def get_config_service() -> ConfigService:
    """Get config service instance."""
    repository = FileRepository()
    return ConfigService(repository)


@router.post("/validate", response_model=ValidationResponse)
async def validate_configuration(
    validation_request: ValidationRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate current configuration and optionally test API connections."""
    try:
        # Basic configuration validation
        validation_result = await config_service.validate_configuration()
        
        config_errors = []
        for error in validation_result.get("errors", []):
            config_errors.append(ValidationErrorDetail(
                field="general",
                message=error,
                code="validation_error"
            ))
        
        api_validation = {}
        model_validation = []
        
        # Test API connections if requested
        if validation_request.test_api_connections:
            api_validation = await _test_api_connections(config_service)
        
        # Validate models if requested
        if validation_request.validate_local_models:
            model_validation = await _validate_models(config_service)
        
        return ValidationResponse(
            valid=validation_result["valid"] and len(config_errors) == 0,
            config_errors=config_errors,
            api_validation=api_validation,
            model_validation=model_validation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


async def _test_api_connections(config_service: ConfigService) -> Dict[str, APIValidationResult]:
    """Test API connections for all configured providers."""
    # This is a placeholder - in Phase 2 we'll implement actual API testing
    api_keys = await config_service.repository.load_api_keys()
    
    results = {}
    for provider in ["openai", "anthropic", "google", "qwen", "ai21"]:
        key_name = f"{provider.upper()}_API_KEY"
        if provider == "google":
            key_name = "GOOGLE_API_KEY"
        
        if api_keys.get(key_name):
            results[provider] = APIValidationResult(
                connected=True,  # Placeholder
                latency_ms=50.0
            )
        else:
            results[provider] = APIValidationResult(
                connected=False,
                error="API key not configured"
            )
    
    return results


async def _validate_models(config_service: ConfigService) -> list[ModelValidationResult]:
    """Validate model configurations."""
    # This is a placeholder - in Phase 2 we'll implement actual model validation
    config_data = await config_service.get_models_config()
    results = []
    
    for model in config_data.get("models", []):
        results.append(ModelValidationResult(
            model_name=model["name"],
            valid=True,  # Placeholder
            errors=[]
        ))
    
    return results
