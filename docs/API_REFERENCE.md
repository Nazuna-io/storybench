# StoryBench v1.5 API Reference

## Overview

StoryBench v1.5 provides a comprehensive API for automated creative writing evaluation. This reference covers all major components and their usage.

## Core Components

### ConfigLoader

Manages YAML-based configuration for models and evaluation settings.

```python
from storybench.config_loader import ConfigLoader

# Initialize with default config path
config = ConfigLoader()

# Use custom config file
config = ConfigLoader(config_path="custom/models.yaml")

# Get enabled models
enabled_models = config.get_enabled_models()
# Returns: List[Dict] with model configurations

# Get all models (enabled and disabled)
all_models = config.get_all_models()

# Get specific model configuration
model_config = config.get_model_config("claude-opus-4")
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get_enabled_models()` | None | `List[Dict]` | Returns all enabled model configurations |
| `get_all_models()` | None | `List[Dict]` | Returns all model configurations |
| `get_model_config(name)` | `name: str` | `Dict` | Returns specific model configuration |

### LiteLLMEvaluator

Unified evaluator using LiteLLM for all provider integrations.

```python
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator

# Initialize evaluator
evaluator = LiteLLMEvaluator(
    provider="anthropic",           # Required: openai, anthropic, google, deepinfra
    model="claude-3-opus-20240229", # Required: model identifier
    api_key="sk-ant-...",          # Optional: uses env var if not provided
    max_tokens=2000,               # Optional: default 2000
    temperature=0.7                # Optional: default 0.7
)

# Evaluate a response
response = evaluator.evaluate_response(
    response_text="The generated story...",
    prompt="Write a creative story about...",
    criteria="Evaluate for creativity, coherence..."
)

# Response object contains:
# - content: evaluation text
# - usage: token usage statistics  
# - cost: estimated cost
# - metadata: additional information
```

**Constructor Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | `str` | Yes | API provider: openai, anthropic, google, deepinfra |
| `model` | `str` | Yes | Model identifier for the provider |
| `api_key` | `str` | No | API key (uses environment variable if not provided) |
| `max_tokens` | `int` | No | Maximum tokens for responses (default: 2000) |
| `temperature` | `float` | No | Sampling temperature 0.0-1.0 (default: 0.7) |

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `evaluate_response()` | `response_text, prompt, criteria` | `Response` | Evaluates a single response |
| `get_usage_stats()` | None | `Dict` | Returns cumulative usage statistics |
| `get_cost_estimate()` | None | `float` | Returns estimated total cost |

### APIEvaluatorAdapter

Backwards compatibility adapter for existing v1.4 code.

```python
from storybench.evaluators.api_evaluator_adapter import APIEvaluatorAdapter

# Drop-in replacement for old APIEvaluator
evaluator = APIEvaluatorAdapter(
    provider="openai",
    model="gpt-4"
)

# Same interface as v1.4
response = evaluator.evaluate_response(text, prompt, criteria)
```

### AutomatedEvaluationRunner

High-level interface for running complete evaluation pipelines.

```python
from run_automated_evaluation import AutomatedEvaluationRunner

# Initialize runner
runner = AutomatedEvaluationRunner(
    config_path="config/models.yaml",
    dry_run=False,
    force_rerun=["claude-opus-4"],  # Optional: force specific models
    no_resume=False                 # Optional: ignore previous progress
)

# Run evaluation pipeline
results = await runner.run_evaluation_pipeline()

# Check progress
progress = runner.get_progress_summary()
```

## Data Models

### Response

Represents an LLM response with metadata.

```python
from storybench.models.response import Response

response = Response(
    content="The evaluation text...",
    usage={
        "prompt_tokens": 150,
        "completion_tokens": 200,
        "total_tokens": 350
    },
    cost=0.0023,
    metadata={
        "model": "claude-opus-4",
        "provider": "anthropic",
        "timestamp": "2025-06-03T10:30:00Z"
    }
)
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `str` | The main response content |
| `usage` | `Dict` | Token usage statistics |
| `cost` | `float` | Estimated cost in USD |
| `metadata` | `Dict` | Additional metadata |

### EvaluationProgress

Tracks progress of automated evaluation runs.

```python
from run_automated_evaluation import EvaluationProgress

progress = EvaluationProgress(
    total_models=5,
    completed_models=3,
    skipped_models=1,
    failed_models=0,
    total_cost=2.45,
    start_time="2025-06-03T10:00:00Z"
)
```

## Dashboard Components

### DataService

Handles database connections and data processing for the dashboard.

```python
from streamlit_dashboard.data_service import DataService

# Initialize service
service = DataService()

# Get database statistics
stats = service.get_database_stats()
# Returns: Dict with response counts, model counts, etc.

# Get performance data with extracted scores
performance_df = service.get_model_performance_data()
# Returns: pandas.DataFrame with scores by model and criteria

