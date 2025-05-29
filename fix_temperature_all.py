#!/usr/bin/env python3
"""Fix APIEvaluator to use temperature=1.0 for all models"""

# Read the file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'r') as f:
    content = f.read()

# Replace all temperature references to use 1.0
# Fix the generation method temperature
old_temp_pattern = 'temperature": 1 if (self.model_name.startswith("o4")) else kwargs.get("temperature", 0.9)'
new_temp_pattern = 'temperature": 1.0'

content = content.replace(old_temp_pattern, new_temp_pattern)

# Also fix any remaining 0.9 defaults
content = content.replace('kwargs.get("temperature", 0.9)', '1.0')

# Write the fixed file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'w') as f:
    f.write(content)

print("✅ APIEvaluator temperature standardized to 1.0 for all models")
