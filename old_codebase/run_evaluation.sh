#!/bin/bash

# Run CPU-only creative evaluation script
# Make sure to install required dependencies first:
# pip install torch transformers llama-cpp-python

# Create results directory
mkdir -p results

# Set environment variables for optimal CPU performance
export PYTHONIOENCODING=utf-8
export TOKENIZERS_PARALLELISM=false

# Configure CPU threading for optimal performance
export OMP_NUM_THREADS=$(nproc)   # Use all CPU cores
export MKL_NUM_THREADS=$(nproc)   # For Intel MKL optimization

# Run the evaluation script
python llm_creative_eval.py \
  --models_config models_config.json \
  --prompts_file creative_prompts.json \
  --output_dir results \
  --num_runs 3

echo "Evaluation complete. Results are in the 'results' directory."
