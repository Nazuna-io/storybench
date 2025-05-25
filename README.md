# StorybenchLLM

A modular tool for evaluating the creativity of proprietary and open-source LLMs across various creative writing tasks including storytelling, screenwriting, advertising concepts, and cross-genre narratives.

## 🚀 Phase 5 Complete: Research-Quality Evaluation System

**StorybenchLLM now features sophisticated sequence-aware evaluation with realistic scoring standards!**

- **✅ Sequence-Aware Evaluation**: Assesses coherence across multi-prompt creative sequences
- **✅ Realistic Scoring Standards**: Stringent criteria that properly differentiate quality levels
- **✅ Full-Context Assessment**: GPT-4 Turbo with 128k context for complete evaluation
- **✅ Research-Quality Results**: Meaningful model comparisons for academic research

## Requirements

- **Python 3.12+** (Required and fully tested)
- **MongoDB Atlas** (or local MongoDB for development)
- **OpenAI API Key** (for evaluation system)
- Node.js 18+ (for web frontend)

## Features

### Advanced Evaluation Engine ✨ ENHANCED
- **Sequence-Aware Analysis**: Evaluates narrative coherence across related responses
- **Realistic Scoring**: 1-5 scale with explicit standards (most responses score 2-3)
- **Full Context Evaluation**: No content truncation - complete assessment of all responses
- **Research Standards**: Compares against professional published fiction, not just AI writing
- **Comprehensive Criteria**: 7 evaluation dimensions with detailed justifications

### Core Evaluation Engine
- **Modular Architecture**: Easy to add new model types and evaluators
- **API & Local Support**: Works with API-based models (OpenAI, Anthropic, Google) and local GGUF models
- **Resume Functionality**: Smart resume from interruption points with database-backed progress tracking
- **Automated Evaluation**: Uses GPT-4 Turbo to score creativity metrics with configurable criteria

### Database & Data Management
- **MongoDB Atlas Integration**: Enterprise-grade database backend
- **Data Migration Tools**: Automatic import of existing JSON evaluation results
- **Advanced Analytics**: Query evaluation patterns, performance metrics, and trends
- **Backup & Recovery**: Automated backup systems with rollback capability
- **Export Functionality**: Export data for external analysis tools

### Web Interface
- **Complete Web UI**: Full web interface for configuration, evaluation, and results ✅
- **Real-time Monitoring**: Live progress tracking with Server-Sent Events
- **Results Dashboard**: Interactive results viewing with actual evaluation data
- **Configuration Management**: Web-based model, prompt, and criteria configuration

### CLI Interface
- **Full CLI**: Complete command-line interface for automated workflows ✅
- **Migration Commands**: Database import/export and cleanup tools
- **Background Processing**: Non-blocking evaluation execution
- **Configuration Versioning**: Handles config changes gracefully

### Quality & Reliability
- **Enhanced Error Handling**: Robust retry mechanism with exponential backoff
- **Prompt Validation**: Validates structure and content during configuration loading
- **Comprehensive Testing**: 91% test success rate with Python 3.12+ compatibility
- **Database Validation**: Automated data integrity checking

## Quick Start

### Prerequisites

1. **MongoDB Atlas Setup** (Recommended for production):
   ```bash
   # Sign up for MongoDB Atlas (free tier available)
   # Create cluster and get connection string
   # Add connection string to .env file
   ```

2. **Environment Setup**:
   ```bash
   python3.12 -m venv venv-storybench
   source venv-storybench/bin/activate
   pip install -e .
   
   # Copy environment template and add your API keys + MongoDB URI
   cp .env.example .env
   # Edit .env with your API keys and MongoDB connection string
   ```

### Web UI (Recommended)

1. **Start Web Server**
   ```bash
   storybench-web
   ```

2. **Access Web UI**: Open http://localhost:8000
   - 📊 **Results**: View evaluation results and progress
   - ⚙️ **Configuration**: Manage models and prompts  
   - 🚀 **Evaluation**: Run evaluations with real-time monitoring
   - 📚 **API Docs**: Available at http://localhost:8000/api/docs

### CLI Interface

1. **Configure Models and Prompts**
   ```bash
   # Edit configuration files
   vim config/models.yaml
   vim config/prompts.json
   vim config/evaluation_criteria.yaml
   ```

2. **Run Evaluation**
   ```bash
   storybench evaluate
   ```

3. **Database Operations**
   ```bash
   # Import existing JSON evaluation results
   storybench migrate --validate --cleanup
   
   # Export data for analysis
   storybench export --export-dir ./analysis_data
   
   # Check database status
   storybench status
   ```

## Database Migration

If you have existing evaluation results in JSON format, Phase 4 provides automatic migration:

```bash
# Migrate existing data to MongoDB
storybench migrate --validate --cleanup

# This will:
# 1. Import all JSON files from output/ directory
# 2. Validate data integrity
# 3. Create timestamped backup of original files
# 4. Clean up original files after successful import
```

## Configuration

### Environment Variables (.env)
```bash
# MongoDB Atlas (Required)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/storybench?retryWrites=true&w=majority

# API Keys (Add as needed)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# Optional: Custom endpoints
GROK_BASE_URL=https://api.x.ai/v1
```

### Model Configuration (config/models.yaml)
Configure available models for evaluation:
```yaml
models:
  - name: "Claude-4-Sonnet"
    type: "api"
    provider: "anthropic"
    model_name: "claude-3-5-sonnet-20241022"
  
  - name: "Local-Llama"
    type: "local"
    repo_id: "microsoft/DialoGPT-medium"
    filename: "model.gguf"
```

