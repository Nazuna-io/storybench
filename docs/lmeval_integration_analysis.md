# StoryBench + LM-Eval Integration Analysis

## Executive Summary

After analyzing both StoryBench and Google's lm-eval framework, I recommend a **hybrid approach** that:
1. **Preserves** your carefully crafted evaluation pipeline entirely
2. **Adopts** LiteLLM for model provider abstraction (replacing manual API code)
3. **Maintains** LangChain for context management (your critical requirement)
4. **Implements** YAML-based configuration for easy model management
5. **Adds** automated pipeline running with resume/skip capabilities
6. **Removes** the orphaned Vue.js frontend
7. **Enhances** visualization with Streamlit dashboard

## Current Architecture Analysis

### StoryBench Strengths
- **Robust evaluation pipeline**: 5 sequences × 3 prompts × 3 runs with context resets
- **LangChain context management**: No truncation, handles up to 200K tokens
- **Directus CMS integration**: Version-controlled prompts and criteria
- **MongoDB storage**: Reliable data persistence
- **Professional reporting**: Automated analysis with examples and consistency metrics

### Pain Points
1. **Manual model management**: Hard-coded models in Python files
2. **Provider-specific code**: Separate implementations for each API provider
3. **Manual pipeline execution**: No automated resume/skip functionality
4. **Orphaned frontend**: Vue.js code needs removal

### LangChain Usage Analysis
Based on code scan, you're using LangChain for:
- **Context management** (`LangChainContextManager`) - Critical feature
- **Text splitting** (`RecursiveCharacterTextSplitter`, `TokenTextSplitter`)
- **Document handling** (`Document` objects)
- **Token estimation** (character-based approximation)

No other LangChain features detected - context management is indeed the primary use.

## Google's LM-Eval Architecture

### Key Features
1. **LiteLLM Integration**: Unified API for multiple providers
2. **Configuration-based**: TOML config files for settings
3. **Batch processing**: Efficient parallel evaluation
4. **Archive system**: SQLite-based result storage
5. **Visualization**: Basic matplotlib-based punt rate analysis

### What We Can Leverage
1. **LiteLLM model abstraction** - Simplifies provider management
2. **Configuration pattern** - YAML/TOML based model definitions
3. **Batch architecture** - Parallel processing concepts

### What We Should NOT Adopt
1. **Evaluation framework** - Keep your Directus-based system
2. **Storage system** - MongoDB is superior to SQLite archives
3. **Basic visualizations** - Your Streamlit dashboard is more comprehensive

## Recommended Implementation Plan

### Phase 1: Model Management Enhancement

#### 1.1 Create YAML Configuration
```yaml
# config/models.yaml
models:
  anthropic:
    - name: claude-opus-4
      model_id: claude-opus-4-20250514
      max_tokens: 200000
      enabled: true
    - name: claude-sonnet-4
      model_id: claude-sonnet-4-20250514
      max_tokens: 200000
      enabled: true
      
  openai:
    - name: gpt-4.1
      model_id: gpt-4.1
      max_tokens: 128000
      enabled: true
      
  google:
    - name: gemini-2.5-pro
      model_id: gemini-2.5-pro-preview-05-06
      max_tokens: 1000000
      enabled: true
      
  deepinfra:
    - name: qwen3-235b
      model_id: Qwen/Qwen3-235B-A22B
      max_tokens: 32768
      enabled: true

# Evaluation settings
evaluation:
  evaluator_model: gemini-2.5-pro-preview-05-06
  temperature_generation: 1.0
  temperature_evaluation: 0.3
  max_retries: 3
  batch_size: 1
```

