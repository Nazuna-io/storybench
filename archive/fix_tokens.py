#!/usr/bin/env python3
"""Fix APIEvaluator to use more tokens for o4-mini testing"""

# Read the file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'r') as f:
    content = f.read()

# Fix the token count in setup - change from 1 to 10 for o4 models
content = content.replace('max_completion_tokens=1', 'max_completion_tokens=10')

# Write the fixed file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'w') as f:
    f.write(content)

print("✅ APIEvaluator token count fixed for o4-mini")
