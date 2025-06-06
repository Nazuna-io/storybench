# StoryBench v1.4 to v1.5 Migration Guide

## Overview

StoryBench v1.5 introduces major improvements including automated pipeline execution, interactive Streamlit dashboard, and unified LiteLLM integration. This guide helps you migrate from v1.4 to v1.5.

## 🔄 Migration Steps

### 1. Backup Your Current Setup

```bash
# Backup your current configuration
cp -r config config_v14_backup
cp .env .env_v14_backup

# Backup any custom evaluation results
cp -r output output_v14_backup
```

### 2. Update Configuration Format

**v1.4 Configuration** (Python files):
```python
# models.py
MODELS = {
    'gpt-4': {'enabled': True, 'max_tokens': 2000}
}
```

**v1.5 Configuration** (YAML files):
```yaml
# config/models.yaml
models:
  gpt-4:
    enabled: true
    provider: openai
    model_name: gpt-4
    max_tokens: 2000
    temperature: 0.7
```

**Migration Command:**
```bash
# Copy the example configuration
cp config/models.example.yaml config/models.yaml
# Edit config/models.yaml with your models and settings
```

### 3. Update Environment Variables

Add new required environment variables to your `.env` file:

```env
# Existing variables (keep these)
MONGODB_URI=your_mongodb_connection_string
OPENAI_API_KEY=your_openai_key

# New in v1.5 (add these)
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key  
DEEPINFRA_API_KEY=your_deepinfra_key
```

### 4. Update Dependencies

```bash
# Install new dependencies
pip install -r requirements.txt
pip install -r streamlit_dashboard/requirements.txt
```

### 5. Database Migration

**No database schema changes required!** Your existing MongoDB data is fully compatible with v1.5.

The new dashboard will automatically work with your existing:
- Response collections
- Evaluation collections  
- All historical data

### 6. Update Evaluation Scripts

**v1.4 Evaluation Code:**
```python
from storybench.evaluators.api_evaluator import APIEvaluator

evaluator = APIEvaluator(provider="openai", model="gpt-4")
response = evaluator.evaluate_response(text, prompt, criteria)
```

**v1.5 Evaluation Code (Option 1 - New LiteLLM):**
```python
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator

evaluator = LiteLLMEvaluator(provider="openai", model="gpt-4")
response = evaluator.evaluate_response(text, prompt, criteria)
```

**v1.5 Evaluation Code (Option 2 - Backwards Compatible):**
```python
from storybench.evaluators.api_evaluator_adapter import APIEvaluatorAdapter

# Your existing code works unchanged!
evaluator = APIEvaluatorAdapter(provider="openai", model="gpt-4") 
response = evaluator.evaluate_response(text, prompt, criteria)
```

## 🚀 New Features You Can Use

### 1. Automated Pipeline Execution

Replace manual evaluation scripts with:

```bash
# Run all enabled models automatically
python run_automated_evaluation.py

# Advanced options
python run_automated_evaluation.py --dry-run
python run_automated_evaluation.py --force-rerun claude-opus-4,gpt-4o
```

### 2. Interactive Dashboard

Launch the new Streamlit dashboard:

```bash
cd streamlit_dashboard
streamlit run app.py
```

Access at `http://localhost:8501` for:
- 📊 Overview with key metrics
- 🏆 Model rankings and comparisons  
- 📈 Criteria analysis with heatmaps
- 🏢 Provider comparisons
- ⚡ Real-time progress monitoring
- 🔍 Advanced data exploration

### 3. Enhanced Testing

Run comprehensive tests:

```bash
python run_tests.py
```

## 🔧 Breaking Changes

### 1. Frontend Replacement

- **v1.4**: Vue.js frontend
- **v1.5**: Streamlit dashboard

**Migration**: The Vue.js frontend has been replaced with a more powerful Streamlit dashboard. No data migration needed - the dashboard automatically works with your existing evaluation data.

### 2. Configuration System

- **v1.4**: Python configuration files
- **v1.5**: YAML configuration files

**Migration**: Update your model configurations using the new YAML format shown above.

### 3. Docker Deployment

**v1.4 docker-compose.yml:**
```yaml
services:
  backend:
    # ... existing config
  frontend:
    # Vue.js frontend
```

**v1.5 docker-compose.yml:**
```yaml
services:
  backend:
    # ... existing config  
  dashboard:
    # Streamlit dashboard
```

**Migration**: Use the new `docker-compose.yml` file which includes the Streamlit dashboard service.

## 📊 Data Compatibility

### ✅ Fully Compatible
- All existing MongoDB collections
- Response data and evaluations
- Historical analysis and reports
- Evaluation criteria and scoring

### 🆕 Enhanced in v1.5
- Better score extraction from evaluation text
- Provider-level analysis (Anthropic, OpenAI, Google, DeepInfra)
- Real-time progress tracking
- Advanced statistical analysis

## 🐛 Troubleshooting

### Issue: "Module not found" errors
**Solution**: Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
pip install -r streamlit_dashboard/requirements.txt
```

### Issue: Configuration file errors
**Solution**: Verify your `config/models.yaml` follows the correct format:
```bash
python -c "import yaml; yaml.safe_load(open('config/models.yaml'))"
```

### Issue: Dashboard not loading data
**Solution**: Check your MongoDB connection:
```bash
python -c "from streamlit_dashboard.data_service import DataService; print(DataService().get_database_stats())"
```

### Issue: API key errors
**Solution**: Verify all required API keys are in your `.env` file and properly formatted.

## 📞 Support

If you encounter issues during migration:

1. Check the troubleshooting section above
2. Review the comprehensive test suite: `python run_tests.py`
3. Consult the detailed documentation in `docs/`
4. All your v1.4 data remains safe and accessible

## 🎉 Migration Complete!

Once migrated, you'll have access to:
- ⚡ **Automated evaluations** with one command
- 📊 **Interactive dashboard** with 6 analysis pages  
- 🔌 **Unified API access** to all major LLM providers
- 🧪 **Comprehensive testing** framework
- 📈 **Enhanced analytics** and insights

Your historical evaluation data will be immediately available in the new dashboard with enhanced visualization and analysis capabilities!
