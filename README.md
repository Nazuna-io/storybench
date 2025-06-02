# Storybench

A comprehensive evaluation pipeline for assessing the creative writing capabilities of frontier language models across diverse creative tasks including storytelling, screenwriting, advertising concepts, and cross-genre narratives.

## 🎉 **PRODUCTION RELEASE v1.0** - Complete Analysis & Automated Reporting

**Storybench has successfully completed comprehensive testing of 12 frontier models with professional-grade automated reporting!**

### 🏆 **Major Achievement: Complete 12-Model Evaluation with Professional Analysis**

We've successfully evaluated **541 creative responses** (45 per model) across **12 frontier models** from 4 major providers with **540 comprehensive evaluations** and automated report generation.

**📊 Latest Results:**
1. **🥇 Claude-Opus-4** - 4.52/5.0 (Creative Innovator)
2. **🥈 Gemini-2.5-Pro** - 4.45/5.0 (Technical Perfectionist) 
3. **🥉 Claude-3.7-Sonnet** - 4.25/5.0 (Reliable All-Rounder)

**🔍 Key Discoveries:** 
- **Consistency Issues**: All models show high variability across runs (0.8-1.1 std deviation)
- **Provider Competition**: Google (4.33 avg) slightly edges Anthropic (4.33 avg)  
- **Creativity Challenge**: Character development remains weakest area across all models

### ✅ **Production-Validated Pipeline with Automated Reporting**
- **541 Responses Generated** - 100% success rate across all models
- **540 Evaluations Completed** - 100% parsing success with robust score extraction
- **Professional Reports** - Automated generation with examples and consistency analysis
- **12 Models Tested** - Complete frontier model landscape coverage
- **4 Providers Integrated** - Anthropic, OpenAI, Google, Deepinfra
- **7 Evaluation Criteria** - Comprehensive creative writing assessment
- **Criteria-Based Examples** - Best/worst examples for each criterion with explanations
- **Consistency Analysis** - Reliability metrics across multiple runs
- **MongoDB Integration** - Production-grade data storage and retrieval

### 🚀 **Enterprise-Ready Features**

#### **📊 Automated Report Generation**
- **Professional Format**: Matches industry-standard analysis reports
- **Criteria Examples**: Best/worst examples for each of 7 criteria with evaluator explanations
- **Consistency Analysis**: Performance reliability across multiple runs  
- **Markdown Tables**: Properly formatted rankings and score matrices
- **Provider Analysis**: Company-level performance comparison
- **Use Case Recommendations**: Evidence-based model selection guidance

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

## 🚀 **Quick Start: Generate Professional Reports**

### **Generate Report from Current Data**
```bash
# Export complete evaluation data
python3 export_complete_data.py

# Generate professional report with examples and consistency analysis
python3 professional_report_generator.py complete_storybench_data_[timestamp].json my_report.md

# Quick analysis (alternative)
python3 simple_report_generator.py complete_storybench_data_[timestamp].json
```

### **Run New Evaluation & Generate Report**
```bash
# 1. Run evaluation pipeline (after updating prompts/criteria)
python3 test_full_api_production.py

# 2. Export new data
python3 export_complete_data.py

# 3. Generate updated report
python3 professional_report_generator.py complete_storybench_data_[new_timestamp].json enhanced_report.md
```

### **Available Report Types**
- **`professional_report_generator.py`** - Complete professional analysis (recommended)
- **`simple_report_generator.py`** - Quick performance overview
- **`response_analysis.py`** - Response-only analysis (no evaluation scores needed)

## 📋 **What's in the Professional Reports**

### **Core Analysis**
- **Executive Summary** with key insights and discoveries
- **Performance Rankings** with medals and provider information
- **Detailed Score Matrix** showing all 7 criteria across 12 models
- **Individual Model Analysis** with strengths, weaknesses, and use cases

### **Advanced Features**
- **Criteria-Based Examples**: For each of 7 criteria:
  - Best example (highest scoring response + evaluator quote)
  - Worst example (lowest scoring response + failure explanation)
  - Model attribution and performance scores

- **Consistency Analysis**: 
  - Standard deviation across multiple runs per model
  - Most/least consistent criteria identification  
  - Reliability scores (0-5.0 scale)

- **Provider Analysis**:
  - Performance comparison by company
  - Average scores and best models per provider
  - Strategic insights for model selection

## 🛠️ **Installation & Setup**

### **Prerequisites**
- Python 3.8+
- MongoDB (local or Atlas)
- API keys for model providers

### **Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Environment Setup**
Create `.env` file:
```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
# or MongoDB Atlas: mongodb+srv://user:pass@cluster.mongodb.net/

# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
DEEPINFRA_API_KEY=your_deepinfra_key

# Directus (optional)
DIRECTUS_URL=your_directus_url
DIRECTUS_TOKEN=your_directus_token
```

## 🎯 **Core Evaluation Pipeline**

### **Run Complete Evaluation**
```bash
# Full API production test (all 12 models)
python3 test_full_api_production.py

# Single model test
python3 -m storybench.cli test --model claude-opus-4-20250514

# Resume interrupted evaluation
python3 resume_claude_sonnet.py  # (or specific model)
```

### **Monitor Progress**
```bash
# Check evaluation status
python3 validate_test_readiness.py

# View current results
python3 corrected_analysis.py
```

## 📊 **Data Export & Analysis**