#### 1.2 LiteLLM Integration (Keep LangChain!)
```python
# src/storybench/evaluators/litellm_evaluator.py
import litellm
from .base import BaseEvaluator
from ..langchain_context_manager import LangChainContextManager

class LiteLLMEvaluator(BaseEvaluator):
    """Evaluator using LiteLLM for API abstraction, LangChain for context."""
    
    def __init__(self, name: str, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(name, config)
        
        # Setup LiteLLM
        provider = config.get("provider")
        model_name = config.get("model_name")
        
        # Configure API keys
        if provider == "anthropic":
            litellm.anthropic_api_key = api_keys.get("anthropic")
        elif provider == "openai":
            litellm.openai_api_key = api_keys.get("openai")
        elif provider == "google":
            litellm.vertex_project = api_keys.get("google_project")
            litellm.vertex_location = api_keys.get("google_location", "us-central1")
        elif provider == "deepinfra":
            # LiteLLM supports custom endpoints
            self.custom_llm_provider = "deepinfra"
            litellm.api_base = "https://api.deepinfra.com/v1"
            litellm.api_key = api_keys.get("deepinfra")
            
        self.litellm_model = self._get_litellm_model_name(provider, model_name)
        
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate using LiteLLM but manage context with LangChain."""
        
        # Use existing LangChain context manager
        context = self.context_manager.build_context(
            history_text=self.generation_history,
            current_prompt=prompt
        )
        
        # Check if context fits
        context_stats = self.context_manager.get_context_stats(context)
        if context_stats["estimated_tokens"] > self.config["context_size"]:
            raise ContextLimitExceededError(
                f"Context too large: {context_stats['estimated_tokens']} tokens"
            )
        
        # Generate with LiteLLM
        response = await litellm.acompletion(
            model=self.litellm_model,
            messages=[{"role": "user", "content": context}],
            temperature=kwargs.get("temperature", 1.0),
            max_tokens=kwargs.get("max_tokens", 8192),
            **self._get_provider_kwargs()
        )
        
        # Update history and return
        self.generation_history = context + "\n\n" + response.choices[0].message.content
        return {
            "response": response.choices[0].message.content,
            "model": self.litellm_model,
            "usage": response.usage._asdict() if response.usage else {}
        }
```

### Phase 2: Pipeline Automation

#### 2.1 Automated Pipeline Runner
```python
# src/storybench/pipeline/auto_runner.py
import yaml
from pathlib import Path
from typing import Dict, List, Set

class AutomatedPipelineRunner:
    """Automated evaluation pipeline with resume/skip capabilities."""
    
    def __init__(self, config_path: str = "config/models.yaml"):
        self.config = self._load_config(config_path)
        self.db_connection = DatabaseConnection()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    async def get_completed_evaluations(self) -> Set[str]:
        """Get set of completed model evaluations."""
        # Query MongoDB for completed evaluations
        completed = await self.db_connection.database["response_llm_evaluations"].distinct(
            "model_name",
            {"status": "completed"}
        )
        return set(completed)
    
    async def run_pipeline(self, resume: bool = True, force_rerun: List[str] = None):
        """Run evaluation pipeline with smart resume/skip."""
        
        # Get current Directus versions
        directus_client = DirectusClient()
        prompt_version = await directus_client.get_current_prompt_version()
        criteria_version = await directus_client.get_current_criteria_version()
        
        # Get completed evaluations for current versions
        if resume:
            completed = await self.get_completed_evaluations()
        else:
            completed = set()
            
        # Process each provider's models
        for provider, models in self.config['models'].items():
            for model_config in models:
                if not model_config.get('enabled', True):
                    print(f"⏭️  Skipping disabled model: {model_config['name']}")
                    continue
                    
                model_id = f"{provider}/{model_config['model_id']}"
                
                if model_id in completed and model_id not in (force_rerun or []):
                    print(f"✅ Skipping completed: {model_id}")
                    continue
                
                print(f"🚀 Running evaluation for: {model_id}")
                
                try:
                    # Create evaluator with LiteLLM
                    evaluator = LiteLLMEvaluator(
                        name=model_config['name'],
                        config={
                            "provider": provider,
                            "model_name": model_config['model_id'],
                            "context_size": model_config['max_tokens'],
                            "temperature": self.config['evaluation']['temperature_generation']
                        },
                        api_keys=self._load_api_keys()
                    )
                    
                    # Run evaluation (your existing pipeline logic)
                    await self.run_model_evaluation(evaluator, prompt_version, criteria_version)
                    
                except Exception as e:
                    print(f"❌ Error with {model_id}: {str(e)}")
                    # Log error but continue with next model
                    continue
```

