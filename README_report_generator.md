# Storybench Report Generator

Automated report generation for Storybench model evaluation results.

## Quick Start

1. **Run a simple report** (recommended for most use cases):
   ```bash
   python run_report.py
   ```
   This automatically finds your latest data file and generates a report.

2. **Run with examples** (detailed analysis):
   ```bash
   python run_report.py --examples
   ```

3. **Specify custom data file**:
   ```bash
   python run_report.py --data your_data_file.json
   ```

## Files Overview

- **`run_report.py`** - Smart runner that finds latest data automatically
- **`simple_report_generator.py`** - Fast, streamlined report generator  
- **`generate_storybench_report.py`** - Full-featured report generator (WIP)
- **`report_config.py`** - Configuration settings

## Usage Examples

### Basic Usage
```bash
# Generate report from latest data file
python run_report.py

# Generate report with specific output name
python run_report.py --output my_analysis.md

# Use specific data file
python simple_report_generator.py data_file.json
```

### Advanced Usage
```bash
# Full report with examples (when available)
python run_report.py --examples

# Direct usage of simple generator
python simple_report_generator.py full_api_production_test_report_20250528_212154.json custom_report.md
```

## Output

Reports include:
- **Overall Rankings** - Models ranked by performance
- **Detailed Score Matrix** - Breakdown by evaluation criteria  
- **Top Performer Analysis** - Strengths and weaknesses
- **Provider Analysis** - Performance by company
- **Category Leaders** - Best model for each criterion
- **Recommendations** - Practical model selection guidance

## Expected Data Format

The script expects JSON files with this structure:
```json
{
  "responses": [
    {
      "_id": "response_id",
      "model_name": "model-name", 
      "text": "response content",
      ...
    }
  ],
  "evaluations": [
    {
      "response_id": "response_id",
      "evaluation_text": "Text with scores like 'creativity: 4.5'",
      ...
    }
  ]
}
```

## Troubleshooting

**No data files found:**
- Ensure you have JSON files in the current directory
- Expected patterns: `*_test_report_*.json`, `evaluation_results.json`

**Missing scores in report:**
- Check evaluation text format includes patterns like `creativity: 4.5`
- Verify response IDs match between responses and evaluations

**Import errors:**
- Ensure you're running from the storybench directory
- Python 3.7+ required

## Next Steps for Enhanced Evaluation

After updating your prompts and evaluation criteria:

1. Run your enhanced evaluation pipeline
2. Execute: `python run_report.py --examples` 
3. Compare results with previous reports
4. Iterate on prompt design based on findings

The script automatically adapts to new evaluation criteria and data formats.
