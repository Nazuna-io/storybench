# StorybenchLLM

A modular tool for evaluating the creativity of proprietary and open-source LLMs across various creative writing tasks including storytelling, screenwriting, advertising concepts, and cross-genre narratives.

## Requirements

- **Python 3.12+** (Required and fully tested)
- Node.js 18+ (for web frontend)

## Features

- **Modular Architecture**: Easy to add new model types and evaluators
- **API & Local Support**: Works with API-based models (OpenAI, Anthropic, Google) and local GGUF models
- **Web UI**: Complete web interface for configuration, evaluation, and results ✅
- **CLI Interface**: Full command-line interface for automated workflows ✅
- **Real-time Monitoring**: Live progress tracking with Server-Sent Events
- **Resume Functionality**: Smart resume from interruption points with progress detection
- **Background Processing**: Non-blocking evaluation execution
- **Results Dashboard**: Interactive results viewing with actual evaluation data
- **Robust Resume**: Can recover from crashes and continue evaluations
- **Progress Tracking**: Real-time progress with incremental saves
- **Configuration Versioning**: Handles config changes gracefully
- **Automated Evaluation**: Uses LLMs to score creativity metrics
- **Enhanced API Error Handling**: Robust retry mechanism with exponential backoff
- **Prompt Validation**: Validates structure and content of `prompts.json` during configuration loading
- **Comprehensive Testing**: 91% test success rate with Python 3.12+ compatibility validated

## Quick Start

### Web UI (Recommended)
1. **Setup Environment**
   ```bash
   python3.12 -m venv venv-storybench
   source venv-storybench/bin/activate
   pip install -e .
   ```

2. **Start Web Server**
   ```bash
   storybench-web
   ```

3. **Access Web UI**: Open http://localhost:8000
   - 📊 **Results**: View evaluation results and progress
   - ⚙️ **Configuration**: Manage models and prompts  
   - 🚀 **Evaluation**: Run evaluations with real-time monitoring
   - 📚 **API Docs**: Available at http://localhost:8000/api/docs

### CLI Interface
1. **Setup Environment**
   ```bash
   python3.12 -m venv venv-storybench
   source venv-storybench/bin/activate  # On Windows: venv-storybench\Scripts\activate
   pip install -e .
   ```

2. **Configure API Keys**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run Evaluation**
   ```bash
   # Validate configuration first
   storybench validate
   
   # Run evaluation (dry-run for testing)
   storybench evaluate --dry-run
   
   # Run actual evaluation
   storybench evaluate
   
   # Clean up models when needed
   storybench clean --models
   ```

## Configuration

- `config/models.yaml` - Model configurations and settings
- `config/prompts.json` - Creative writing prompts
- `config/evaluation_criteria.yaml` - Scoring criteria
- `.env` - API keys (not committed to git)

## Results

Results are saved in the `output/` directory as JSON files, one per model with automatic progress tracking and resume capability.

## Development & Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run test suite
pytest                                    # All tests
pytest -k "not selenium"                 # Skip browser tests
pytest tests/test_basic.py -v            # Basic functionality tests
pytest tests/test_comprehensive_backend.py -v  # API tests
pytest tests/test_python312_compatibility.py -v # Python 3.12+ tests

# Test coverage: 91% success rate
# - 59 tests passing
# - 3 tests skipped (intentional)
# - 1 expected failure (xfailed)
# - Python 3.12+ compatibility fully validated
```

## Completed Features

- ✅ **Web UI**: Complete web interface with real-time monitoring
- ✅ **CLI Interface**: Full command-line functionality
- ✅ **Auto-evaluation**: System now automatically evaluates response quality using LLMs
- ✅ **Local LLM Support**: Local GGUF model capability working and tested
- ✅ **Python 3.12+ Support**: Fully compatible and tested with Python 3.12+
- ✅ **Comprehensive Testing**: Refactored test suite with high success rate
- ✅ **API Documentation**: Interactive API docs available

## Project Structure

```
storybench/
├── src/storybench/          # Main package
│   ├── cli.py              # Command-line interface
│   ├── evaluators/         # LLM evaluators (API & local)
│   ├── models/             # Configuration models
│   └── web/                # Web interface (FastAPI)
├── config/                  # Configuration files  
├── output/                  # Evaluation outputs (gitignored)
├── tests/                   # Comprehensive test suite
├── frontend/               # Vue.js web frontend
└── models/                 # Downloaded local models (gitignored)
```

## Python 3.12+ Compatibility

This project requires Python 3.12+ and has been fully tested for compatibility:

- ✅ **Type annotations**: Modern typing with `Optional`, `List`, `Dict`
- ✅ **Async/await**: Full asyncio compatibility
- ✅ **Pathlib**: Modern path handling
- ✅ **FastAPI**: Web framework compatibility
- ✅ **Dependencies**: All major dependencies support Python 3.12+
- ✅ **Testing**: Comprehensive test suite validates 3.12+ functionality
