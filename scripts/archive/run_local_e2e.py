#!/usr/bin/env python3
"""
Wrapper script to run end-to-end evaluation using only local models.
This ensures no API calls are made during the process.
"""
import os
import sys
import asyncio
import logging
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('local_e2e.log')
    ]
)
logger = logging.getLogger(__name__)

def load_model_config(config_path: str) -> Dict[str, Any]:
    """Load and validate model configuration."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if not isinstance(config, dict) or "models" not in config or not config["models"]:
            raise ValueError("Invalid model configuration: missing or empty 'models' list")
            
        return config
    except Exception as e:
        logger.error(f"Failed to load model config from {config_path}: {e}")
        raise

def update_model_settings(config: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update model settings with the provided updates."""
    updated = config.copy()
    for model in updated.get("models", []):
        if "model_settings" not in model:
            model["model_settings"] = {}
        model["model_settings"].update(updates)
    return updated

def main():
    # Set environment variables to prevent API usage
    os.environ["STORYBENCH_FORCE_LOCAL"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU
    
    # Paths to configurations
    base_config_path = "config/local_only_models.json"
    eval_config_path = "config/local_only_models.json"
    
    # Load and validate configurations
    try:
        # Load base config for generation
        base_config = load_model_config(base_config_path)
        gen_model_name = "Gemma-3-1B-IT-Q2_K_L"
        
        # Load evaluation config
        eval_config = load_model_config(eval_config_path)
        eval_model_name = "Gemma-3-1B-IT-Q2_K_L"
        
        logger.info(f"Using generation model: {gen_model_name}")
        logger.info(f"Using evaluation model: {eval_model_name}")
        
        # Add memory optimization settings
        base_config = update_model_settings(base_config, {
            "n_threads": 4,  # Use 4 CPU threads
            "n_threads_batch": 4,  # Use 4 CPU threads for batch processing
            "n_ctx": 16384,  # Smaller context window for generation
            "n_batch": 2048,  # Smaller batch size
            "n_ubatch": 512,  # Smaller micro-batch size
        })
        
        # Save updated configs
        updated_base_path = "config/local_only_models_updated.json"
        with open(updated_base_path, 'w') as f:
            json.dump(base_config, f, indent=2)
        
        updated_eval_path = "config/local_only_models_eval_updated.json"
        with open(updated_eval_path, 'w') as f:
            json.dump(eval_config, f, indent=2)
            
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Build the command with proper error handling
    try:
        cmd = [
            sys.executable, "run_end_to_end.py",
            "--models", gen_model_name,
            "--local-config", updated_base_path,
            "--evaluator-model", eval_model_name,
            "--auto-evaluate"
        ]
        
        logger.info("Starting end-to-end evaluation with local models...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        # Run the command with real-time output
        async def run_command():
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ
            )
            
            # Stream stdout and stderr in real-time
            async def stream_output(stream, is_error=False):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line = line.decode().strip()
                    if is_error:
                        logger.error(line)
                    else:
                        logger.info(line)
            
            # Start output streams
            await asyncio.gather(
                stream_output(process.stdout, False),
                stream_output(process.stderr, True)
            )
            
            # Wait for process to complete
            return_code = await process.wait()
            if return_code != 0:
                logger.error(f"Process failed with return code {return_code}")
            return return_code
        
        # Run the async command
        return asyncio.run(run_command())
        
    except Exception as e:
        logger.error(f"Error running evaluation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
