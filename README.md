# Storybench v1.5

A comprehensive evaluation pipeline for assessing the creative writing capabilities of frontier language models across diverse creative tasks including storytelling, screenwriting, advertising concepts, and cross-genre narratives.

## 🎉 **NEW IN v1.5** - Complete Automation & Interactive Dashboard

**StoryBench v1.5 brings major improvements in automation, interactive visualization, and production-ready evaluation workflows!**

### 🚀 **What's New in v1.5**

#### **📊 Interactive Streamlit Dashboard**
- **Real-time Monitoring**: Live progress tracking of evaluation runs
- **Performance Analysis**: Interactive radar charts and model rankings
- **Statistical Insights**: Comprehensive criteria analysis with visualizations
- **Model Comparison**: Side-by-side performance profiling
- **Cost Tracking**: Monitor API usage and evaluation costs

#### **🔧 YAML Configuration Management**
- **Easy Model Addition**: Just edit `config/models.yaml` - no code changes needed!
- **Centralized Settings**: All evaluation parameters in one place
- **Enable/Disable Models**: Simple flags to include/exclude models from evaluation

#### **⚡ Automated Pipeline Execution**
- **Single Command**: Run entire evaluation with `python run_automated_evaluation.py`
- **Smart Resume**: Automatically skip completed evaluations
- **Force Rerun**: Option to re-evaluate specific models
- **Progress Tracking**: Real-time progress with JSON status files

#### **🔌 LiteLLM Integration**
- **Unified API Access**: Single interface for all providers (OpenAI, Anthropic, Google, DeepInfra)
- **Better Reliability**: Built-in retry logic and error handling
- **Cost Tracking**: Monitor API usage and costs
- **Backwards Compatible**: Existing code continues to work unchanged

### 🏆 **Latest Evaluation Results**

We've successfully evaluated **913 creative responses** across **13 frontier models** from 4 major providers with **900 completed LLM evaluations**:

**📊 Current Top Performers:**
1. **🥇 Claude-Opus-4** - Leading creative innovation
2. **🥈 Multiple Strong Performers** - Claude Sonnet, GPT-4 variants, Gemini series
3. **🥉 Specialized Models** - DeepSeek, Qwen, Llama variants

*View detailed rankings and performance analysis in the interactive dashboard*

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
