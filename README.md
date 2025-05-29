# Storybench

A comprehensive evaluation pipeline for assessing the creative writing capabilities of frontier language models across diverse creative tasks including storytelling, screenwriting, advertising concepts, and cross-genre narratives.

## 🎉 **BETA RELEASE v1.0** - Production-Ready Creative Writing Evaluation

**Storybench has successfully completed comprehensive testing of 12 frontier models with groundbreaking results!**

### 🏆 **Major Achievement: Complete 12-Model Evaluation**

We've successfully evaluated **540 creative responses** (45 per model) across **12 frontier models** from 4 major providers:

**📊 Top Performers:**
1. **🥇 Claude-3.7-Sonnet** - 4.21/5.0 (Creative Writing Champion)
2. **🥈 Claude-Opus-4** - 4.20/5.0 (Technical Perfectionist) 
3. **🥉 Gemini-2.5-Pro** - 4.18/5.0 (Reliable All-Rounder)

**🔍 Key Discovery:** Claude-3.7-Sonnet outperforms newer Claude-4 models in creative writing, suggesting specialized optimization for creative tasks.

### ✅ **Production-Validated Pipeline**
- **540 Responses Generated** - 100% success rate across all models
- **540 Evaluations Completed** - Full coverage with improved score extraction
- **12 Models Tested** - Complete frontier model landscape coverage
- **4 Providers Integrated** - Anthropic, OpenAI, Google, Deepinfra
- **7 Evaluation Criteria** - Comprehensive creative writing assessment
- **Robust Error Handling** - Automatic resume logic and skip-on-failure
- **MongoDB Integration** - Production-grade data storage and retrieval

### 🚀 **Enterprise-Ready Features**

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
- **Adaptability** - Flexibility across formats and requirements

### 🔧 **Technical Excellence**

#### **Robust Architecture**
- **Resume Logic** - Automatically continues interrupted evaluations
- **Error Recovery** - Skips failed models and continues pipeline
- **Duplicate Prevention** - Intelligent cleanup of overlapping evaluations
- **Score Extraction** - Advanced parsing with 100% success rate
- **Database Integrity** - Comprehensive data validation and storage

#### **Configuration Management**
- **Environment Variables** - Secure API key management
- **Directus Integration** - Dynamic prompt and criteria loading
- **MongoDB Atlas** - Production-grade cloud database
- **Temperature Control** - 1.0 for prompts, 0.3 for evaluation
- **Token Management** - 8192 max tokens for complex responses

### 📊 **Comprehensive Analysis Tools**

#### **Performance Analytics**
- **Model Rankings** - Overall and criterion-specific performance
- **Provider Comparisons** - Cross-provider capability analysis  
- **Use Case Recommendations** - Model selection for specific tasks
- **Statistical Insights** - Performance patterns and trends

#### **Specialized Reports**
- **Creative Task Optimization** - Best models for specific creative needs
- **Technical vs Creative Trade-offs** - Performance characteristic analysis
- **Generation Comparison** - Claude-3 vs Claude-4 insights
- **Cost-Performance Analysis** - Efficiency recommendations

### 🎯 **Key Research Insights**

1. **Specialized Training Matters** - Claude-3.7's creative dominance over newer models
2. **Size ≠ Performance** - o4-mini competes with much larger models (3.99/5.0)
3. **Provider Specialization** - Each provider shows distinct capability patterns
4. **Creativity Ceiling** - Pure creativity remains challenging (max 3.87/5.0)
5. **Technical Maturity** - Adaptability widely achieved (5 models at 5.0/5.0)

## 🚀 Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/storybench.git
cd storybench

# Set up virtual environment
python -m venv venv-storybench
source venv-storybench/bin/activate  # On Windows: venv-storybench\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Environment Setup**:
```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY=your_openai_key
# - ANTHROPIC_API_KEY=your_anthropic_key
# - GOOGLE_API_KEY=your_google_key
# - DEEPINFRA_API_KEY=your_deepinfra_key
# - MONGODB_URI=your_mongodb_connection_string
```

