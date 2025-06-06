# StoryBench v1.5 Streamlit Dashboard

A modern, interactive dashboard for analyzing StoryBench evaluation results.

## Features

### 📊 Overview Page
- **Key Metrics**: Total responses, models evaluated, LLM evaluations, last evaluation date
- **Model Response Counts**: Interactive horizontal bar chart showing response distribution
- **Top Performers**: Top 5 models ranked by overall evaluation score
- **Evaluation Coverage**: Progress tracking of evaluation completion

### 🏆 Model Rankings Page  
- **Overall Rankings Table**: Complete model ranking with scores and response counts
- **Individual Model Analysis**: Detailed radar charts for single model performance profiles
- **Model Comparison**: Side-by-side radar chart comparison (up to 4 models)
- **Criteria Breakdown**: Box plots showing score distribution across all criteria
- **Statistical Summary**: Descriptive statistics for all evaluation criteria
- **Key Insights**: Automated identification of highest/lowest scoring and most/least consistent criteria

### ⚡ Real-Time Progress Page
- **Progress File Detection**: Automatic discovery of JSON progress files from automated runs
- **Run Summary**: Start/end times, total cost, completion status
- **Progress Visualization**: Interactive progress bars by model
- **Detailed Model Status**: Expandable sections with completion stats, costs, and error logs
- **Configuration View**: Access to run configuration and raw progress data
- **Auto-refresh**: Optional 30-second auto-refresh for real-time monitoring

## Current Data Stats
- **913 total responses** from **13 models**
- **900 LLM evaluations** completed
- **606 responses** with extracted evaluation scores across **7 criteria**
- **Models include**: Claude (Opus/Sonnet), GPT-4 variants, Gemini, DeepSeek, Qwen, Llama

## Technical Implementation
- **Framework**: Streamlit 1.45+ with responsive design
- **Database**: Direct MongoDB connection using existing schema
- **Visualizations**: Plotly for interactive charts (radar charts, bar charts, box plots)
- **Data Processing**: Pandas for efficient data manipulation and aggregation
- **Score Extraction**: Regex-based parsing of evaluation text for criteria scores
- **Real-time Monitoring**: JSON file watching for automated evaluation progress

## Architecture
```
streamlit_dashboard/
├── app.py                 # Main multi-page Streamlit application
├── data_service.py        # MongoDB connection and data processing
├── requirements.txt       # Python dependencies
└── pages/
    ├── __init__.py
    ├── overview.py        # Overview page with key metrics
    ├── rankings.py        # Model rankings and comparison
    └── progress.py        # Real-time progress monitoring
```

## Usage

### Starting the Dashboard
```bash
cd /home/todd/storybench/streamlit_dashboard
source ../venv-storybench/bin/activate
streamlit run app.py --server.port 8505
```

### Monitoring Automated Evaluations
The progress page automatically detects JSON progress files created by:
```bash
python run_automated_evaluation.py
```

### Navigation
Use the sidebar to navigate between:
- 📊 **Overview**: High-level metrics and top performers
- 🏆 **Model Rankings**: Detailed performance analysis and comparison
- ⚡ **Real-Time Progress**: Live monitoring of evaluation runs

## Data Sources
- **Responses**: `db.responses` collection with model outputs
- **Evaluations**: `db.response_llm_evaluations` with parsed criteria scores
- **Progress**: JSON files from automated evaluation runner

## Phase 4 Status: ✅ COMPLETE
- Overview page with key metrics and top performers ✅
- Rankings page with radar charts and model comparison ✅  
- Real-time progress monitoring from JSON files ✅
- Responsive design with interactive visualizations ✅
- Direct MongoDB integration using existing data schema ✅
