# Storybench Web Interface

## Phase 1 - FastAPI Backend Foundation ✅
## Phase 2 - Enhanced Validation & API Testing ✅

The first two phases of the web interface implementation are now complete!

### ✅ Phase 1 Features (Completed)

- **FastAPI Application Structure**: Complete backend framework with automatic OpenAPI documentation
- **Repository Abstraction Layer**: Clean separation between data access and business logic
- **Configuration Management**: API endpoints for reading and updating model configurations
- **API Key Management**: Secure handling with masking for display
- **Prompts Management**: CRUD operations for creative writing prompts
- **Validation Framework**: Configuration validation with error reporting
- **File-based Storage**: Working with existing YAML/JSON configuration files

### ✅ Phase 2 Features (Completed)

- **Real API Connectivity Testing**: Live testing of OpenAI, Anthropic, and Google/Gemini APIs
- **Lightweight Testing Mode**: Fast API validation using minimal requests (100-500ms)
- **Full Evaluator Testing**: Comprehensive model setup testing for thorough validation
- **Intelligent Error Handling**: User-friendly error messages with 30-second timeout protection
- **Model-Specific Validation**: Tests each configured model individually with detailed reporting
- **Performance Metrics**: Response time tracking and success rate monitoring

### 🚧 API Endpoints (Phases 1 & 2)

#### Configuration Management
- `GET /api/config/models` - Get current model configurations
- `PUT /api/config/models` - Update model configurations  
- `GET /api/config/api-keys` - Get masked API keys
- `PUT /api/config/api-keys` - Update API keys
- `GET /api/config/prompts` - Get current prompts
- `PUT /api/config/prompts` - Update prompts
- `GET /api/config/evaluation-criteria` - Get evaluation criteria
- `PUT /api/config/evaluation-criteria` - Update criteria

#### Enhanced Validation (Phase 2)
- `POST /api/config/validate` - Comprehensive configuration and API testing
  - Real API connectivity testing
  - Lightweight and full testing modes
  - Performance metrics and error reporting

#### Placeholder Endpoints (for future phases)
- `POST /api/evaluations/start` - Start evaluation (Phase 5)
- `GET /api/evaluations/status` - Get evaluation status (Phase 5)
- `GET /api/results` - Get evaluation results (Phase 4)

### 🛠️ Running the Backend

```bash
# Install dependencies (if not already done)
pip install -e .

# Start the development server
storybench-web

# Or manually with uvicorn
uvicorn storybench.web.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Base URL**: http://localhost:8000/api/
- **Interactive Documentation**: http://localhost:8000/api/docs
- **Alternative Documentation**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/health

### 📋 Next Steps - Phase 3

The next phase will implement:
- **Vue.js Frontend Foundation**: Modern responsive web interface
- **Configuration Management UI**: Interactive forms for model and API key management
- **Real-time Validation Interface**: Live API testing with visual feedback
- **Interactive Dashboard**: User-friendly interface for all configuration tasks

### 🏗️ Architecture

```
src/storybench/web/
├── main.py                 # FastAPI application entry point
├── api/                    # REST API endpoints
│   ├── models.py          # Model configuration endpoints
│   ├── prompts.py         # Prompt management endpoints  
│   ├── validation.py      # Configuration validation endpoints
│   ├── evaluations.py     # Evaluation execution endpoints (placeholder)
│   └── results.py         # Results retrieval endpoints (placeholder)
├── services/
│   └── config_service.py  # Configuration management business logic
├── models/
│   ├── requests.py        # Pydantic request models
│   └── responses.py       # Pydantic response models
└── repositories/
    ├── base.py           # Abstract repository interface
    └── file_repository.py # File-based data access implementation
```

### 🔧 Configuration

The web interface uses the same configuration files as the CLI:
- `config/models.yaml` - Model configurations and settings
- `config/prompts.json` - Creative writing prompts  
- `config/evaluation_criteria.yaml` - Scoring criteria
- `.env` - API keys (securely masked in API responses)

All configuration changes through the web interface immediately update the underlying files that the CLI uses, ensuring full compatibility between both interfaces.
