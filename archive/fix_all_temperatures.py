#!/usr/bin/env python3
"""Fix temperature=1.0 in all test scripts"""

import os
import glob

# Files to update
files_to_update = [
    '/home/todd/storybench/test_full_api_production.py',
    '/home/todd/storybench/validate_model_names.py'
]

for file_path in files_to_update:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace all temperature values with 1.0
        content = content.replace('temperature=0.8', 'temperature=1.0')
        content = content.replace('temperature=0.7', 'temperature=1.0')
        content = content.replace('temperature=0.5', 'temperature=1.0')
        content = content.replace('temperature=0.3', 'temperature=1.0')
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated temperature to 1.0 in {os.path.basename(file_path)}")

print("\n🌡️ All temperature settings standardized to 1.0")