# Extract scores from evaluation text
scores = service.extract_scores_from_evaluation(evaluation_text)
# Returns: Dict mapping criteria to scores
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_database_stats()` | `Dict` | Database statistics and counts |
| `get_model_performance_data()` | `DataFrame` | Performance data with extracted scores |
| `extract_scores_from_evaluation(text)` | `Dict` | Extract scores from evaluation text |

## Database Schema

### Collections

StoryBench uses MongoDB with the following collections:

#### responses
```json
{
  "_id": "ObjectId",
  "text": "Generated response text",
  "prompt_name": "creative_story",
  "sequence_name": "storytelling",
  "model_name": "claude-opus-4",
  "model_type": "api",
  "model_provider": "anthropic",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "created_at": "2025-06-03T10:30:00Z",
  "generation_time": 2.34,
  "test_run": false,
  "batch_id": "batch_20250603_103000"
}
```

#### response_llm_evaluations
```json
{
  "_id": "ObjectId",
  "response_id": "ObjectId (references responses)",
  "evaluating_llm_provider": "google",
  "evaluating_llm_model": "gemini-2.5-pro",
  "evaluation_criteria_version": "directus_v1",
  "evaluation_text": "**creativity**: 4.5 - Excellent...",
  "evaluation_time": 1.23,
  "created_at": "2025-06-03T10:35:00Z",
  "test_run": false,
  "test_batch": "eval_batch_20250603"
}
```

## Provider-Specific Configuration

### OpenAI
```yaml
gpt-4o:
  enabled: true
  provider: openai
  model_name: gpt-4o
  max_tokens: 2000
  temperature: 0.7
```

### Anthropic
```yaml
claude-opus-4:
  enabled: true
  provider: anthropic
  model_name: claude-3-opus-20240229
  max_tokens: 4000
  temperature: 0.5
```

### Google
```yaml
gemini-2.5-pro:
  enabled: true
  provider: google
  model_name: gemini-pro
  max_tokens: 2048
  temperature: 0.7
```

### DeepInfra
```yaml
deepseek-r1:
  enabled: true
  provider: deepinfra
  model_name: deepseek-ai/DeepSeek-R1
  max_tokens: 1000
  temperature: 0.6
```

## Error Handling

### Common Exceptions

```python
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluatorError

try:
    response = evaluator.evaluate_response(text, prompt, criteria)
except LiteLLMEvaluatorError as e:
    print(f"Evaluation failed: {e}")
    # Handle specific error types
    if "rate_limit" in str(e):
        # Wait and retry
        time.sleep(60)
    elif "invalid_api_key" in str(e):
        # Check API key configuration
        pass
```

### Retry Logic

Built-in retry logic with exponential backoff:

```python
evaluator = LiteLLMEvaluator(
    provider="openai",
    model="gpt-4",
    max_retries=3,          # Number of retry attempts
    retry_delay=1.0,        # Initial delay in seconds
    backoff_factor=2.0      # Exponential backoff multiplier
)
```

## Testing

### Unit Tests

```python
import pytest
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator

def test_evaluator_initialization():
    evaluator = LiteLLMEvaluator("openai", "gpt-3.5-turbo")
    assert evaluator.provider == "openai"
    assert evaluator.model == "gpt-3.5-turbo"

def test_score_extraction():
    from streamlit_dashboard.data_service import DataService
    service = DataService()
    
    text = "**creativity**: 4.5\\n**coherence**: 4.0"
    scores = service.extract_scores_from_evaluation(text)
    
    assert scores["creativity"] == 4.5
    assert scores["coherence"] == 4.0
```

### Integration Tests

```python
@pytest.mark.integration
def test_full_evaluation_pipeline():
    from storybench.config_loader import ConfigLoader
    from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator
    
    config = ConfigLoader()
    models = config.get_enabled_models()
    
    for model_config in models[:1]:  # Test first model only
        evaluator = LiteLLMEvaluator(**model_config)
        response = evaluator.evaluate_response(
            "Test response",
            "Test prompt", 
            "Test criteria"
        )
        assert response.content is not None
```

## Utilities

### Cost Tracking

```python
# Track costs across multiple evaluations
total_cost = 0.0

for model_config in enabled_models:
    evaluator = LiteLLMEvaluator(**model_config)
    
    for prompt in prompts:
        response = evaluator.evaluate_response(...)
        total_cost += response.cost
        
print(f"Total evaluation cost: ${total_cost:.4f}")
```

### Progress Monitoring

```python
import json
from datetime import datetime

# Read progress file
with open("evaluation_progress_20250603_103000.json", "r") as f:
    progress = json.load(f)

# Check completion status
for model_name, model_progress in progress["models"].items():
    completion_pct = (model_progress["completed"] / model_progress["total"]) * 100
    print(f"{model_name}: {completion_pct:.1f}% complete")
```

## Performance Optimization

### Batch Processing

```python
# Process evaluations in batches
batch_size = 10
responses = get_responses_to_evaluate()

for i in range(0, len(responses), batch_size):
    batch = responses[i:i+batch_size]
    
    # Process batch
    for response in batch:
        evaluation = evaluator.evaluate_response(...)
        save_evaluation(evaluation)
    
    # Optional: pause between batches
    time.sleep(1)
```

### Memory Management

```python
# For large datasets, use generators
def get_responses_generator():
    cursor = db.responses.find()
    for doc in cursor:
        yield doc

# Process one at a time instead of loading all into memory
for response in get_responses_generator():
    process_response(response)
```

---

This API reference provides comprehensive coverage of StoryBench v1.5 components. For usage examples and tutorials, see the User Guide. For deployment information, consult the Deployment Guide.
