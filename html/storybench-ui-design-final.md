# Storybench Web UI Implementation Design Document

## Project Overview

**Project Name:** Storybench Web UI  
**Purpose:** Create a modern web interface for the Storybench LLM creativity evaluation system  
**Architecture:** FastAPI backend + Vue.js frontend with Server-Sent Events  
**Target:** Web-first responsive design for internal tool usage

## System Architecture

### Backend: FastAPI Server

- **Framework:** FastAPI with async support and automatic OpenAPI documentation
- **Integration:** Wraps existing Python CLI functionality without modification
- **Real-time:** Server-Sent Events (SSE) for evaluation progress and console output
- **Data:** File-based storage (JSON/YAML) with MongoDB-ready abstraction layer

### Frontend: Vue.js SPA

- **Framework:** Vue.js 3 with Composition API
- **State Management:** Pinia for global state
- **Styling:** Tailwind CSS matching existing mockups
- **Design:** Web-first responsive with light/dark mode support

### File Structure

```
src/storybench/web/
├── main.py                 # FastAPI entry point
├── api/
│   ├── models.py          # Model configuration endpoints
│   ├── prompts.py         # Prompt management endpoints  
│   ├── evaluations.py     # Evaluation execution endpoints
│   ├── results.py         # Results retrieval endpoints
│   └── validation.py      # Configuration and API validation
├── services/
│   ├── config_service.py  # Configuration management logic
│   ├── eval_service.py    # Evaluation execution service
│   └── validation_service.py # API validation service
├── models/
│   ├── requests.py        # Pydantic request models
│   └── responses.py       # Pydantic response models
└── repositories/
    ├── base.py           # Abstract repository interface
    ├── file_repository.py # Current file-based implementation
    └── mongo_repository.py # Future MongoDB implementation

frontend/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/index.js
│   ├── stores/            # Pinia stores
│   ├── components/        # Reusable components
│   ├── views/            # Page components
│   └── utils/            # Helper functions
├── package.json
└── vite.config.js
```

## API Specification

### Configuration Management

- `GET /api/config/models` - Get current model configurations with existing values
- `PUT /api/config/models` - Update model configurations
- `GET /api/config/api-keys` - Get masked API keys
- `PUT /api/config/api-keys` - Update API keys
- `POST /api/config/validate` - Validate configuration and test API connections
- `GET /api/config/prompts` - Get current prompts
- `PUT /api/config/prompts` - Update prompts (increments version)
- `GET /api/config/evaluation-criteria` - Get evaluation criteria
- `PUT /api/config/evaluation-criteria` - Update criteria (increments version)

### Evaluation Management

- `POST /api/evaluations/start` - Start evaluation (auto-detects resume)
- `GET /api/evaluations/status` - Get current evaluation status
- `GET /api/evaluations/logs` - Stream console output via SSE
- `POST /api/evaluations/stop` - Stop running evaluation
- `GET /api/evaluations/resume-status` - Check resume capability

### Results Management

- `GET /api/results` - Get all results with version filtering
- `GET /api/results/versions` - Get list of configuration versions
- `GET /api/results/{model_name}` - Get specific model results
- `GET /api/results/{model_name}/version/{version}` - Version-specific results

## Data Models

### Configuration Version Management

```python
@dataclass
class ConfigVersion:
    version_hash: str        # 8-character hash
    prompts_hash: str
    criteria_hash: str
    global_settings_hash: str
    timestamp: datetime
```

### Result Structure (Enhanced)

```python
{
    "metadata": {
        "model_name": str,
        "config_version": str,  # Links to ConfigVersion
        "config_details": {
            "prompts_hash": str,
            "criteria_hash": str,
            "global_settings_hash": str
        },
        "timestamp": str,
        "last_updated": str
    },
    "sequences": {
        "FilmNarrative": {
            "run_1": [response_objects],
            "run_2": [response_objects], 
            "run_3": [response_objects]
        }
        # ... other sequences
    },
    "evaluation_scores": {
        "overall": float,
        "creativity": float,
        "coherence": float,
        # ... other criteria
    },
    "status": "completed" | "in_progress" | "failed"
}
```

### API Request/Response Models

```python
class ModelConfigRequest(BaseModel):
    name: str
    type: Literal["api", "local"]
    provider: Optional[str]
    model_name: str
    repo_id: Optional[str]
    filename: Optional[str]

class ValidationResponse(BaseModel):
    valid: bool
    config_errors: List[str]
    api_validation: Dict[str, Dict[str, Any]]
    model_validation: List[Dict[str, Any]]

class EvaluationStatus(BaseModel):
    running: bool
    current_model: Optional[str]
    progress: Dict[str, Any]
    can_resume: bool
    resume_info: Dict[str, Any]
```

## Core Features Implementation

### 1. Configuration Management

**Model Configuration:**

- Display current YAML values in forms
- Conditional fields based on model type (API vs Local)
- Real-time validation with error display
- API connectivity testing per provider

**API Key Management:**

- Masked display (`sk-...abc123`) with unmask toggle
- Secure storage and transmission
- Per-provider validation testing
- Status indicators (connected/error/untested)

**Prompt Management:**

