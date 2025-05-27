#!/usr/bin/env python3
"""Test script to verify the integrated solution works end-to-end."""

import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Create a minimal local model config for testing
test_config = {
    "models": [
        {
            "name": "test-gemma-tokenaware",
            "provider": "local_default_provider",
            "type": "local",
            "repo_id": "unsloth/gemma-3-1b-it-GGUF",
            "filename": "gemma-3-1b-it-Q2_K_L.gguf",
            "model_settings": {
                "n_ctx": 8192,
                "max_tokens": 1024,  # Smaller for testing
                "temperature": 0.8,
                "n_gpu_layers": 0
            }
        }
    ]
}

# Write the test config
with open('/home/todd/storybench/test_local_models.json', 'w') as f:
    json.dump(test_config, f, indent=2)

print("Created test configuration: test_local_models.json")
print("Content:")
print(json.dumps(test_config, indent=2))
print("\nTo test the integrated solution, run:")
print("python3 run_end_to_end.py --local-config test_local_models.json --models test-gemma-tokenaware --sequences FilmNarrative")
