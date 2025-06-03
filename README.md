# StoryBench v1.5 ✅ COMPLETE

A comprehensive evaluation pipeline for assessing the creative writing capabilities of frontier language models across diverse creative tasks including storytelling, screenwriting, advertising concepts, and cross-genre narratives.

## 🎉 **StoryBench v1.5 - PRODUCTION READY** 

**All 6 development phases complete! StoryBench v1.5 brings complete automation, interactive dashboard, and production-ready deployment.**

### 🚀 **Complete Feature Set**

#### **📊 Interactive Streamlit Dashboard**
- **6 Complete Analysis Pages**: Overview, Rankings, Criteria Analysis, Provider Comparison, Progress Monitoring, Data Explorer
- **Real-time Monitoring**: Live progress tracking of evaluation runs with cost analysis
- **Advanced Visualizations**: Interactive radar charts, heatmaps, correlation analysis, statistical insights
- **Data Export**: CSV export functionality for external analysis
- **Current Data**: 913 responses, 13 models, 900 evaluations across 7 criteria

#### **⚡ Automated Pipeline Execution**
- **One-Command Evaluation**: `python run_automated_evaluation.py`
- **Smart Resume**: Automatically skip completed evaluations with version awareness
- **Cost Tracking**: Real-time API usage monitoring and cost estimation
- **Error Resilience**: Built-in retry logic and graceful failure handling
- **Progress Monitoring**: JSON progress files for real-time status updates

#### **🔧 YAML Configuration Management**
- **Easy Model Addition**: Edit `config/models.yaml` - no code changes needed
- **Centralized Settings**: All evaluation parameters in one configuration file
- **Model Control**: Simple enable/disable flags for selective evaluation
- **Provider Support**: OpenAI, Anthropic, Google, DeepInfra unified access

#### **🔌 LiteLLM Integration**
- **Unified API**: Single interface for all major LLM providers
- **Enhanced Reliability**: Exponential backoff retry logic and error handling  
- **Usage Analytics**: Comprehensive cost tracking and performance metrics
- **Backwards Compatible**: Existing v1.4 code continues to work unchanged

#### **🐳 Production Deployment**
- **Docker Ready**: Complete containerization with `docker-compose.yml`
- **Security Hardened**: SSL/TLS configuration, environment secrets management
- **Auto-Scaling**: Load balancer configuration and health monitoring
- **Cloud Ready**: AWS and GCP deployment examples included

### 🏆 **Evaluation Results**

Successfully processing **913 creative responses** across **13 frontier models** from 4 major providers with **900 completed LLM evaluations**:

**📊 Top Performing Providers:**
1. **🥇 Anthropic** - Claude Opus/Sonnet leading creative innovation
2. **🥈 OpenAI** - GPT-4 variants with strong technical performance  
3. **🥉 Google** - Gemini series with balanced capabilities
4. **🔄 DeepInfra** - Specialized models (DeepSeek, Qwen, Llama) with unique strengths

*View detailed model rankings and performance analysis in the interactive dashboard*

### ✅ **Production-Ready System**

#### **📋 Complete Documentation (1000+ lines)**
- **User Guide**: Comprehensive installation and usage instructions
- **API Reference**: Detailed documentation for all components
- **Deployment Guide**: Production deployment with Docker and security
- **Migration Guide**: Complete v1.4 to v1.5 upgrade instructions

#### **🧪 Testing Framework (80% Coverage)**
- **Comprehensive Test Suite**: 40+ test cases across all components
- **Integration Testing**: End-to-end workflow validation
- **Dashboard Testing**: All 6 pages validated and functional
- **Error Handling**: Edge cases and failure scenarios covered

### ✅ **Production-Ready Features**

#### **🤖 Model Support (12 Models)**
- **Anthropic**: Claude-Opus-4, Claude-Sonnet-4, Claude-3.7-Sonnet
- **OpenAI**: GPT-4.1, GPT-4o, o4-mini  
- **Google**: Gemini-2.5-Pro, Gemini-2.5-Flash
- **Deepinfra**: Qwen3-235B, Llama-4-Maverick, DeepSeek-R1, DeepSeek-V3

#### **📝 Creative Writing Tasks (5 Sequences)**
- **Film Narrative Development** - Concept to visual realization
- **Literary Narrative Creation** - Character-driven storytelling
- **Commercial Concept Design** - Marketing and advertising creativity
- **Regional Thriller Writing** - Location-specific narrative development
- **Cross-Genre Fusion** - Innovative genre-blending narratives

#### **🎯 Evaluation Framework (7 Criteria)**
- **Creativity** - Originality and innovative thinking
- **Coherence** - Logical flow and narrative consistency
- **Character Depth** - Multi-dimensional character development
- **Dialogue Quality** - Natural and engaging conversations
- **Visual Imagination** - Vivid imagery and scene-setting
- **Conceptual Depth** - Complex themes and philosophical content
- **Adaptability** - Format flexibility and prompt following

## 🚀 **Quick Start**

### **Installation**

