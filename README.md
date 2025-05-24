# StorybenchLLM

A modular tool for evaluating the creativity of proprietary and open-source LLMs across various creative writing tasks including storytelling, screenwriting, advertising concepts, and cross-genre narratives.

## Features

- **Modular Architecture**: Easy to add new model types and evaluators
- **API & Local Support**: Works with API-based models (OpenAI, Anthropic, Google) and local GGUF models
- **Robust Resume**: Can recover from crashes and continue evaluations
- **Progress Tracking**: Real-time progress with incremental saves
- **Configuration Versioning**: Handles config changes gracefully
- **Automated Evaluation**: Uses LLMs to score creativity metrics
- **Enhanced API Error Handling**: Robust retry mechanism with exponential backoff for API-based model evaluations.
- **Prompt Validation**: Validates structure and content of `prompts.json` during configuration loading.

## Quick Start

1. **Setup Environment**
   ```bash
   python3.10 -m venv venv-storybench
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
   storybench evaluate --config config/models.yaml
   ```

## Configuration

- `config/models.yaml` - Model configurations and settings
- `config/prompts.json` - Creative writing prompts
- `config/evaluation_criteria.yaml` - Scoring criteria
- `.env` - API keys (not committed to git)

## Results

Results are saved in the `output/` directory as JSON files, one per model with automatic progress tracking and resume capability.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## TODO

- [ ] **Auto-evaluation**: Currently the system collects responses to prompts and outputs data files, but does not automatically evaluate response quality using LLMs
- [ ] **Local LLM Testing**: Local LLM capability needs proper setup and testing to ensure it works reliably
- [ ] **Web UI**: Add a web-based user interface for easier configuration and monitoring of evaluations

## Project Structure

```
storybench/
├── src/storybench/          # Main package
├── config/                  # Configuration files  
├── output/                  # Evaluation outputs (gitignored)
├── tests/                   # Test suite
└── models/                  # Downloaded local models (gitignored)
```
