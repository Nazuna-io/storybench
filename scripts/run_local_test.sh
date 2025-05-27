#!/bin/bash

# This script runs the end-to-end pipeline with a local model for both generation and evaluation.
# Updated for handling 14k+ token responses with improved context management.

# Ensure you have config/local_models.json set up correctly.
# Model is now configured with:
# - n_ctx: 32768 (large context window for 14k+ responses)
# - max_tokens: 16384 (supports long generation)
# - Improved context truncation and model state reset

echo "🚀 Starting local model test with large context support..."
echo "📊 Model: Gemma-3-1B-IT-Q2_K_L"
echo "🧠 Context: 32k tokens, Generation: 16k tokens"
echo "🔄 Features: Smart context truncation, model state reset"
echo ""

python3 run_end_to_end.py \
    --models "Gemma-3-1B-IT-Q2_K_L" \
    --sequences "FilmNarrative" \
    --local-config config/local_models.json \
    --auto-evaluate \
    --evaluator-model "Gemma-3-1B-IT-Q2_K_L"
