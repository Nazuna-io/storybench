"""Directus CMS client for fetching prompt data."""

import os
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime

from .directus_models import (
    DirectusPromptSetVersion, DirectusPromptSequence, DirectusPrompt,
    DirectusListResponse, DirectusItemResponse, PublicationStatus,
    StorybenchPromptsStructure, StorybenchPromptConfig,
    DirectusEvaluationVersion, StorybenchEvaluationStructure, StorybenchEvaluationCriterion
)


class DirectusClientError(Exception):
    """Base exception for Directus client errors."""
    pass


class DirectusAuthenticationError(DirectusClientError):
    """Raised when authentication fails."""
    pass


class DirectusNotFoundError(DirectusClientError):
    """Raised when requested resource is not found."""
    pass


class DirectusServerError(DirectusClientError):
    """Raised when server returns 5xx errors."""
    pass


class DirectusClient:
    """Client for interacting with Directus CMS API."""
    
    def __init__(self, base_url: str = None, token: str = None, timeout: int = 60):
        """Initialize Directus client."""
        self.base_url = base_url or os.getenv('DIRECTUS_URL')
        self.token = token or os.getenv('DIRECTUS_TOKEN')
        self.timeout = timeout
        
        if not self.base_url:
            raise DirectusClientError("Directus URL not provided")
        if not self.token:
            raise DirectusClientError("Directus token not provided")
            
        self.base_url = self.base_url.rstrip('/')
        self.client_config = {
            'timeout': httpx.Timeout(timeout),
            'headers': {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
        }
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make HTTP request to Directus API with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(**self.client_config) as client:
            try:
                response = await client.request(method, url, **kwargs)
                
                # Handle different HTTP status codes
                if response.status_code == 401:
                    raise DirectusAuthenticationError("Invalid or expired token")
                elif response.status_code == 404:
                    raise DirectusNotFoundError(f"Resource not found: {endpoint}")
                elif response.status_code >= 500:
                    raise DirectusServerError(f"Server error: {response.status_code}")
                elif not response.is_success:
                    error_text = response.text
                    raise DirectusClientError(f"API request failed: {response.status_code} - {error_text}")
                
                return response.json()
                
            except httpx.TimeoutException:
                raise DirectusClientError(f"Request timeout after {self.timeout} seconds")
            except httpx.RequestError as e:
                raise DirectusClientError(f"Request failed: {str(e)}")
    
    async def get_latest_published_version(self) -> Optional[DirectusPromptSetVersion]:
        """Get the latest published prompt set version."""
        params = {
            'filter[status][_eq]': 'published',
            'sort': '-version_number',
            'limit': '1',
            'fields': '*,sequences_in_set.prompt_sequences_id.*,sequences_in_set.prompt_sequences_id.prompts_in_sequence.prompts_id.*'
        }
        
        response_data = await self._make_request('GET', '/items/prompt_set_versions', params=params)
        
        if not response_data.get('data'):
            return None
            
        version_data = response_data['data'][0]
        return DirectusPromptSetVersion(**version_data)
    
    async def get_version_by_number(self, version_number: int) -> Optional[DirectusPromptSetVersion]:
        """Get a specific prompt set version by version number."""
        params = {
            'filter[version_number][_eq]': str(version_number),
            'filter[status][_eq]': 'published',
            'fields': '*,sequences_in_set.prompt_sequences_id.*,sequences_in_set.prompt_sequences_id.prompts_in_sequence.prompts_id.*'
        }
        
        response_data = await self._make_request('GET', '/items/prompt_set_versions', params=params)
        
        if not response_data.get('data'):
            return None
            
        version_data = response_data['data'][0]
        return DirectusPromptSetVersion(**version_data)
    
    async def convert_to_storybench_format(self, version: DirectusPromptSetVersion) -> StorybenchPromptsStructure:
        """Convert Directus format to storybench MongoDB format."""
        sequences = {}
        
        if version.sequences_in_set:
            for sequence_junction in version.sequences_in_set:
                sequence = sequence_junction.prompt_sequences_id
                
                if sequence.status == PublicationStatus.PUBLISHED and sequence.prompts_in_sequence:
                    # Get all published prompts from this sequence
                    published_prompts = []
                    
                    for prompt_junction in sequence.prompts_in_sequence:
                        prompt = prompt_junction.prompts_id
                        if prompt.status == PublicationStatus.PUBLISHED:
                            published_prompts.append(
                                StorybenchPromptConfig(name=prompt.name, text=prompt.text)
                            )
                    
                    # Sort prompts by order_in_sequence if available
                    if published_prompts and hasattr(published_prompts[0], 'order_in_sequence'):
                        published_prompts.sort(key=lambda p: getattr(prompt_junction.prompts_id, 'order_in_sequence', 0))
                    
                    if published_prompts:
                        sequences[sequence.sequence_name] = published_prompts
        
        return StorybenchPromptsStructure(
            sequences=sequences,
            version=version.version_number,
            directus_id=version.id,
            created_at=version.date_created or datetime.utcnow(),
            updated_at=version.date_updated
        )
    
    async def fetch_prompts(self, version_number: Optional[int] = None) -> Optional[StorybenchPromptsStructure]:
        """Fetch prompts from Directus CMS in storybench format.
        
        Args:
            version_number: Specific version to fetch. If None, fetches latest published version.
            
        Returns:
            StorybenchPromptsStructure or None if not found.
        """
        if version_number is not None:
            version = await self.get_version_by_number(version_number)
        else:
            version = await self.get_latest_published_version()
        
        if not version:
            return None
            
        return await self.convert_to_storybench_format(version)
    
    async def list_published_versions(self) -> List[DirectusPromptSetVersion]:
        """List all published prompt set versions."""
        params = {
            'filter[status][_eq]': 'published',
            'sort': '-version_number',
            'fields': 'id,version_number,version_name,description,date_created,date_updated,status'
        }
        
        response_data = await self._make_request('GET', '/items/prompt_set_versions', params=params)
        
        if not response_data.get('data'):
            return []
            
        return [DirectusPromptSetVersion(**item) for item in response_data['data']]
    
    async def test_connection(self) -> bool:
        """Test connection to Directus API."""
        try:
            # Test with a simple query to prompt_set_versions instead of collections
            await self._make_request('GET', '/items/prompt_set_versions?limit=1')
            return True
        except DirectusClientError:
            return False
    
    async def get_latest_published_evaluation_version(self) -> Optional[DirectusEvaluationVersion]:
        """Get the latest published evaluation version."""
        # First try with junction table fields
        params_with_fields = {
            'filter[status][_eq]': 'published',
            'sort': '-version_number',
            'limit': '1',
            'fields': '*,evaluation_criteria_in_version.evaluation_criteria_id.*,scoring_in_version.scoring_id.*'
        }
        
        response_data = await self._make_request('GET', '/items/evaluation_versions', params=params_with_fields)
        
        # If no results with junction fields, try without them
        if not response_data.get('data'):
            params_basic = {
                'filter[status][_eq]': 'published',
                'sort': '-version_number',
                'limit': '1',
                'fields': '*'
            }
            
            response_data = await self._make_request('GET', '/items/evaluation_versions', params=params_basic)
        
        if not response_data.get('data'):
            return None
            
        version_data = response_data['data'][0]
        return DirectusEvaluationVersion(**version_data)
    
    async def get_evaluation_version_by_number(self, version_number: int) -> Optional[DirectusEvaluationVersion]:
        """Get a specific evaluation version by version number."""
        params = {
            'filter[version_number][_eq]': str(version_number),
            'filter[status][_eq]': 'published',
            'fields': '*,evaluation_criteria_in_version.evaluation_criteria_id.*,scoring_in_version.scoring_id.*'
        }
        
        response_data = await self._make_request('GET', '/items/evaluation_versions', params=params)
        
        if not response_data.get('data'):
            return None
            
        version_data = response_data['data'][0]
        return DirectusEvaluationVersion(**version_data)
    
    async def convert_to_storybench_evaluation_format(self, version: DirectusEvaluationVersion) -> StorybenchEvaluationStructure:
        """Convert Directus evaluation format to storybench evaluation structure."""
        criteria = {}
        scoring_guidelines = ""
        
        if version.evaluation_criteria_in_version:
            for criterion_junction in version.evaluation_criteria_in_version:
                criterion = criterion_junction.evaluation_criteria_id
                
                # Convert criterion to storybench format
                criteria[criterion.name] = StorybenchEvaluationCriterion(
                    name=criterion.name.replace('_', ' ').title(),  # "character_depth" -> "Character Depth"
                    description=criterion.description,
                    scale=[1, criterion.scale],  # Convert to [min, max] format
                    criteria=criterion.criteria
                )
        
        if version.scoring_in_version:
            # Use the first scoring guideline if multiple exist
            scoring_junction = version.scoring_in_version[0]
            scoring = scoring_junction.scoring_id
            scoring_guidelines = scoring.guidelines
        
        return StorybenchEvaluationStructure(
            criteria=criteria,
            scoring_guidelines=scoring_guidelines,
            version=version.version_number,
            version_name=version.version_name,
            directus_id=version.id,
            created_at=datetime.now()
        )
