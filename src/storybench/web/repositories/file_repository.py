"""File-based repository implementation."""

import json
import yaml
import os
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import Repository


class FileRepository(Repository):
    """File-based repository using existing storybench file structure."""
    
    def __init__(self, config_dir: str = "config", output_dir: str = "output"):
        """Initialize with config and output directories."""
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        self.env_file = Path(".env")
        
    async def load_models_config(self) -> Dict[str, Any]:
        """Load models configuration from YAML file."""
        models_path = self.config_dir / "models.yaml"
        async with aiofiles.open(models_path, 'r') as f:
            content = await f.read()
            return yaml.safe_load(content)
    
    async def save_models_config(self, config: Dict[str, Any]) -> None:
        """Save models configuration to YAML file."""
        models_path = self.config_dir / "models.yaml"
        async with aiofiles.open(models_path, 'w') as f:
            await f.write(yaml.dump(config, default_flow_style=False, sort_keys=False))
    
    async def load_prompts(self) -> Dict[str, List[Dict[str, str]]]:
        """Load prompts from JSON file."""
        prompts_path = self.config_dir / "prompts.json"
        async with aiofiles.open(prompts_path, 'r') as f:
            content = await f.read()
            return json.loads(content)
    
    async def save_prompts(self, prompts: Dict[str, List[Dict[str, str]]]) -> None:
        """Save prompts to JSON file."""
        prompts_path = self.config_dir / "prompts.json"
        async with aiofiles.open(prompts_path, 'w') as f:
            await f.write(json.dumps(prompts, indent=2))

    async def load_evaluation_criteria(self) -> Dict[str, Any]:
        """Load evaluation criteria from YAML file."""
        criteria_path = self.config_dir / "evaluation_criteria.yaml"
        if not criteria_path.exists():
            return {}  # Return empty dict if file doesn't exist yet
        async with aiofiles.open(criteria_path, 'r') as f:
            content = await f.read()
            return yaml.safe_load(content) or {}
    
    async def save_evaluation_criteria(self, criteria: Dict[str, Any]) -> None:
        """Save evaluation criteria to YAML file."""
        criteria_path = self.config_dir / "evaluation_criteria.yaml"
        async with aiofiles.open(criteria_path, 'w') as f:
            await f.write(yaml.dump(criteria, default_flow_style=False, sort_keys=False))
    
    async def load_api_keys(self) -> Dict[str, Optional[str]]:
        """Load API keys from .env file."""
        if not self.env_file.exists():
            return {
                'OPENAI_API_KEY': None,
                'ANTHROPIC_API_KEY': None,
                'GOOGLE_API_KEY': None,
                'QWEN_API_KEY': None,
                'AI21_API_KEY': None
            }
        
        env_vars = {}
        async with aiofiles.open(self.env_file, 'r') as f:
            content = await f.read()
            for line in content.strip().split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
        
        return {
            'OPENAI_API_KEY': env_vars.get('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': env_vars.get('ANTHROPIC_API_KEY'),
            'GOOGLE_API_KEY': env_vars.get('GOOGLE_API_KEY'),
            'QWEN_API_KEY': env_vars.get('QWEN_API_KEY'),
            'AI21_API_KEY': env_vars.get('AI21_API_KEY')
        }

    async def save_api_keys(self, keys: Dict[str, Optional[str]]) -> None:
        """Save API keys to .env file."""
        # Read existing .env file to preserve other variables
        existing_vars = {}
        if self.env_file.exists():
            async with aiofiles.open(self.env_file, 'r') as f:
                content = await f.read()
                for line in content.strip().split('\n'):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        existing_vars[key.strip()] = value.strip()
        
        # Update with new keys (only if provided and not None)
        for key, value in keys.items():
            if value is not None:
                existing_vars[key] = f'"{value}"'
        
        # Write back to .env file
        env_content = '\n'.join(f'{key}={value}' for key, value in existing_vars.items())
        async with aiofiles.open(self.env_file, 'w') as f:
            await f.write(env_content + '\n')
    
    async def load_results(self, model_name: Optional[str] = None, 
                          config_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load evaluation results from output directory."""
        results = []
        
        if not self.output_dir.exists():
            return results
        
        # Get all JSON files in output directory
        for result_file in self.output_dir.glob("*.json"):
            try:
                async with aiofiles.open(result_file, 'r') as f:
                    content = await f.read()
                    result_data = json.loads(content)
                    
                    # Filter by model name if specified
                    if model_name and result_data.get('metadata', {}).get('model_name') != model_name:
                        continue
                    
                    # Filter by config version if specified
                    if config_version and result_data.get('metadata', {}).get('config_version') != config_version:
                        continue
                    
                    results.append(result_data)
            except (json.JSONDecodeError, KeyError):
                # Skip invalid result files
                continue
        
        return results

    async def save_result(self, model_name: str, result_data: Dict[str, Any]) -> None:
        """Save individual evaluation result to JSON file."""
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Create filename based on model name and timestamp
        config_version = result_data.get('metadata', {}).get('config_version', 'unknown')
        filename = f"{model_name}_{config_version}.json"
        result_path = self.output_dir / filename
        
        async with aiofiles.open(result_path, 'w') as f:
            await f.write(json.dumps(result_data, indent=2, default=str))
    
    async def get_result_versions(self) -> List[str]:
        """Get list of available result configuration versions."""
        versions = set()
        
        if not self.output_dir.exists():
            return []
        
        for result_file in self.output_dir.glob("*.json"):
            try:
                async with aiofiles.open(result_file, 'r') as f:
                    content = await f.read()
                    result_data = json.loads(content)
                    version = result_data.get('metadata', {}).get('config_version')
                    if version:
                        versions.add(version)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return sorted(list(versions))