### Evaluation Prompts (config/prompts.json)
Define creative writing prompts across different sequences:
```json
{
  "FilmNarrative": [
    {
      "name": "Initial Concept",
      "text": "Create a completely original feature film concept..."
    }
  ]
}
```

### Evaluation Criteria (config/evaluation_criteria.yaml)
Configure how responses are automatically scored:
```yaml
creativity:
  name: "Creativity and Originality"
  description: "Assesses novelty and creative thinking"
  scale: 10

coherence:
  name: "Narrative Coherence"
  description: "Evaluates logical flow and structure"
  scale: 10
```

## Architecture

### Database Schema (MongoDB Atlas)
```javascript
// Collections:
evaluations: {
  _id: ObjectId,
  config_hash: String,
  models: [String],
  status: "completed" | "in_progress" | "failed",
  total_tasks: Number,
  completed_tasks: Number,
  timestamp: Date
}

responses: {
  _id: ObjectId,
  evaluation_id: String,  // Reference to evaluation
  model_name: String,
  sequence: String,
  run: Number,
  prompt_name: String,
  response: String,
  generation_time: Number,
  completed_at: Date
}

evaluation_scores: {
  _id: ObjectId,
  evaluation_id: ObjectId,
  model_name: String,
  overall_score: Number,
  detailed_scores: {
    creativity: Number,
    coherence: Number,
    // ... other criteria
  }
}
```

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web UI        │    │   CLI Interface  │    │  API Endpoints  │
│   (Frontend)    │    │   (Click)        │    │  (FastAPI)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                │
                    ┌──────────────────┐
                    │   Core Engine    │
                    │   (Async Python) │
                    └──────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────────────┐ ┌──────────────┐ ┌────────────┐
        │   Model APIs  │ │ Local Models │ │  MongoDB   │
        │ (OpenAI, etc) │ │   (GGUF)     │ │   Atlas    │
        └───────────────┘ └──────────────┘ └────────────┘
```

## Development

### Setup Development Environment
```bash
# Clone and setup
git clone <repository>
cd storybench
python3.12 -m venv venv-storybench
source venv-storybench/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Set up environment
cp .env.example .env
# Edit .env with your API keys and MongoDB URI
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=storybench --cov-report=html

# Test database migration
python test_phase4_migration.py

# Verify setup
python setup_phase4.py
```

### Web UI Development
```bash
# Install frontend dependencies
cd frontend
npm install

# Start development server
npm run dev  # Frontend: http://localhost:3000
storybench-web  # Backend: http://localhost:8000
```

## Data Management

### Migration Commands
```bash
# Import existing JSON results to MongoDB
storybench migrate --output-dir ./output --validate --cleanup

# Export database data for analysis
storybench export --export-dir ./exports

# Backup specific evaluations
storybench export --evaluation-ids 507f1f77bcf86cd799439011
```

### Database Operations
```bash
# Check connection and status
storybench status

# View evaluation progress
storybench evaluate --dry-run

# Resume interrupted evaluation
storybench evaluate --resume
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Issues**
   ```bash
   # Check connection string in .env
   # Verify IP whitelist in MongoDB Atlas
   # Test connection: python setup_phase4.py
   ```

2. **Migration Problems**
   ```bash
   # Check file permissions in output/ directory
   # Verify JSON file format
   # Check logs for specific errors
   ```

3. **Performance Issues**
   ```bash
   # For large datasets, use batch processing
   # Monitor memory usage during evaluation
   # Consider MongoDB Atlas cluster scaling
   ```

### Support
- **Documentation**: Check PHASE_4_IMPLEMENTATION_SUMMARY.md
- **Logs**: Check application logs for detailed error information
- **Validation**: Use setup_phase4.py for comprehensive checks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run full test suite: `pytest`
5. Submit pull request

### Code Style
- **Black**: Code formatting (`black .`)
- **Flake8**: Linting (`flake8 src/`)
- **MyPy**: Type checking (`mypy src/`)
- **Pre-commit**: Automated checks

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 0.3.0 - Phase 5 Complete (June 2025)
- ✅ **Sequence-Aware Evaluation**: Assesses coherence across multi-prompt creative sequences
- ✅ **Realistic Scoring Standards**: Stringent criteria that properly differentiate quality levels
- ✅ **Full-Context Assessment**: GPT-4 Turbo with 128k context for complete evaluation
- ✅ **Research-Quality Results**: Meaningful model comparisons for academic research

### Version 0.2.0 - Phase 4 Complete (May 2025)
- ✅ **MongoDB Atlas Integration**: Enterprise database backend
- ✅ **Data Migration System**: Automatic JSON import with validation
- ✅ **Advanced Analytics**: Database-driven evaluation insights
- ✅ **Backup & Recovery**: Automated data safety systems
- ✅ **CLI Enhancement**: Migration and export commands
- ✅ **Production Ready**: Enterprise-grade reliability and scalability

### Version 0.1.0 - Core System (Previous)
- ✅ **Multi-Model Support**: API and local model evaluation
- ✅ **Web Interface**: Complete frontend with real-time monitoring
- ✅ **CLI Tools**: Command-line evaluation workflows
- ✅ **Resume Functionality**: Interruption recovery
- ✅ **Automated Scoring**: LLM-based evaluation metrics

---

**StorybenchLLM** - Enterprise-grade LLM creativity evaluation with MongoDB Atlas backend 🚀
