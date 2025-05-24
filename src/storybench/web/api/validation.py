"""API endpoints for configuration validation."""

from fastapi import APIRouter, HTTPException, Depends
import asyncio
import time
from typing import Dict, Any

from ..models.requests import ValidationRequest
from ..models.responses import ValidationResponse, ValidationErrorDetail, APIValidationResult, ModelValidationResult
from ..services.validation_service import ValidationService
from ..repositories.file_repository import FileRepository


router = APIRouter()

# Dependency to get validation service
def get_validation_service() -> ValidationService:
    """Get validation service instance."""
    repository = FileRepository()
    return ValidationService(repository)


@router.post("/validate", response_model=ValidationResponse)
async def validate_configuration(
    validation_request: ValidationRequest,
    validation_service: ValidationService = Depends(get_validation_service)
):
    """Validate current configuration and optionally test API connections."""
    try:
        # Use enhanced validation service
        validation_result = await validation_service.validate_configuration(
            test_apis=validation_request.test_api_connections,
            lightweight_test=validation_request.lightweight_test
        )
        
        config_errors = []
        for error in validation_result.get("config_errors", []):
            config_errors.append(ValidationErrorDetail(
                field="general",
                message=error,
                code="validation_error"
            ))
        
        # Convert API test results
        api_validation = {}
        if "api_tests" in validation_result:
            for provider, result in validation_result["api_tests"].items():
                api_validation[provider] = APIValidationResult(
                    connected=result.connected,
                    error=result.error,
                    latency_ms=result.latency_ms
                )
        
        # Convert model validation results
        model_validation = []
        if "model_validation" in validation_result:
            for result in validation_result["model_validation"]:
                api_result = None
                if result.api_result:
                    api_result = APIValidationResult(
                        connected=result.api_result.connected,
                        error=result.api_result.error,
                        latency_ms=result.api_result.latency_ms
                    )
                
                model_validation.append(ModelValidationResult(
                    model_name=result.model_name,
                    valid=result.valid,
                    errors=result.errors,
                    api_result=api_result
                ))
        
        return ValidationResponse(
            valid=validation_result["valid"],
            config_errors=config_errors,
            api_validation=api_validation,
            model_validation=model_validation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

