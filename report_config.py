# Storybench Report Generator Configuration

# Data file patterns to look for (in order of preference)
DATA_FILE_PATTERNS = [
    "full_api_production_test_report_*.json",
    "*_test_report_*.json", 
    "evaluation_results.json"
]

# Output directory for reports
OUTPUT_DIR = "reports"

# Report settings
INCLUDE_EXAMPLES = True
TOP_MODELS_TO_ANALYZE = 6
CRITERIA_WEIGHTS = {
    "creativity": 1.2,        # Slightly higher weight for creativity
    "coherence": 1.0,
    "character_depth": 1.0,
    "dialogue_quality": 1.0,
    "visual_imagination": 1.0,
    "conceptual_depth": 1.1,  # Slightly higher weight for conceptual depth
    "adaptability": 0.9       # Slightly lower weight for adaptability
}

# Provider information for better categorization
PROVIDER_MAPPING = {
    "claude": "Anthropic",
    "gemini": "Google", 
    "gpt": "OpenAI",
    "o4": "OpenAI",
    "deepseek": "Deepinfra",
    "qwen": "Deepinfra",
    "llama": "Deepinfra"
}

# Evaluation criteria descriptions
CRITERIA_DESCRIPTIONS = {
    "creativity": "Originality and innovation in responses",
    "coherence": "Logical consistency and narrative flow", 
    "character_depth": "Psychological complexity and development",
    "dialogue_quality": "Natural and engaging conversation",
    "visual_imagination": "Descriptive power and imagery",
    "conceptual_depth": "Thematic sophistication and insight",
    "adaptability": "Following prompts and format flexibility"
}