#### 2.2 Simple CLI Interface
```python
# run_evaluation.py
#!/usr/bin/env python3
"""
Simple one-command evaluation runner.
Usage: python run_evaluation.py [--no-resume] [--rerun model1,model2]
"""

import argparse
import asyncio
from src.storybench.pipeline.auto_runner import AutomatedPipelineRunner

async def main():
    parser = argparse.ArgumentParser(description='Run StoryBench evaluation pipeline')
    parser.add_argument('--no-resume', action='store_true', 
                       help='Start fresh, ignore completed evaluations')
    parser.add_argument('--rerun', type=str, 
                       help='Force rerun specific models (comma-separated)')
    parser.add_argument('--config', type=str, default='config/models.yaml',
                       help='Path to models configuration file')
    
    args = parser.parse_args()
    
    # Parse rerun list
    force_rerun = args.rerun.split(',') if args.rerun else None
    
    # Run pipeline
    runner = AutomatedPipelineRunner(config_path=args.config)
    await runner.run_pipeline(
        resume=not args.no_resume,
        force_rerun=force_rerun
    )
    
    print("\n✨ Evaluation pipeline completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Phase 3: Frontend Cleanup

Remove the orphaned Vue.js frontend:
```bash
# Clean up frontend files
rm -rf frontend/
rm -f Dockerfile.frontend
rm -f WEB_UI_README.md
# Update docker-compose.yml to remove frontend service
```

### Phase 4: Enhanced Visualization

Your existing Streamlit dashboard is already superior to lm-eval's basic matplotlib plots. Keep and enhance it:

1. **Add real-time updates** during evaluation runs
2. **Include model configuration viewer** (from YAML)
3. **Add evaluation history tracking** (versions from Directus)
4. **Export capabilities** for reports

## Migration Steps

1. **Install LiteLLM**: `pip install litellm`
2. **Create configuration files** in `config/` directory
3. **Implement `LiteLLMEvaluator`** alongside existing evaluators
4. **Test with one model** before full migration
5. **Implement automated runner** with resume capabilities
6. **Remove Vue.js frontend** 
7. **Update documentation**

## Benefits of This Approach

1. **Minimal disruption**: Core evaluation pipeline unchanged
2. **Easy model management**: Just edit YAML files
3. **Provider abstraction**: LiteLLM handles API differences
4. **Context preservation**: LangChain continues managing context
5. **Automated workflows**: One command to run everything
6. **Better maintainability**: Less code, more configuration

## What We're NOT Changing

1. **Evaluation pipeline**: 5 sequences × 3 prompts × 3 runs remains
2. **Context management**: LangChain stays for no-truncation guarantee
3. **Directus integration**: Prompts and criteria remain in CMS
4. **MongoDB storage**: Continues as primary datastore
5. **Evaluation logic**: Gemini-2.5-Pro evaluator unchanged
6. **Report generation**: Existing analysis scripts preserved

## Next Steps

1. Review and approve this plan
2. Create a feature branch for implementation
3. Start with Phase 1 (Model Management)
4. Test thoroughly with subset of models
5. Roll out to full model set
6. Document new workflow

This approach gives you the benefits of lm-eval's design patterns (LiteLLM abstraction, configuration-based setup) while preserving everything that makes StoryBench unique and valuable for your creative writing evaluation needs.
        "model_name": model_name,
        "temperature": 1.0,
    }
    
    # Add context size if specified
    if context_size:
        config["context_size"] = context_size
    
    return LiteLLMEvaluator(name, config, api_keys)
```

## Key Advantages of This Implementation

1. **Drop-in Replacement**: Can replace `APIEvaluator` without changing pipeline logic
2. **Unified API**: Single interface for all providers (OpenAI, Anthropic, Google, DeepInfra)
3. **LangChain Preserved**: Context management remains exactly the same
4. **Error Handling**: Maintains your `ContextLimitExceededError` flow
5. **Metrics Compatible**: Returns same response format as current system

## Example Usage

```python
# Old way (current)
evaluator = APIEvaluator(
    name="claude-opus-4",
    config={
        "provider": "anthropic",
        "model_name": "claude-opus-4-20250514",
        "context_size": 200000,
        "temperature": 1.0
    },
    api_keys={"anthropic": os.getenv("ANTHROPIC_API_KEY")}
)

# New way (with LiteLLM)
evaluator = LiteLLMEvaluator(
    name="claude-opus-4",
    config={
        "provider": "anthropic",
        "model_name": "claude-opus-4-20250514",
        "context_size": 200000,
        "temperature": 1.0
    },
    api_keys={"anthropic": os.getenv("ANTHROPIC_API_KEY")}
)

# Everything else remains the same!
response = await evaluator.generate_response(
    prompt="Write a creative story...",
    temperature=1.0,
    max_tokens=8192
)
```

## Migration Path

### Step 1: Add LiteLLM to requirements
```bash
pip install litellm
```

### Step 2: Create the LiteLLMEvaluator
Copy the implementation above to `src/storybench/evaluators/litellm_evaluator.py`

