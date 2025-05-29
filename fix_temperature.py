#!/usr/bin/env python3
"""Fix APIEvaluator to handle o4-mini temperature restrictions"""

# Read the file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'r') as f:
    content = f.read()

# Find the _generate_openai method and fix temperature handling
old_temperature = 'temperature=kwargs.get("temperature", 0.9)'
new_temperature = '''temperature=1 if (self.model_name.startswith("o4")) else kwargs.get("temperature", 0.9)'''

content = content.replace(old_temperature, new_temperature)

# Write the fixed file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'w') as f:
    f.write(content)

print("✅ APIEvaluator temperature restriction fixed for o4-mini")
