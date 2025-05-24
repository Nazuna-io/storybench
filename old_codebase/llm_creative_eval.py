#!/usr/bin/env python3
# CPU-only model evaluation script with multiple trials per prompt
# Focused on reliability over speed for creative evaluation

import os
import json
import time
import argparse
import torch
import logging
from datetime import datetime
import gc
import psutil
import random

# For GGUF models
from llama_cpp import Llama

# For HF models
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("evaluation.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Custom stopping criteria for HF models
class StopOnTokens(StoppingCriteria):
    def __init__(self, stop_token_ids):
        self.stop_token_ids = stop_token_ids
    
    def __call__(self, input_ids, scores, **kwargs):
        for stop_id in self.stop_token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False

def log_memory_usage():
    """Log current memory usage"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    logger.info(f"RAM usage: {memory_info.rss / (1024 * 1024 * 1024):.2f} GB")
    
    # Log system memory
    vm = psutil.virtual_memory()
    logger.info(f"System RAM: {vm.used / (1024 * 1024 * 1024):.2f} GB used, {vm.available / (1024 * 1024 * 1024):.2f} GB available")

def load_prompts(prompts_file):
    """Load the prompt sequences from a JSON file"""
    with open(prompts_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_variant_prompt(base_prompt, run_index):
    """Create a variant prompt for multiple runs"""
    variant_additions = [
        "For this response, explore a completely different direction than you might normally take. Be original and surprising in your approach.",
        "Think outside conventional narratives for this response. Create something unique that demonstrates creative thinking and fresh ideas.",
        "For your third approach to this prompt, push boundaries with innovative concepts and perspectives unlike typical responses."
    ]
    
    return f"{base_prompt}\n\n{variant_additions[run_index % len(variant_additions)]}"

def format_prompt(prompt_text, conversation_history=None):
    """Format the prompt based on conversation history"""
    if conversation_history:
        return f"{conversation_history}\n\nHuman: {prompt_text}\n\nAssistant:"
    else:
        return f"Human: {prompt_text}\n\nAssistant:"

def create_model_directory(base_dir, model_name):
    """Create directory for model outputs"""
    model_dir = os.path.join(base_dir, model_name)
    os.makedirs(model_dir, exist_ok=True)
    return model_dir

def run_gguf_model(model_path, model_name, prompts, output_dir, num_runs=3):
    """Run evaluation on a GGUF model using CPU only with multiple runs per prompt"""
    logger.info(f"Loading GGUF model '{model_name}' on CPU")
    
    # Create model directory
    model_dir = create_model_directory(output_dir, model_name)
    
    try:
        start_time = time.time()
        
        # Check if model_path is a directory (for split files) or a single file
        if os.path.isdir(model_path):
            gguf_files = [f for f in os.listdir(model_path) if f.endswith('.gguf')]
            if not gguf_files:
                raise ValueError(f"No GGUF files found in directory: {model_path}")
            
            gguf_files.sort()
            model_file_path = os.path.join(model_path, gguf_files[0])
            logger.info(f"Found split GGUF files. Using first part: {model_file_path}")
        else:
            model_file_path = model_path
        
        # Log memory before loading
        log_memory_usage()
        
        # For CPU, use most cores available
        threads_to_use = min(48, os.cpu_count())
        logger.info(f"Using {threads_to_use} CPU threads for inference")
        
        # Load model optimized for CPU
        model = Llama(
            model_path=model_file_path,
            n_gpu_layers=0,        # CPU only
            n_ctx=8192,            # Large context window
            n_batch=32,            # Moderate batch size
            n_threads=threads_to_use,
            use_mmap=False,        # Disable memory mapping to load fully into RAM
            use_mlock=True,        # Keep in RAM
            verbose=True
        )
        
        # Test the model with small generation to ensure it's initialized
        logger.info("Testing model performance with a small generation...")
        test_start = time.time()
        test_output = model("Hello world", max_tokens=10)
        test_time = time.time() - test_start
        logger.info(f"Test generation completed in {test_time:.2f} seconds")
        logger.info(f"Test output: {test_output}")
        
        # Log memory after loading
        log_memory_usage()
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f} seconds")
        
        # Process each prompt sequence
        for sequence_name, sequence_prompts in prompts.items():
            # Create multiple sequence files for different runs
            for run in range(num_runs):
                sequence_output_file = os.path.join(model_dir, f"{sequence_name}_run{run+1}.txt")
                conversation_history = ""
                
                with open(sequence_output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Model: {model_name}\n")
                    f.write(f"Sequence: {sequence_name}\n")
                    f.write(f"Run: {run+1} of {num_runs}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Model loading time: {load_time:.2f} seconds\n\n")
                    
                    for i, prompt_data in enumerate(sequence_prompts):
                        prompt_name = prompt_data["name"]
                        base_prompt_text = prompt_data["text"]
                        
                        # Create a variant of the prompt for this run
                        prompt_text = get_variant_prompt(base_prompt_text, run)
                        
                        logger.info(f"Running {model_name} on {sequence_name} - {prompt_name} (Run {run+1})")
                        
                        # Format prompt with conversation history
                        full_prompt = format_prompt(prompt_text, conversation_history)
                        
                        # Set a random seed for each run to encourage diversity
                        random_seed = random.randint(1, 10000)
                        
                        # Generate response
                        generation_start = time.time()
                        
                        # Generate with more consistent parameters
                        response = model(
                            full_prompt,
                            max_tokens=4096,
                            temperature=0.9,
                            stop=["Human:", "\nHuman:"],
                            echo=False,
                            repeat_penalty=1.1,
                            seed=random_seed
                        )
                        
                        generation_time = time.time() - generation_start
                        token_count = len(response["choices"][0]["text"].split())
                        tps = token_count / generation_time if generation_time > 0 else 0
                        
                        logger.info(f"Generated {token_count} tokens in {generation_time:.2f} seconds ({tps:.2f} tokens/sec)")
                        
                        # Extract response text
                        response_text = response["choices"][0]["text"].strip()
                        
                        # Update conversation history for next prompt
                        if not conversation_history:
                            conversation_history = full_prompt + " " + response_text
                        else:
                            conversation_history += f"\n\nHuman: {prompt_text}\n\nAssistant: {response_text}"
                        
                        # Write to output file
                        f.write(f"\n{'='*50}\n")
                        f.write(f"PROMPT {i+1}: {prompt_name}\n")
                        f.write(f"{'='*50}\n\n")
                        f.write(f"{prompt_text}\n\n")
                        f.write(f"{'='*50}\n")
                        f.write(f"RESPONSE:\n")
                        f.write(f"{'='*50}\n\n")
                        f.write(f"{response_text}\n\n")
                        f.write(f"Generation time: {generation_time:.2f} seconds ({tps:.2f} tokens/sec)\n\n")
                
                logger.info(f"Completed sequence {sequence_name} run {run+1} for {model_name}")
        
        # Clean up
        logger.info("Cleaning up model resources...")
        del model
        gc.collect()
        
        # Force memory cleanup
        logger.info("Forcing garbage collection...")
        for _ in range(3):
            gc.collect()
            
        log_memory_usage()
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing GGUF model {model_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_hf_model(model_path, model_name, prompts, output_dir, num_runs=3):
    """Run evaluation on a HuggingFace model using CPU only with multiple runs per prompt"""
    logger.info(f"Loading HF model '{model_name}' on CPU")
    
    # Create model directory
    model_dir = create_model_directory(output_dir, model_name)
    
    try:
        start_time = time.time()
        
        # Log memory before loading
        log_memory_usage()
        
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # CPU configuration
        device_map = "cpu"
        threads_to_use = min(48, os.cpu_count())
        torch.set_num_threads(threads_to_use)
        logger.info(f"Using CPU with {threads_to_use} threads")
        
        # Load model with CPU settings
        logger.info(f"Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=device_map,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=False,  # Load fully into RAM
            offload_folder=None,
            offload_state_dict=False
        )
        
        # Configure stopping criteria
        stop_words = ["Human:", "\nHuman:"]
        stop_token_ids = [tokenizer(stop_word, return_tensors='pt').input_ids.squeeze()[-1] for stop_word in stop_words]
        stopping_criteria = StoppingCriteriaList([StopOnTokens(stop_token_ids)])
        
        # Test the model with small generation to ensure it's initialized
        logger.info("Testing model performance with a small generation...")
        test_start = time.time()
        test_input = tokenizer("Hello world", return_tensors="pt")
        test_output = model.generate(test_input.input_ids, max_new_tokens=10)
        test_time = time.time() - test_start
        logger.info(f"Test generation completed in {test_time:.2f} seconds")
        logger.info(f"Test output: {tokenizer.decode(test_output[0], skip_special_tokens=True)}")
        
        # Log memory after loading
        log_memory_usage()
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f} seconds")
        
        # Process each prompt sequence
        for sequence_name, sequence_prompts in prompts.items():
            # Create multiple sequence files for different runs
            for run in range(num_runs):
                sequence_output_file = os.path.join(model_dir, f"{sequence_name}_run{run+1}.txt")
                conversation_history = ""
                
                with open(sequence_output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Model: {model_name}\n")
                    f.write(f"Sequence: {sequence_name}\n")
                    f.write(f"Run: {run+1} of {num_runs}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Model loading time: {load_time:.2f} seconds\n\n")
                    
                    for i, prompt_data in enumerate(sequence_prompts):
                        prompt_name = prompt_data["name"]
                        base_prompt_text = prompt_data["text"]
                        
                        # Create a variant of the prompt for this run
                        prompt_text = get_variant_prompt(base_prompt_text, run)
                        
                        logger.info(f"Running {model_name} on {sequence_name} - {prompt_name} (Run {run+1})")
                        
                        # Format prompt with conversation history
                        full_prompt = format_prompt(prompt_text, conversation_history)
                        
                        # Generate response
                        generation_start = time.time()
                        inputs = tokenizer(full_prompt, return_tensors="pt")
                        
                        # Set a random seed for each run to encourage diversity
                        torch.manual_seed(random.randint(1, 10000))
                        
                        # Generate with optimized parameters
                        outputs = model.generate(
                            inputs.input_ids,
                            max_new_tokens=4096,
                            temperature=0.9,
                            do_sample=True,
                            top_p=0.95,
                            stopping_criteria=stopping_criteria,
                            repetition_penalty=1.1
                        )
                        
                        generation_time = time.time() - generation_start
                        
                        # Decode and extract only the response
                        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        response_text = full_output[len(full_prompt):].strip()
                        
                        # Calculate approx tokens per second
                        token_count = len(response_text.split())
                        tps = token_count / generation_time if generation_time > 0 else 0
                        
                        logger.info(f"Generated ~{token_count} tokens in {generation_time:.2f} seconds ({tps:.2f} tokens/sec)")
                        
                        # Update conversation history for next prompt
                        if not conversation_history:
                            conversation_history = full_prompt + " " + response_text
                        else:
                            conversation_history += f"\n\nHuman: {prompt_text}\n\nAssistant: {response_text}"
                        
                        # Write to output file
                        f.write(f"\n{'='*50}\n")
                        f.write(f"PROMPT {i+1}: {prompt_name}\n")
                        f.write(f"{'='*50}\n\n")
                        f.write(f"{prompt_text}\n\n")
                        f.write(f"{'='*50}\n")
                        f.write(f"RESPONSE:\n")
                        f.write(f"{'='*50}\n\n")
                        f.write(f"{response_text}\n\n")
                        f.write(f"Generation time: {generation_time:.2f} seconds ({tps:.2f} tokens/sec)\n\n")
                
                logger.info(f"Completed sequence {sequence_name} run {run+1} for {model_name}")
        
        # Clean up
        logger.info("Cleaning up model resources...")
        del model
        del tokenizer
        
        # Force memory cleanup
        logger.info("Forcing garbage collection...")
        for _ in range(3):
            gc.collect()
            
        log_memory_usage()
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing HF model {model_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Evaluate creative capabilities of LLMs on CPU")
    parser.add_argument("--models_config", required=True, help="JSON file containing model configurations")
    parser.add_argument("--prompts_file", required=True, help="JSON file containing prompt sequences")
    parser.add_argument("--output_dir", default="results", help="Directory to save results")
    parser.add_argument("--num_runs", type=int, default=3, help="Number of runs per prompt sequence")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load prompts and model configurations
    prompts = load_prompts(args.prompts_file)
    
    with open(args.models_config, 'r', encoding='utf-8') as f:
        models_config = json.load(f)
    
    # Log system information
    logger.info(f"Starting CPU-only evaluation with {args.num_runs} runs per prompt")
    log_memory_usage()
    
    # Process each model
    for model_config in models_config:
        model_name = model_config["name"]
        model_path = model_config["path"]
        model_type = model_config["type"]
        
        logger.info(f"Starting evaluation for {model_name}")
        
        if model_type.lower() == 'gguf':
            success = run_gguf_model(model_path, model_name, prompts, args.output_dir, args.num_runs)
        elif model_type.lower() == 'hf':
            success = run_hf_model(model_path, model_name, prompts, args.output_dir, args.num_runs)
        else:
            logger.error(f"Unknown model type: {model_type}")
            continue
        
        if success:
            logger.info(f"Successfully completed evaluation for {model_name}")
        else:
            logger.error(f"Failed to complete evaluation for {model_name}")
    
    logger.info("All evaluations complete")
    log_memory_usage()

if __name__ == "__main__":
    main()