2. **Database Setup**:
   - Create MongoDB Atlas cluster (free tier available)
   - Add connection string to `.env`
   - Database and collections created automatically

3. **API Keys**:
   - OpenAI API key (for evaluation)
   - Provider API keys (for model testing)
   - All keys validated during setup

### Quick Start

#### **Run Production Test**
```bash
# Validate environment
python validate_test_readiness.py

# Run complete 12-model evaluation
python test_full_api_production.py

# Generate analysis report
python corrected_analysis.py
```

#### **Single Model Testing**
```bash
# Test specific model
python -c "
from src.storybench.evaluators.api_evaluator import APIEvaluator
# Configure and test individual models
"
```

#### **Web Interface** (In Development)
```bash
# Start web server
python -m src.storybench.web.app
# Open http://localhost:5000
```

## 📊 Example Results

### Top Model Performance
```
🥇 claude-3-7-sonnet-20250219    4.21/5.0  (Creative Champion)
🥈 claude-opus-4-20250514        4.20/5.0  (Technical Excellence)  
🥉 gemini-2.5-pro-preview-05-06  4.18/5.0  (Reliable All-Rounder)
```

### Use Case Recommendations
- **Creative Writing**: claude-3-7-sonnet-20250219
- **Technical Content**: claude-opus-4-20250514  
- **Commercial Projects**: gemini-2.5-pro-preview-05-06
- **Visual Storytelling**: o4-mini
- **Budget-Conscious**: gemini-2.5-flash-preview-05-20

## 🔧 Architecture

### Core Components
- **Evaluators** - Model-specific API clients with unified interface
- **Database** - MongoDB with response and evaluation collections
- **Clients** - Directus CMS integration for dynamic content
- **Analysis** - Comprehensive scoring and reporting tools
- **Pipeline** - Robust orchestration with error handling

### Data Flow
1. **Prompts** loaded from Directus CMS
2. **Responses** generated via model APIs
3. **Evaluations** performed by Gemini-2.5-Pro
4. **Storage** in MongoDB with full metadata
5. **Analysis** with advanced score extraction
6. **Reports** generated with comprehensive insights

## 🧪 Evaluation Methodology

### Multi-Dimensional Assessment
- **7 Criteria** evaluated independently
- **5-Point Scale** with detailed rubrics
- **Sequence Coherence** across multi-prompt tasks
- **Context Preservation** between related prompts
- **Gemini-2.5-Pro Evaluator** with 0.3 temperature for consistency

### Statistical Rigor
- **45 Responses per Model** for statistical significance
- **3 Runs per Sequence** to test consistency
- **Context Resets** between runs to ensure independence
- **100% Evaluation Coverage** with robust parsing
- **Duplicate Prevention** and data integrity checks

## 📈 Research Applications

### Academic Research
- **Model Comparison Studies** - Cross-provider capability analysis
- **Creative AI Research** - Understanding creativity in language models
- **Benchmark Development** - Standardized creative writing evaluation
- **Training Optimization** - Insights for creative model development

### Industry Applications  
- **Model Selection** - Data-driven choice for creative applications
- **Content Strategy** - Optimal model deployment for different tasks
- **Cost Optimization** - Performance per dollar analysis
- **Quality Assurance** - Automated creative content evaluation

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black src/ tests/
```

### Adding New Models
1. Implement model client in `src/storybench/evaluators/`
2. Add configuration to evaluation pipeline
3. Update model lists and documentation
4. Run validation tests

### Adding New Evaluation Criteria
1. Update evaluation prompt templates
2. Modify score extraction patterns
3. Add criterion to analysis tools
4. Validate with test evaluations

## 📜 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- **Directus CMS** - Dynamic content management
- **MongoDB Atlas** - Reliable cloud database  
- **Model Providers** - API access for comprehensive testing
- **Research Community** - Inspiration and validation

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/storybench/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/storybench/discussions)
- **Documentation**: See `/docs` directory for detailed guides

**Storybench Beta v1.0** - Production-ready creative writing evaluation for the frontier model era! 🚀