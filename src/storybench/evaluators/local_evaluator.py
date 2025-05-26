"""Local GGUF model evaluator using llama-cpp-python."""

import os
import time
import logging
import asyncio
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import torch
import requests
from tqdm import tqdm
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

from .base import BaseEvaluator

logger = logging.getLogger(__name__)

# Default models directory
MODELS_DIR = Path(os.environ.get("STORYBENCH_MODELS_DIR", Path.cwd() / "models"))

# Ensure models directory exists
MODELS_DIR.mkdir(exist_ok=True, parents=True)


class LocalEvaluator(BaseEvaluator):
    """Evaluator for local GGUF models using llama-cpp-python."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize local evaluator.
        
        Args:
            name: Display name for the model
            config: Model configuration dictionary containing:
                - repo_id: Hugging Face repository ID
                - filename: Model filename (e.g., model-q4_K.gguf)
                - subdirectory: Optional subdirectory in the repo
        """
        super().__init__(name, config)
        self.repo_id = config.get("repo_id")
        self.filename = config.get("filename")
        self.subdirectory = config.get("subdirectory")
        self.model_path = None
        self.llm = None
        
        # Check for required configuration
        if not self.repo_id or not self.filename:
            raise ValueError(f"Local model {name} missing required configuration: repo_id and filename")
        
    async def setup(self) -> bool:
        """Setup local model by downloading from Hugging Face and loading with llama.cpp.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        try:
            # Download model if not already present
            self.model_path = await self._download_model()
            
            # Check for GPU availability
            n_gpu_layers = -1  # Default: use all layers on GPU if available
            if torch.cuda.is_available():
                logger.info(f"CUDA is available with {torch.cuda.device_count()} devices")
                # Get available VRAM
                device = torch.cuda.current_device()
                vram_total = torch.cuda.get_device_properties(device).total_memory / (1024**3)  # GB
                vram_limit_percent = self.config.get("vram_limit_percent", 80)
                vram_available = vram_total * (vram_limit_percent / 100)
                
                logger.info(f"GPU has {vram_total:.2f} GB VRAM, using {vram_limit_percent}% ({vram_available:.2f} GB)")
            else:
                logger.info("CUDA is not available, using CPU only")
                n_gpu_layers = 0
            
            # Load the model
            logger.info(f"Loading model {self.filename} from {self.model_path}")
            self.llm = Llama(
                model_path=str(self.model_path),
                n_ctx=4096,  # Context window size
                n_batch=512,  # Batch size for prompt processing
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            logger.info(f"Successfully loaded model {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup local model {self.name}: {str(e)}")
            return False
        
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using local model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional parameters for generation
                - temperature: Sampling temperature (default: 0.8)
                - max_tokens: Maximum tokens to generate (default: 2048)
                - stop: List of strings to stop generation (default: None)
        
        Returns:
            Dict containing the generated response and metadata
        
        Raises:
            RuntimeError: If the model is not loaded
        """
        if not self.llm:
            raise RuntimeError(f"Model {self.name} is not loaded. Call setup() first.")
        
        # Extract generation parameters
        temperature = kwargs.get("temperature", 0.8)
        max_tokens = kwargs.get("max_tokens", 2048)
        stop = kwargs.get("stop", None)
        
        start_time = time.time()
        
        try:
            # Generate response
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                echo=False  # Don't include the prompt in the response
            )
            
            # Extract text from response
            generated_text = response["choices"][0]["text"].strip()
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Format response similar to API evaluators
            return {
                "text": generated_text,
                "model": self.name,
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": response["usage"]["prompt_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "total_tokens": response["usage"]["total_tokens"]
                },
                "generation_time": generation_time
            }
            
        except Exception as e:
            logger.error(f"Error generating response with {self.name}: {str(e)}")
            raise
        
    async def cleanup(self) -> None:
        """Clean up local model resources."""
        if self.llm:
            # No explicit cleanup needed for llama-cpp-python
            # Just remove the reference to free memory
            self.llm = None
            
    async def _download_model(self) -> Path:
        """Download model from Hugging Face if not already present.
        
        Returns:
            Path to the downloaded model file
        """
        # Construct model path
        model_dir = MODELS_DIR / self.repo_id.replace("/", "_")
        if self.subdirectory:
            model_dir = model_dir / self.subdirectory
            
        model_path = model_dir / self.filename
        
        # Check if model already exists
        if model_path.exists():
            logger.info(f"Model already exists at {model_path}")
            return model_path
        
        # Create directory if it doesn't exist
        model_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Downloading {self.filename} from {self.repo_id}")
        
        try:
            # Download model from Hugging Face
            downloaded_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.filename,
                subfolder=self.subdirectory,
                local_dir=model_dir,
                local_dir_use_symlinks=False
            )
            
            logger.info(f"Successfully downloaded model to {downloaded_path}")
            return Path(downloaded_path)
            
        except Exception as e:
            logger.error(f"Failed to download model {self.filename} from {self.repo_id}: {str(e)}")
            raise
