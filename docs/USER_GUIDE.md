    prompt="Write a creative story...",
    criteria="Evaluate for creativity and coherence..."
)
```

### Docker Deployment

For production deployment:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Services available:
# - Backend API: http://localhost:8000
# - Dashboard: http://localhost:8501
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError: No module named 'storybench'`

**Solution**: 
```bash
# Ensure you're in the virtual environment
source venv-storybench/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Database Connection Issues
**Problem**: Cannot connect to MongoDB

**Solutions**:
```bash
# Check connection string format
echo $MONGODB_URI

# Test connection
python -c "from pymongo import MongoClient; print(MongoClient(os.getenv('MONGODB_URI')).admin.command('ping'))"

# Verify IP whitelist in MongoDB Atlas
# Ensure your IP is whitelisted or use 0.0.0.0/0 for testing
```

#### 3. API Key Issues
**Problem**: Authentication errors with LLM providers

**Solutions**:
```bash
# Verify API keys are set
env | grep API_KEY

# Test specific provider
python -c "
import os
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator
evaluator = LiteLLMEvaluator('openai', 'gpt-3.5-turbo')
print('API key working!')
"
```

#### 4. Dashboard Not Loading Data
**Problem**: Dashboard shows "No data available"

**Solutions**:
```bash
# Check data service connection
cd streamlit_dashboard
python -c "
from data_service import DataService
ds = DataService()
print(ds.get_database_stats())
"

# Verify collections exist
python -c "
from pymongo import MongoClient
import os
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['storybench']
print('Collections:', db.list_collection_names())
"
```

#### 5. Configuration Errors
**Problem**: YAML configuration file errors

**Solutions**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/models.yaml'))"

# Check required fields
python -c "
from storybench.config_loader import ConfigLoader
config = ConfigLoader()
print('Enabled models:', len(config.get_enabled_models()))
"
```

### Performance Optimization

#### Large Dataset Handling
For datasets with 1000+ responses:
- Use the Data Explorer's filtering capabilities
- Export subsets to CSV for external analysis
- Consider pagination in custom scripts

#### Memory Management
```bash
# Monitor memory usage during evaluations
python run_automated_evaluation.py --dry-run  # Check load first

# For large runs, process in batches
# Edit config/models.yaml to enable fewer models at once
```

### Logging and Debugging

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Check Evaluation Logs
```bash
# View recent evaluation logs
ls -la logs/

# Monitor real-time progress
tail -f evaluation_progress_*.json
```

### Getting Help

1. **Check Documentation**: Review all files in `docs/` directory
2. **Run Tests**: Execute `python run_tests.py` to validate setup
3. **Sample Data**: Use dry-run mode to test without API calls
4. **Community**: Check GitHub issues and discussions

### Recovery Procedures

#### Corrupted Evaluation Run
```bash
# Remove progress file to restart
rm evaluation_progress_*.json

# Start fresh evaluation
python run_automated_evaluation.py --no-resume
```

#### Database Recovery
```bash
# Export current data
python export_complete_data.py

# Verify data integrity
python -c "
from pymongo import MongoClient
import os
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['storybench']
print('Responses:', db.responses.count_documents({}))
print('Evaluations:', db.response_llm_evaluations.count_documents({}))
"
```

## Best Practices

### 1. Evaluation Strategy
- Start with a small subset of models for testing
- Use dry-run mode to estimate costs before large evaluations
- Monitor progress files for cost tracking
- Keep API keys secure and rotate them regularly

### 2. Configuration Management
- Version control your `config/models.yaml` file
- Use descriptive model names and comments
- Test configuration changes with dry-runs
- Backup configurations before major changes

### 3. Data Management
- Regular exports of evaluation data
- Monitor MongoDB storage usage
- Clean up test evaluations periodically
- Document evaluation criteria versions

### 4. Dashboard Usage
- Use filtering in Data Explorer for focused analysis
- Export key insights to CSV for reports
- Monitor real-time progress during long evaluations
- Save important visualizations as screenshots

### 5. Production Deployment
- Use Docker for consistent environments
- Set up monitoring for API costs
- Implement backup strategies for data
- Use environment-specific configurations

---

## Next Steps

After completing this user guide:
1. Try the Quick Start tutorial
2. Explore the dashboard with your data
3. Review the API documentation for custom integrations
4. Check out advanced usage examples

For additional help, consult:
- `docs/API_REFERENCE.md` - Detailed API documentation
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/TROUBLESHOOTING.md` - Extended troubleshooting guide
