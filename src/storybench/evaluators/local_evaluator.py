"""Enhanced Local GGUF model evaluator using LangChain and llama-cpp-python."""

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

from .base import BaseEvaluator
from ..unified_context_system import create_32k_system, create_128k_system, create_1m_system, ContextLimitExceededError

logger = logging.getLogger(__name__)

# Default models directory
MODELS_DIR = Path(os.environ.get("STORYBENCH_MODELS_DIR", Path.cwd() / "models"))

# Ensure models directory exists
MODELS_DIR.mkdir(exist_ok=True, parents=True)


class LocalEvaluator(BaseEvaluator):
    """Enhanced evaluator for local GGUF models using LangChain integration."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize local evaluator with LangChain context management.
        
        Args:
            name: Display name for the model
            config: Model configuration dictionary containing:
                - repo_id: Hugging Face repository ID
                - filename: Model filename (e.g., model-q4_K.gguf)
                - subdirectory: Optional subdirectory in the repo
                - context_size: Context window size (default: 32768)
        """
        # Set context size before calling super().__init__
        context_size = config.get('context_size', 32768)  # Default to 32K
        config['context_size'] = context_size  # Ensure it's in config for parent
        
        super().__init__(name, config)
        self.repo_id = config.get("repo_id")
        self.filename = config.get("filename")
        self.subdirectory = config.get("subdirectory")
        self.model_path = None
        self.llm = None  # This will be the LangChain wrapper
        self._progress_callbacks = set()
        
        # Store model parameters from config, applying defaults
        # Handle both flattened config (from run_end_to_end.py) and nested "model_settings"/"settings"
        if "model_settings" in config:
            model_settings = config["model_settings"]
        elif "settings" in config:
            model_settings = config["settings"]
        else:
            # Flattened format - use the config directly
            model_settings = config        
        self.model_parameters = {
            "n_gpu_layers": model_settings.get("n_gpu_layers", -1),  # -1 for all layers to GPU
            "n_ctx": context_size,  # Use configured context size
            "n_batch": model_settings.get("n_batch", 2048),  # Increased for better GPU utilization
            "n_ubatch": model_settings.get("n_ubatch", 512),  # Micro-batch size
            "temperature": model_settings.get("temperature", 0.8),
            "max_tokens": model_settings.get("max_tokens", 2048),
            "stop": model_settings.get("stop", None),
            "vram_limit_percent": model_settings.get("vram_limit_percent", 80),
            "top_k": model_settings.get("top_k", 40),
            "top_p": model_settings.get("top_p", 0.95),
            "repeat_penalty": model_settings.get("repeat_penalty", 1.1),
            # Performance optimization parameters
            "flash_attn": model_settings.get("flash_attn", False),
            "offload_kqv": model_settings.get("offload_kqv", True),
            "use_mmap": model_settings.get("use_mmap", True),
            "use_mlock": model_settings.get("use_mlock", False),
            "split_mode": model_settings.get("split_mode", 1),
            # RoPE scaling parameters
            "rope_freq_base": model_settings.get("rope_freq_base"),
            "rope_freq_scale": model_settings.get("rope_freq_scale"),
            "rope_scaling_type": model_settings.get("rope_scaling_type")
        }
        
        # Capture any other settings passed in the config that are not standard init args for Llama
        # These might be other specific GGUF parameters the user wants to pass.
        known_config_keys = ["repo_id", "filename", "subdirectory", "type", "provider", "name", "model_name", "model_settings", "settings", "context_size"]
        for key, value in model_settings.items():
            if key not in self.model_parameters:
                self.model_parameters[key] = value
        
        # Check for required configuration
        if not self.repo_id or not self.filename:
            raise ValueError(f"Local model {name} missing required configuration: repo_id and filename")
    
    def register_progress_callback(self, callback):
        """Register a callback for download progress updates.
        
        Args:
            callback: Function that takes (progress_percent, status_message) as arguments
        """
        self._progress_callbacks.add(callback)
    
    def _send_progress(self, progress: float, status: str):
        """Send progress updates to registered callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(progress, status)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    async def setup(self) -> bool:
        """Setup the evaluator by downloading and loading the model with LangChain."""
        try:
            logger.info(f"Setting up LocalEvaluator for {self.name}")
            
            # Download model if needed
            self._send_progress(0, f"Checking model: {self.filename}")
            print(f"DEBUG: About to download model for {self.name}")
            self.model_path = await self._download_model()
            print(f"DEBUG: Model download completed for {self.name}")
            
            if not self.model_path or not self.model_path.exists():
                logger.error(f"Model file not found after download: {self.model_path}")
                return False            
            logger.info(f"Model path confirmed: {self.model_path}")
            self._send_progress(50, "Loading model with LangChain...")
            
            # Create unified LangChain system - context manager + LLM wrapper
            context_size = self.model_parameters["n_ctx"]
            logger.info(f"Initializing LangChain system with {context_size} context size")
            print(f"DEBUG: About to create unified system for {self.name}")
            
            # Create the unified system based on context size
            if context_size <= 32768:
                # Use 32K system
                logger.info("Using 32K unified context system")
                model_params = {k: v for k, v in self.model_parameters.items() if k != 'n_ctx'}
                print(f"DEBUG: Calling create_32k_system for {self.name}")
                unified_context_manager, self.llm = create_32k_system(
                    model_path=str(self.model_path),
                    **model_params
                )
                print(f"DEBUG: create_32k_system completed for {self.name}")
                # Replace our context manager with the unified one for consistency
                self.context_manager = unified_context_manager
                
            elif context_size <= 131072:
                # Use 128K system  
                logger.info("Using 128K unified context system")
                model_params = {k: v for k, v in self.model_parameters.items() if k != 'n_ctx'}
                unified_context_manager, self.llm = create_128k_system(
                    model_path=str(self.model_path),
                    **model_params
                )
                self.context_manager = unified_context_manager
                
            else:
                # Use 1M system for very large contexts
                logger.info("Using 1M unified context system") 
                model_params = {k: v for k, v in self.model_parameters.items() if k != 'n_ctx'}
                unified_context_manager, self.llm = create_1m_system(
                    model_path=str(self.model_path),
                    **model_params
                )
                self.context_manager = unified_context_manager
            
            print(f"DEBUG: Unified system created, about to test for {self.name}")
            logger.info(f"LangChain system initialized with {self.context_manager.max_context_tokens} token context")
            
            # Test the model with a simple prompt
            self._send_progress(90, "Testing model...")
            test_prompt = "Hello, this is a test."
            
            try:
                print(f"DEBUG: About to validate context for {self.name}")
                # Validate test prompt doesn't exceed context
                self.validate_context_size(test_prompt)
                print(f"DEBUG: Context validation passed for {self.name}")
                
                # Test generation
                print(f"DEBUG: About to test generation for {self.name}")
                test_response = self.llm(test_prompt, max_tokens=10, temperature=0.1)
                print(f"DEBUG: Test generation completed for {self.name}")
                logger.info(f"Model test successful: {len(test_response)} chars generated")
                
            except Exception as e:
                logger.error(f"Model test failed: {e}")
                print(f"DEBUG: Model test failed for {self.name}: {e}")
                return False
            
            self.is_setup = True
            self._send_progress(100, f"Model {self.name} ready")
            logger.info(f"LocalEvaluator {self.name} setup complete")
            print(f"DEBUG: Setup completed successfully for {self.name}")
            return True            
        except Exception as e:
            logger.error(f"Failed to setup LocalEvaluator {self.name}: {e}")
            print(f"DEBUG: Setup failed for {self.name}: {e}")
            self._send_progress(0, f"Setup failed: {str(e)}")
            return False
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using LangChain-wrapped local model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional parameters for generation
        
        Returns:
            Dict containing the generated response and metadata
        
        Raises:
            RuntimeError: If the model is not loaded
            ContextLimitExceededError: If prompt exceeds context limits
        """
        if not self.llm:
            raise RuntimeError(f"Model {self.name} is not loaded. Call setup() first.")
        
        start_time = time.time()
        
        try:
            # STRICT CONTEXT VALIDATION - No truncation allowed
            context_stats = self.validate_context_size(prompt)
            
            # Get detailed analytics for evaluation reports
            context_analytics = self.get_context_analytics(prompt)
            logger.info(f"Context validation passed for {self.name}: "
                       f"hash={context_analytics['prompt_hash']}, "
                       f"tokens={context_analytics['estimated_tokens']}/{context_analytics['max_tokens']}, "
                       f"utilization={context_analytics['utilization_percent']:.1f}%")
            
            # Extract generation parameters, using self.model_parameters as defaults
            llm_params = {
                "temperature": kwargs.get("temperature", self.model_parameters.get("temperature")),
                "max_tokens": kwargs.get("max_tokens", self.model_parameters.get("max_tokens")),
                "stop": kwargs.get("stop", self.model_parameters.get("stop")),
                "top_k": kwargs.get("top_k", self.model_parameters.get("top_k")),
                "top_p": kwargs.get("top_p", self.model_parameters.get("top_p")),
                "repeat_penalty": kwargs.get("repeat_penalty", self.model_parameters.get("repeat_penalty")),
            }
            # Remove any params that ended up as None
            llm_params = {k: v for k, v in llm_params.items() if v is not None}

            max_retries = 2  # Allow retries for stuck generations
            
            for attempt in range(max_retries + 1):
                try:
                    # Log generation attempt details
                    max_gen_tokens = llm_params.get("max_tokens", 2048)
                    logger.debug(f"Generation attempt {attempt + 1}/{max_retries + 1}: "
                               f"{context_analytics['estimated_tokens']} prompt tokens, "
                               f"max {max_gen_tokens} generation tokens, "
                               f"hash={context_analytics['prompt_hash']}")
                    
                    # Generate response using LangChain wrapper
                    response_text = self.llm(prompt, **llm_params)
                    
                    # Validate response
                    if response_text is None:
                        generated_text = ""
                    else:
                        generated_text = response_text.strip() if isinstance(response_text, str) else str(response_text).strip()
                    
                    # Log what we got for debugging
                    logger.debug(f"Generated text length: {len(generated_text)} chars")
                    
                    # For story generation, anything under 100 chars indicates a problem
                    min_expected_length = 100  # Minimum chars for a reasonable story response                    
                    if len(generated_text) < min_expected_length and attempt < max_retries:
                        logger.warning(f"Generation attempt {attempt + 1} produced insufficient output ({len(generated_text)} chars < {min_expected_length} expected), retrying...")
                        # Reset model state for retry
                        await self.reset_model_state()
                        continue
                    
                    # Success - return response with context stats
                    try:
                        model_name = getattr(self.llm, 'model_name', self.name)
                    except AttributeError:
                        model_name = self.name
                    
                    metadata = {
                        "model_name": model_name,
                        "model_path": str(self.model_path) if hasattr(self, 'model_path') else "unknown",
                        "generation_params": llm_params,
                        "attempts": attempt + 1
                    }
                    
                    return self._create_response_dict(
                        generated_text, 
                        start_time, 
                        metadata=metadata,
                        context_stats=context_analytics
                    )
                    
                except Exception as e:
                    if attempt == max_retries:
                        raise RuntimeError(f"Model generation failed after {max_retries + 1} attempts: {str(e)}")
                    logger.warning(f"Generation attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(1)  # Brief pause before retry
                    continue
                    
        except ContextLimitExceededError:
            # Re-raise context errors without modification
            raise
        except Exception as e:
            error_msg = f"Generation failed for {self.name}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def reset_model_state(self):
        """Reset model state for retry attempts."""
        try:
            # For LangChain LlamaCpp wrapper, we don't have direct access to reset
            # But we can clear any cached state if needed
            if hasattr(self.llm, 'reset'):
                self.llm.reset()
            logger.debug(f"Model state reset for {self.name}")
        except Exception as e:
            logger.warning(f"Failed to reset model state: {e}")
    
    async def cleanup(self):
        """Clean up model resources."""
        try:
            if self.llm:
                # LangChain wrapper cleanup
                if hasattr(self.llm, 'client') and hasattr(self.llm.client, 'close'):
                    self.llm.client.close()
                self.llm = None
            self.is_setup = False
            logger.info(f"LocalEvaluator {self.name} cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup for {self.name}: {e}")
    
    async def _download_model(self, max_retries: int = 3) -> Path:
        """Ensure model is downloaded and return path to model file.
        
        Args:
            max_retries: Maximum number of download attempts
            
        Returns:
            Path to the downloaded model file
            
        Raises:
            RuntimeError: If download fails after all retries
        """
        # Construct model path
        model_dir = MODELS_DIR / self.repo_id.replace("/", "_")
        if self.subdirectory:
            model_dir = model_dir / self.subdirectory
            
        # Ensure directory exists
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / self.filename
        
        # Return if model already exists and is valid
        if model_path.exists():
            try:
                # Quick check if file is not corrupted
                min_size_mb = 10  # At least 10MB to be considered valid
                file_size_mb = model_path.stat().st_size / (1024 * 1024)
                if file_size_mb > min_size_mb:
                    logger.info(f"Using existing model file: {model_path} ({file_size_mb:.1f}MB)")
                    return model_path
                    
                logger.warning(f"Existing model file appears too small ({file_size_mb:.1f}MB < {min_size_mb}MB), will re-download: {model_path}")
                model_path.unlink()  # Remove corrupted file
            except OSError as e:
                logger.warning(f"Error checking existing model file, will re-download: {str(e)}")
                model_path.unlink(missing_ok=True)  # Remove if exists but can't be read
        
        # Try multiple times to download the file
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Download attempt {attempt}/{max_retries}: {self.filename}")
                self._send_progress(0, f"Downloading {self.filename} (attempt {attempt}/{max_retries})...")
                
                # Try direct download first
                temp_path = model_path.with_suffix(f".download.{attempt}")
                
                try:
                    # Use huggingface_hub for download
                    downloaded_path = hf_hub_download(
                        repo_id=self.repo_id,
                        filename=self.filename,
                        subfolder=self.subdirectory,
                        local_dir=model_dir,
                        local_dir_use_symlinks=False,
                        resume_download=True,  # Resume partial downloads
                        force_download=False    # Don't redownload if exists
                    )
                    
                    logger.info(f"Successfully downloaded model to {downloaded_path}")
                    self._send_progress(100, f"Download complete: {self.filename}")
                    return Path(downloaded_path)
                    
                except Exception as hub_error:
                    logger.error(f"Failed to download model using huggingface_hub: {str(hub_error)}")
                    last_error = hub_error
                        
            except Exception as e:
                last_error = e
                logger.warning(f"Download attempt {attempt}/{max_retries} failed: {str(e)}")
        
        # If we get here, all download attempts failed
        if last_error:
            error_msg = f"Failed to download model after {max_retries} attempts: {str(last_error)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # This should never be reached, but just in case
        raise RuntimeError("Failed to download model: Unknown error")