### Step 3: Test with one model
```python
# test_litellm_integration.py
import asyncio
from src.storybench.evaluators.litellm_evaluator import LiteLLMEvaluator

async def test_litellm():
    evaluator = LiteLLMEvaluator(
        name="test-gemini",
        config={
            "provider": "google",
            "model_name": "gemini-2.5-flash-preview-05-20",
            "context_size": 1000000
        },
        api_keys={"gemini": os.getenv("GOOGLE_API_KEY")}
    )
    
    if await evaluator.setup():
        response = await evaluator.generate_response(
            prompt="Write a haiku about testing",
            temperature=0.7,
            max_tokens=100
        )
        print(response)
    
    await evaluator.cleanup()

asyncio.run(test_litellm())
```

### Step 4: Update the pipeline runner
```python
# In test_full_api_production.py or auto_runner.py
# Change this:
generator = APIEvaluator(f"{provider}-{model_name}-generator", model_config, api_keys)

# To this:
generator = LiteLLMEvaluator(f"{provider}-{model_name}-generator", model_config, api_keys)
```

## Configuration-Based Model Loading

```python
# src/storybench/pipeline/model_loader.py
import yaml
from typing import Dict, List
from ..evaluators.litellm_evaluator import LiteLLMEvaluator

class ModelLoader:
    """Load models from YAML configuration."""
    
    @staticmethod
    def load_models_from_config(config_path: str, api_keys: Dict[str, str]) -> List[LiteLLMEvaluator]:
        """Load all enabled models from configuration."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        evaluators = []
        
        for provider, models in config['models'].items():
            for model_config in models:
                if not model_config.get('enabled', True):
                    continue
                
                evaluator = LiteLLMEvaluator(
                    name=model_config['name'],
                    config={
                        "provider": provider,
                        "model_name": model_config['model_id'],
                        "context_size": model_config['max_tokens'],
                        "temperature": config['evaluation']['temperature_generation']
                    },
                    api_keys=api_keys
                )
                
                evaluators.append(evaluator)
        
        return evaluators
```

## Removing Vue.js Frontend

```bash
#!/bin/bash
# cleanup_frontend.sh

echo "Removing orphaned Vue.js frontend..."

# Remove frontend directory
rm -rf frontend/

# Remove frontend-related files
rm -f Dockerfile.frontend
rm -f WEB_UI_README.md

# Update docker-compose.yml to remove frontend service
sed -i '/frontend:/,/^[^ ]/d' docker-compose.yml

# Remove any frontend references in Python code
find . -name "*.py" -exec grep -l "frontend" {} \; | xargs sed -i '/frontend/d'

echo "Frontend cleanup complete!"
```

## Enhanced Streamlit Dashboard Integration

```python
# dashboard_enhancements.py
import streamlit as st
import yaml
from datetime import datetime

def show_model_config_page():
    """Display current model configuration from YAML."""
    st.title("🔧 Model Configuration")
    
    with open('config/models.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Show enabled models
    st.subheader("Enabled Models")
    enabled_count = 0
    for provider, models in config['models'].items():
        enabled_models = [m for m in models if m.get('enabled', True)]
        if enabled_models:
            st.write(f"**{provider.upper()}** ({len(enabled_models)} models)")
            for model in enabled_models:
                st.write(f"- {model['name']} ({model['max_tokens']:,} tokens)")
                enabled_count += 1
    
    st.metric("Total Enabled Models", enabled_count)
    
    # Show evaluation settings
    st.subheader("Evaluation Settings")
    eval_config = config['evaluation']
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Generation Temperature", eval_config['temperature_generation'])
        st.metric("Evaluation Temperature", eval_config['temperature_evaluation'])
    with col2:
        st.metric("Evaluator Model", eval_config['evaluator_model'])
        st.metric("Max Retries", eval_config['max_retries'])

def show_pipeline_status():
    """Show real-time pipeline execution status."""
    st.title("⚡ Pipeline Status")
    
    # This would connect to your running pipeline
    # and show progress in real-time
    
    if st.button("Refresh Status"):
        st.rerun()
    
    # Show current/recent runs
    # ... implementation ...
```

## Summary

This integration plan provides:

1. **Minimal Disruption**: Core evaluation logic untouched
2. **Better Abstraction**: LiteLLM handles provider differences
3. **Configuration-Based**: YAML files for easy model management
4. **Automation**: Single command runs with resume/skip
5. **Clean Codebase**: Removed orphaned frontend
6. **Enhanced Monitoring**: Streamlit dashboard improvements

The key insight is that LiteLLM and LangChain serve different purposes and can work together:
- **LiteLLM**: Unified API interface across providers
- **LangChain**: Context management without truncation

This gives you the best of both worlds while maintaining your carefully crafted evaluation pipeline.