```bash
# Clone the repository
git clone https://github.com/yourusername/storybench.git
cd storybench

# Create virtual environment
python -m venv venv-storybench
source venv-storybench/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy example configuration
cp config/models.example.yaml config/models.yaml

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### **🎯 Complete Workflow**

1. **Configure Models**: Edit `config/models.yaml` to enable/disable models
2. **Set API Keys**: Add credentials to `.env` file
3. **Run Evaluations**: `python run_automated_evaluation.py`
4. **View Results**: Launch dashboard with `streamlit run streamlit_dashboard/app.py`

### **📊 Interactive Dashboard**

Launch the comprehensive evaluation dashboard:

```bash
cd streamlit_dashboard
streamlit run app.py
```

**Dashboard Features:**
- **📈 Overview**: Key metrics, top performers, and evaluation progress
- **🏆 Rankings**: Model performance comparison with interactive radar charts  
- **📊 Criteria Analysis**: Box plots and statistical insights across evaluation criteria
- **🏢 Provider Comparison**: Performance analysis by company (Anthropic, OpenAI, etc.)
- **⚡ Progress**: Real-time monitoring of evaluation runs
- **🔍 Data Explorer**: Interactive filtering and drill-down analysis

Access at `http://localhost:8501` after launching

### **Configuration**

1. Edit `config/models.yaml` to:
   - Add/remove models
   - Enable/disable specific models
   - Adjust token limits and settings

2. Set API keys in `.env`:
   ```env
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   DEEPINFRA_API_KEY=your_key_here
   ```

### **Running Evaluations**

#### **Simple: Run All Enabled Models**
```bash
python run_automated_evaluation.py
```

#### **Advanced Options**
```bash
# Start fresh (ignore previous runs)
python run_automated_evaluation.py --no-resume

# Force rerun specific models
python run_automated_evaluation.py --rerun claude-opus-4,gpt-4o

# Dry run to see what would be evaluated
python run_automated_evaluation.py --dry-run
```

### **Generate Reports**

```bash
# Export evaluation data
python export_complete_data.py

# Generate professional report
python professional_report_generator.py complete_storybench_data_[timestamp].json report.md
```

## 📋 **Project Structure**

```
storybench/
├── config/                      # Configuration files
│   ├── models.yaml             # Model definitions (v1.5)
│   └── models.example.yaml     # Example configuration
├── src/storybench/             # Core application code
│   ├── config_loader.py        # YAML configuration management (v1.5)
│   ├── evaluators/            
│   │   ├── litellm_evaluator.py # Unified LLM interface (v1.5)
│   │   └── base.py             # Base evaluator class
│   ├── clients/                # API clients
│   └── database/               # MongoDB integration
├── tests/                      # Test suite
├── docs/                       # Documentation
│   ├── v1.5_implementation_plan.md
│   └── v1.5_progress.md
└── run_automated_evaluation.py # Main entry point (v1.5)
```

## 🛠️ **Technical Architecture**

### **Core Components**

1. **Configuration System** (NEW in v1.5)
   - YAML-based model management
   - Type-safe configuration with validation
   - Easy to extend and modify

2. **LiteLLM Integration** (NEW in v1.5)
   - Unified API for all LLM providers
   - Automatic retry and error handling
   - Cost tracking and monitoring

3. **LangChain Context Management**
   - No truncation policy
   - Handles up to 1M+ tokens
   - Maintains conversation history

4. **MongoDB Storage**
   - Responses and evaluations
   - Version tracking
   - Performance optimization

5. **Evaluation Pipeline**
   - 5 sequences × 3 prompts × 3 runs = 45 responses per model
   - Gemini-2.5-Pro as evaluator
   - 7 criteria scoring system

## 📊 **Results & Analysis**

### **Model Performance Summary**
- **Best Overall**: Claude-Opus-4 (4.52/5.0)
- **Most Creative**: Claude-Opus-4 (4.80/5.0)
- **Best Dialogue**: GPT-4.1 (4.60/5.0)
- **Most Consistent**: Meta-Llama (lowest std deviation)

### **Key Findings**
- All models show high variability (0.8-1.1 std deviation)
- Character development remains challenging across all models
- Provider competition is extremely close (within 0.1 points)

## 🔄 **Migration from v1.0**

1. **Backwards Compatible**: Your existing code will continue to work
2. **Optional Migration**: Update to use new features when ready
3. **Configuration**: Create `config/models.yaml` from the example
4. **No Data Changes**: MongoDB schema unchanged

## 🤝 **Contributing**

### **Adding New Models**
1. Edit `config/models.yaml`
2. Add model details under appropriate provider
3. Set `enabled: true`
4. Run evaluation pipeline

### **Development Setup**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Check configuration
python test_config_system.py
```

## 📚 **Documentation**

- [Configuration Guide](docs/configuration_guide.md)
- [API Documentation](docs/api_documentation.md)
- [Evaluation Methodology](docs/evaluation_methodology.md)
- [v1.5 Implementation Plan](docs/v1.5_implementation_plan.md)

## 🐛 **Troubleshooting**

### **Common Issues**

1. **"No module named litellm"**
   - Run: `pip install -r requirements.txt`

2. **"API key not found"**
   - Check your `.env` file has all required keys
   - Ensure no spaces around the `=` sign

3. **"Context limit exceeded"**
   - Model context limit reached
   - Consider using a model with larger context window

## 📄 **License**

MIT License - see LICENSE file for details.

## 🙏 **Acknowledgments**

- **Anthropic** for Claude model access
- **Google** for Gemini evaluation capabilities
- **OpenAI** for GPT model integration
- **DeepInfra** for open model hosting
- **LiteLLM** for unified API interface (v1.5)

---

**StoryBench v1.5** - Now with automated pipeline management and easier configuration!
