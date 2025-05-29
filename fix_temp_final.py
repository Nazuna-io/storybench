#!/usr/bin/env python3
"""Fix APIEvaluator temperature handling more precisely"""

# Read the file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'r') as f:
    content = f.read()

# Fix the remaining temperature reference
old_line = '            "temperature": kwargs.get("temperature", 0.9)'
new_line = '            "temperature": 1 if (self.model_name.startswith("o4")) else kwargs.get("temperature", 0.9)'

content = content.replace(old_line, new_line)

# Write the fixed file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'w') as f:
    f.write(content)

print("✅ APIEvaluator temperature handling fixed completely")
