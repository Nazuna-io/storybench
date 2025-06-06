# StoryBench v1.5 Changelog

## Overview
StoryBench v1.5 modernizes the evaluation pipeline with automated model management, unified API access through LiteLLM, and a comprehensive Streamlit dashboard for visualization and monitoring.

## Release Date
*In Development*

## Major Features

### 🔧 Configuration-Based Model Management
- **YAML Configuration**: Models now defined in `config/models.yaml`
- **Easy Model Addition**: No code changes required to add new models
- **Enable/Disable Toggle**: Simple flag to include/exclude models from evaluation
- **Centralized Settings**: All evaluation parameters in one place

### 🚀 Automated Pipeline Execution
- **Single Command Running**: `python run_automated_evaluation.py`
- **Smart Resume**: Automatically skip completed evaluations
- **Force Rerun**: Option to re-evaluate specific models
- **Progress Tracking**: Real-time progress with time estimates

### 🔌 LiteLLM Integration
- **Unified API Interface**: Single interface for all providers (OpenAI, Anthropic, Google, DeepInfra)
- **Preserved Context Management**: LangChain continues handling context without truncation
- **Simplified Provider Management**: Less code, more reliability
- **Backwards Compatible**: Works with existing evaluation pipeline

### 📊 Streamlit Dashboard
- **Overview Page**: Quick metrics and top performers
- **Model Rankings**: Interactive comparison charts
- **Criteria Analysis**: Box plots and heatmaps for evaluation criteria
- **Provider Comparison**: Performance analysis by company
- **Real-Time Progress**: Live pipeline monitoring
- **Data Explorer**: Filter and export evaluation data

### 🧹 Code Cleanup
- **Removed Orphaned Frontend**: Vue.js code removed
- **Consolidated Evaluators**: Reduced code duplication
- **Improved Error Handling**: Better recovery from failures
- **Enhanced Logging**: More detailed operation tracking

## Technical Improvements

### Architecture
- Modular design with clear separation of concerns
- Configuration-driven architecture
- Improved testability with dependency injection
- Better error boundaries and recovery

### Performance
- Optimized database queries
- Reduced API calls through better batching
- Caching for frequently accessed data
- Parallel processing where applicable

### Reliability
- Exponential backoff for retries
- Graceful degradation on failures
- Checkpoint saving for long runs
- Comprehensive error logging

## Migration Guide

### From v1.0 to v1.5
1. Back up your MongoDB database
2. Update environment variables (no changes required)
3. Install new dependencies: `pip install -r requirements.txt`
4. Copy `config/models.example.yaml` to `config/models.yaml`
5. Configure your models in the YAML file
6. Run: `python run_automated_evaluation.py`

### Breaking Changes
- None - v1.5 is fully backwards compatible

### Deprecated Features
- `APIEvaluator` class (use `LiteLLMEvaluator` instead)
- Manual model configuration in Python files
- Vue.js frontend (use Streamlit dashboard)

## Bug Fixes
- Fixed context truncation issues with large responses
- Resolved race conditions in concurrent evaluations
- Fixed memory leaks in long-running pipelines
- Corrected token counting for various providers

## Known Issues
- Dashboard may be slow with >10,000 evaluations (pagination coming in v1.6)
- Some DeepInfra models may require manual retry on timeout
- Real-time updates require manual refresh in some browsers

## Contributors
- Architecture Design: Todd
- Implementation: Claude (Anthropic)
- Testing: StoryBench Team

## Future Plans (v1.6)
- Multi-user dashboard support
- Automated model discovery from providers
- Custom evaluation criteria editor
- API endpoints for external integration
- Advanced scheduling and queuing

## Resources
- [Implementation Plan](./docs/v1.5_implementation_plan.md)
- [Configuration Guide](./docs/configuration_guide.md)
- [Dashboard Manual](./docs/dashboard_manual.md)
- [API Documentation](./docs/api_documentation.md)

---

*For questions or issues, please open a GitHub issue or contact the team.*