- Simple textarea inputs grouped by sequence
- Character count and basic validation
- Version increment warning on save
- No rich text or preview features

### 2. Resume Functionality

**Implementation Strategy:**

1. Check existing results for current config version
2. Use `ProgressTracker.get_next_task()` to find resume point
3. Display resume status before evaluation start
4. Only resume within same configuration version

**User Interface:**

- Resume status display on evaluation page
- Progress indicators showing completed vs remaining
- Clear messaging about what will be resumed

### 3. Version Management

**Version Tracking:**

- Hash based on prompts + evaluation criteria + global settings
- Automatic increment when configuration changes
- Historical preservation of all results
- Version-aware result filtering

**Results Display:**

- Version column in main results table
- Version filter dropdown
- Ability to compare across versions
- Clear version identification in detailed views

### 4. Real-time Evaluation

**Server-Sent Events Implementation:**

- Console output streaming
- Progress updates
- Status changes
- Error notifications

**Frontend Updates:**

- Real-time progress bars
- Live console output display
- Automatic status refresh
- Graceful reconnection handling

## User Interface Specifications

### Page Layouts

**Dashboard (Main Results View):**

- Wide table with horizontal scroll on mobile
- Columns: Model Name, Version, Overall Score, Individual Criteria Scores
- Search and filter capabilities
- Sort by any column
- Click-through to detailed results

**Model Configuration:**

- Form layout with conditional field display
- Existing values pre-populated
- Validate button with status feedback
- Save confirmation with change summary

**Prompt Management:**

- Organized by prompt sequences
- Simple textarea inputs
- Add/remove prompts within sequences
- Save with version increment warning

**Evaluation Runner:**

- Model selection with resume indicators
- Start/stop/resume controls
- Real-time console output
- Progress tracking with estimates

### Design System

**Color Scheme:**

- Light mode: `bg-slate-50`, `text-[#0d141c]`, `border-[#cedbe8]`
- Dark mode: Automatic CSS variable switching
- Accent: `bg-[#0c7ff2]` for primary actions

**Typography:**

- Font family: `Inter, "Noto Sans", sans-serif`
- Headers: Bold, tracked spacing
- Body: Normal weight, readable line height

**Components:**

- Consistent button styles and states
- Form validation styling
- Loading states and spinners
- Toast notifications for actions

## Security & Validation

### Input Validation

- Pydantic models for all API endpoints
- Frontend form validation with real-time feedback
- File path traversal protection
- Configuration schema validation

### API Security

- API key encryption at rest
- Secure transmission of sensitive data
- Rate limiting on evaluation endpoints
- Comprehensive error handling

### Runtime Safety

- Configuration validation before execution
- API connectivity testing
- Resource availability checks
- Graceful degradation on failures

## Development Implementation Plan

### Phase 1: FastAPI Backend Foundation

**Tasks:**

- Set up FastAPI application structure
- Implement configuration management endpoints
- Create Pydantic models for validation
- Add API key masking/unmasking functionality

**Deliverables:**

- Working FastAPI server with automatic docs
- Configuration CRUD operations
- Basic validation framework

### Phase 2: Validation & Testing Infrastructure

**Tasks:**

- Implement configuration validation service
- Add API connectivity testing
- Create comprehensive error handling
- Set up logging framework

**Deliverables:**

- Validation endpoints with detailed feedback
- API testing functionality
- Error reporting system

### Phase 3: Frontend Foundation

**Tasks:**

- Set up Vue.js application with Vite
- Implement routing and layout components
- Create configuration management pages
- Add form validation and user feedback

**Deliverables:**

- Working Vue.js SPA
- Configuration management interface
- Real-time validation feedback

### Phase 4: Results & Versioning

**Tasks:**

- Implement version-aware result storage
- Create results display with filtering
- Add historical result preservation
- Build comparison capabilities

**Deliverables:**

- Version management system
- Results dashboard with filtering
- Historical data preservation

### Phase 5: Evaluation Engine Integration

**Tasks:**

- Integrate existing evaluation logic
- Implement SSE for real-time updates
- Add resume functionality
- Create progress tracking interface

**Deliverables:**

- Background evaluation execution
- Real-time progress updates
- Resume capability
- Console output streaming

### Phase 6: Polish & Production Readiness

**Tasks:**

- Implement responsive design refinements
- Add comprehensive testing
- Create deployment documentation
- Performance optimization

**Deliverables:**

- Production-ready application
- Complete test coverage
- Deployment guide
- Performance benchmarks

## Technical Considerations

### MongoDB Migration Preparation

- Abstract repository pattern for data access
- Consistent data models across storage types
- Migration utilities for existing file data
- Schema design for efficient querying

### Performance Optimization

- Lazy loading for large result sets
- Pagination for results table
- Caching of configuration data
- Efficient SSE connection management

### Error Handling

- Comprehensive error boundaries
- User-friendly error messages
- Automatic retry mechanisms
- Graceful degradation strategies

### Testing Strategy

- Unit tests for all API endpoints
- Integration tests for evaluation workflow
- Frontend component testing
- End-to-end user workflow testing

This design document provides a complete specification for implementing the Storybench web UI, addressing all requirements while maintaining clean architecture and preparing for future enhancements.
