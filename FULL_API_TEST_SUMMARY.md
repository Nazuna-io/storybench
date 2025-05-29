# Full API Production Test - Summary

## Overview
Created `test_full_api_production.py` - a comprehensive production pipeline test that validates the complete storybench system according to your specifications.

## Features Implemented

### ✅ Directus Integration
- **Prompts**: Fetches 15 prompts from Directus (5 sequences × 3 prompts each)
- **Evaluation Criteria**: Fetches 7 evaluation criteria from Directus  
- **No hardcoded prompts or criteria** - everything comes from Directus CMS
- **Version validation** - ensures correct number of sequences and criteria

### ✅ API Connectivity & Model Validation
- **API Connectivity Testing**: Tests all 4 providers (Anthropic, OpenAI, Google, DeepInfra)
- **Model Name Validation**: Tests each of the 13 models with actual generation
- **Latest Model Variants**: Uses the model names from api-models-list.txt as specified
- **Error Handling**: Graceful handling of failed connections and invalid models

### ✅ Complete Pipeline Execution
- **13 Models**: All models from api-models-list.txt
- **3 Runs per Sequence**: As designed for coherence testing
- **Context Resets**: Between sequences (not between prompts within sequence)
- **Gemini 2.5 Pro Evaluator**: Uses the specified evaluation model
- **MongoDB Storage**: All responses and evaluations stored in production database

### ✅ Sequence-Aware Processing
- **Coherence Testing**: Maintains context within sequences, resets between sequences
- **Sequence Evaluation**: Evaluates complete sequences for narrative coherence
- **Proper Run Structure**: 5 sequences × 3 runs = 15 sequence runs per model

## Expected Output
- **Total Responses**: 13 models × 15 prompts × 3 runs = **585 responses**
- **Total Evaluations**: 13 models × 15 prompts × 3 runs = **585 evaluations**
- **Sequence Runs**: 13 models × 5 sequences × 3 runs = **195 sequence runs**

## Pipeline Steps
1. **Environment Validation** - Check required environment variables
2. **Model Loading** - Load 13 models from api-models-list.txt
3. **API Connectivity Testing** - Test all providers with lightweight tests
4. **Model Name Validation** - Validate each model with actual generation
5. **Directus Prompts** - Fetch and validate 15 prompts (5 sequences × 3)
6. **Directus Evaluation Criteria** - Fetch and validate 7 criteria
7. **Gemini Evaluator Setup** - Setup Gemini 2.5 Pro for evaluation
8. **Database Connection** - Connect to MongoDB Atlas
9. **Pipeline Execution** - Generate responses and evaluations
10. **Results & Reporting** - Comprehensive JSON report

## Usage
```bash
cd /home/todd/storybench
venv-storybench/bin/python test_full_api_production.py
```

## Requirements
The script validates that you have all necessary environment variables:
- `DIRECTUS_URL` and `DIRECTUS_TOKEN`
- `MONGODB_URI` 
- `GOOGLE_API_KEY` (for Gemini 2.5 Pro evaluator)
- Provider API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPINFRA_API_KEY`

## Output
- Real-time progress reporting with emojis and clear status indicators
- Comprehensive JSON report saved as `full_api_production_test_report_YYYYMMDD_HHMMSS.json`
- Validation results for connectivity and model names
- Performance metrics and success rates
- Error logging for debugging

This test script fully validates your production API pipeline and ensures all components work together as designed.