### **Export Options**
```bash
# Export complete dataset (responses + evaluations)
python3 export_complete_data.py

# Export specific evaluation batch  
python3 -m storybench.cli export --export-dir ./analysis_data

# Debug database collections
python3 debug_collections.py
```

### **Analysis Scripts**
```bash
# Generate professional report with examples
python3 professional_report_generator.py [data_file] [output_file]

# Quick performance analysis
python3 simple_report_generator.py [data_file] [output_file]

# Response-only analysis (no scores needed)
python3 response_analysis.py [data_file] [output_file]

# Original corrected analysis
python3 corrected_analysis.py
```

## 🏗️ **Architecture**

### **Core Components**
- **Response Generation**: Multi-provider API integration with robust error handling
- **Evaluation Pipeline**: LLM-based assessment using Gemini-2.5-Pro as evaluator  
- **Data Storage**: MongoDB with organized collections for responses and evaluations
- **Report Generation**: Automated professional analysis with examples and consistency metrics
- **Web Interface**: Vue.js frontend for monitoring and management (optional)

### **Evaluation Process**
1. **Prompt Sequences**: 5 creative writing sequences with 3 prompts each
2. **Response Generation**: 3 runs per model per sequence (45 responses per model)
3. **LLM Evaluation**: Gemini-2.5-Pro scores responses on 7 criteria (1-5 scale)
4. **Score Extraction**: Robust parsing of evaluation text for numerical scores
5. **Analysis & Reporting**: Automated generation of professional reports with examples

### **File Structure**
```
storybench/
├── professional_report_generator.py    # Main report generator
├── export_complete_data.py            # Data export with fixed collection names
├── simple_report_generator.py         # Quick analysis option
├── test_full_api_production.py        # Main evaluation pipeline
├── corrected_analysis.py              # Original analysis script
├── config/                            # Configuration files
├── src/storybench/                    # Core application code
├── frontend/                          # Vue.js web interface
└── reports/                           # Generated analysis reports
```

## 🔧 **Configuration**

### **Model Configuration**
Edit `config/test_models.json` to add/remove models or adjust parameters:
```json
{
  "claude-opus-4-20250514": {
    "provider": "anthropic",
    "temperature": 1.0,
    "max_tokens": 8192
  }
}
```

### **Evaluation Criteria**
Modify evaluation criteria in Directus CMS or update the evaluation prompts in `src/storybench/evaluators/`.

### **Report Configuration**
Adjust report settings in `report_config.py`:
```python
CRITERIA_WEIGHTS = {
    "creativity": 1.2,        # Higher weight for creativity
    "coherence": 1.0,
    # ... other criteria
}
```

## 📈 **Results & Insights**

### **Current Performance Leaders**
- **Overall Best**: Claude-Opus-4 (4.52/5.0) - Excellent creativity and coherence
- **Most Creative**: Claude-Opus-4 (4.80/5.0) - Original concepts and innovation
- **Best Visual**: O4-Mini (4.53/5.0) - Outstanding imagery and description
- **Most Reliable**: Meta-Llama (3.4/5.0 consistency) - Lower performance but consistent

### **Key Findings**
- **Consistency Challenge**: All models show high variability (0.8-1.1 std dev)
- **Adaptability Strength**: Multiple models achieve perfect 5.0/5.0 adaptability
- **Character Development Gap**: All models average ~3.5/5.0 in character depth
- **Provider Competition**: Google and Anthropic tied at 4.33 average performance

### **Research Applications**
- **Model Selection**: Evidence-based recommendations for specific creative tasks
- **Capability Gaps**: Identification of areas needing improvement across all models
- **Consistency Analysis**: Understanding reliability patterns for production use
- **Benchmark Dataset**: 541 high-quality creative responses for further research

## 🤝 **Contributing**

### **Adding New Models**
1. Add model configuration to `config/test_models.json`
2. Implement provider integration in `src/storybench/clients/`
3. Run evaluation: `python3 test_full_api_production.py`
4. Generate updated report: `python3 professional_report_generator.py`

### **Enhancing Evaluation**
1. Update evaluation criteria in Directus or evaluation prompts
2. Run new evaluation pipeline  
3. Export data: `python3 export_complete_data.py`
4. Generate comparative report

### **Report Customization**
- Modify `professional_report_generator.py` for different report formats
- Adjust `report_config.py` for criteria weights and formatting
- Add new analysis dimensions in consistency analysis section

## 🚨 **Troubleshooting**

### **Common Issues**
- **"No evaluations found"**: Use `debug_collections.py` to check database collections
- **Broken markdown tables**: Ensure proper pipe alignment in report generators
- **Missing API keys**: Check `.env` file and environment variable setup
- **Evaluation parsing errors**: Review score extraction patterns in `parse_scores_from_evaluation()`

### **Data Recovery**
```bash
# Export data from correct collections
python3 export_complete_data.py

# Debug database state
python3 debug_collections.py

# Resume interrupted evaluation
python3 resume_claude_sonnet.py
```

## 📄 **License**

MIT License - see LICENSE file for details.

## 🙏 **Acknowledgments**

- **Anthropic** for Claude model access and API reliability
- **Google** for Gemini evaluation model performance  
- **OpenAI** for GPT model integration
- **Deepinfra** for open-source model hosting
- **MongoDB** for robust data storage and retrieval

---

**Storybench v1.1** - Professional creative writing evaluation with automated reporting and consistency analysis. Ready for production use and research applications.
