# Output Directory

This directory contains evaluation results and output files.

Files in this directory are not tracked by git (see .gitignore).

## Structure

- `{model_name}_{config_hash}.json` - Individual model evaluation results
- Evaluation results include all responses, timing, and metadata
- Progress tracking enables resume functionality

## Example Result File Structure

```json
{
  "metadata": {
    "model_name": "GPT-4",
    "config_version": 1,
    "timestamp": "2025-01-25T10:30:00Z"
  },
  "sequences": {
    "FilmNarrative": {
      "run_1": [...],
      "run_2": [...],
      "run_3": [...]
    }
  },
  "evaluation_scores": {...},
  "status": "complete"
}
```
