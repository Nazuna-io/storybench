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
            "n_ctx": model_settings.get("n_ctx", 4096),
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
        known_config_keys = ["repo_id", "filename", "subdirectory", "type", "provider", "name", "model_name", "model_settings", "settings"]
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
        
    def unregister_progress_callback(self, callback):
        """Unregister a progress callback.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
            
    def _send_progress(self, progress_percent: float, status_message: str):
        """Send progress update to all registered callbacks.
        
        Args:
            progress_percent: Download progress percentage (0-100)
            status_message: Status message to display
        """
        for callback in self._progress_callbacks:
            try:
                callback(progress_percent, status_message)
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")
                # Don't remove callback on error, it might be temporary
        
    async def setup(self) -> bool:
        """Setup local model by downloading from Hugging Face and loading with llama.cpp.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        try:
            # Download model if not already present
            self.model_path = await self._download_model()
            
            if not self.model_path or not self.model_path.exists():
                logger.error(f"Model file not found at {self.model_path}")
                return False
                
            # Validate model file size
            min_size_mb = 10  # Minimum expected size for a GGUF model in MB
            file_size_mb = self.model_path.stat().st_size / (1024 * 1024)
            if file_size_mb < min_size_mb:
                logger.error(f"Model file appears too small ({file_size_mb:.1f}MB < {min_size_mb}MB). File may be corrupted.")
                return False
            
            # Check for GPU availability
            gpu_info = {}
            n_gpu_layers_to_use = self.model_parameters.get("n_gpu_layers", -1)
            
            try:
                if torch.cuda.is_available():
                    device = torch.cuda.current_device()
                    gpu_info = {
                        'name': torch.cuda.get_device_name(device),
                        'vram_total': torch.cuda.get_device_properties(device).total_memory / (1024**3),  # GB
                        'count': torch.cuda.device_count()
                    }
                    vram_limit_percent = self.model_parameters.get("vram_limit_percent", 80)
                    gpu_info['vram_available'] = gpu_info['vram_total'] * (vram_limit_percent / 100)
                    
                    logger.info(
                        f"GPU: {gpu_info['name']} with {gpu_info['vram_total']:.1f}GB VRAM, "
                        f"using {vram_limit_percent}% ({gpu_info['vram_available']:.1f}GB for model with n_gpu_layers={n_gpu_layers_to_use})"
                    )
                else:
                    logger.info("CUDA is not available, using CPU only for model")
                    n_gpu_layers_to_use = 0 # Override to 0 if CUDA not available
                    
            except Exception as e:
                logger.warning(f"Error detecting GPU capabilities: {str(e)}. Falling back to CPU for model.")
                n_gpu_layers_to_use = 0 # Override to 0 on error
                
            # Load the model with error handling for common issues
            logger.info(f"Loading model {self.filename} from {self.model_path}")
            try:
                # Prepare Llama constructor arguments
                llama_args = {
                    "model_path": str(self.model_path),
                    "n_ctx": self.model_parameters.get("n_ctx", 4096),
                    "n_batch": self.model_parameters.get("n_batch", 2048),
                    "n_ubatch": self.model_parameters.get("n_ubatch", 512),
                    "n_gpu_layers": n_gpu_layers_to_use,
                    "flash_attn": self.model_parameters.get("flash_attn", False),
                    "offload_kqv": self.model_parameters.get("offload_kqv", True),
                    "use_mmap": self.model_parameters.get("use_mmap", True),
                    "use_mlock": self.model_parameters.get("use_mlock", False),
                    "split_mode": self.model_parameters.get("split_mode", 1),
                    "verbose": False
                }
                
                # Add RoPE scaling parameters if present
                if "rope_freq_base" in self.model_parameters and self.model_parameters["rope_freq_base"]:
                    llama_args["rope_freq_base"] = float(self.model_parameters["rope_freq_base"])
                if "rope_freq_scale" in self.model_parameters and self.model_parameters["rope_freq_scale"]:
                    llama_args["rope_freq_scale"] = float(self.model_parameters["rope_freq_scale"])
                
                # Handle rope_scaling_type conversion from string to int
                if "rope_scaling_type" in self.model_parameters:
                    scaling_type = self.model_parameters["rope_scaling_type"]
                    if scaling_type == "linear":
                        llama_args["rope_scaling_type"] = 1  # LLAMA_ROPE_SCALING_LINEAR
                    elif scaling_type == "yarn":
                        llama_args["rope_scaling_type"] = 2  # LLAMA_ROPE_SCALING_YARN
                    elif isinstance(scaling_type, int):
                        llama_args["rope_scaling_type"] = scaling_type
                
                # Log the context size being used
                logger.info(f"Initializing model with n_ctx={llama_args['n_ctx']}")
                if "rope_freq_base" in llama_args or "rope_freq_scale" in llama_args:
                    logger.info(f"Using RoPE scaling: base={llama_args.get('rope_freq_base', 'default')}, scale={llama_args.get('rope_freq_scale', 'default')}")
                
                self.llm = Llama(**llama_args)
                
                # Test model with a small prompt to verify it works
                test_prompt = "Once upon a time"
                test_response = self.llm(test_prompt, max_tokens=1, temperature=0)
                if not test_response or 'choices' not in test_response or not test_response['choices']:
                    raise RuntimeError("Model failed to generate test response")
                    
                logger.info(f"Successfully loaded and verified model {self.name}")
                return True
                
            except RuntimeError as e:
                if "failed to load model" in str(e).lower() or "ggml" in str(e).lower():
                    logger.error(f"Failed to load GGUF model. The file might be corrupted or incompatible. Error: {str(e)}")
                else:
                    logger.error(f"Runtime error while loading model: {str(e)}")
                return False
                
            except Exception as e:
                logger.error(f"Unexpected error while loading model: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to setup local model {self.name}: {str(e)}")
            # Clean up any partial downloads on failure
            if hasattr(self, 'model_path') and self.model_path and self.model_path.exists():
                try:
                    self.model_path.unlink()
                    logger.info(f"Cleaned up potentially corrupted model file: {self.model_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up model file: {str(cleanup_error)}")
            return False
        
    async def reset_model_state(self):
        """Reset model state between generations to prevent context corruption.
        
        This is particularly important for long sequences where the KV cache
        might get corrupted or full after large (14k+ token) generations.
        """
        if self.llm:
            try:
                # Reset the KV cache to clean state
                self.llm.reset()
                logger.debug(f"Reset model state for {self.name}")
            except Exception as e:
                logger.warning(f"Failed to reset model state for {self.name}: {e}")
                # If reset fails, try to reinitialize the model
                try:
                    logger.info(f"Reinitializing model {self.name} due to reset failure")
                    await self.setup()
                except Exception as setup_error:
                    logger.error(f"Failed to reinitialize model {self.name}: {setup_error}")
                    raise RuntimeError(f"Model {self.name} is in corrupted state and cannot be reset")

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
        
        # Extract generation parameters, using self.model_parameters as defaults
        llm_params = {
            "temperature": kwargs.get("temperature", self.model_parameters.get("temperature")),
            "max_tokens": kwargs.get("max_tokens", self.model_parameters.get("max_tokens")),
            "stop": kwargs.get("stop", self.model_parameters.get("stop")),
            "top_k": kwargs.get("top_k", self.model_parameters.get("top_k")),
            "top_p": kwargs.get("top_p", self.model_parameters.get("top_p")),
            "repeat_penalty": kwargs.get("repeat_penalty", self.model_parameters.get("repeat_penalty")),
            "echo": False  # Don't include the prompt in the response
        }
        # Remove any params that ended up as None if Llama.cpp doesn't like them
        llm_params = {k: v for k, v in llm_params.items() if v is not None}

        start_time = time.time()
        max_retries = 2  # Allow retries for stuck generations
        
        for attempt in range(max_retries + 1):
            try:
                # Log generation attempt details
                estimated_prompt_tokens = len(prompt) // 3  # Rough estimation
                max_gen_tokens = llm_params.get("max_tokens", 2048)
                logger.debug(f"Generation attempt {attempt + 1}/{max_retries + 1}: ~{estimated_prompt_tokens} prompt tokens, max {max_gen_tokens} generation tokens")
                
                # Generate response
                response = self.llm(
                    prompt,
                    **llm_params
                )
                
                # Extract text from response
                generated_text = response["choices"][0]["text"].strip()
                
                # Check if generation was successful (non-empty and reasonable length)
                if not generated_text or len(generated_text) < 10:
                    if attempt < max_retries:
                        logger.warning(f"Generation attempt {attempt + 1} produced minimal output ({len(generated_text)} chars), retrying after model reset...")
                        await self.reset_model_state()
                        continue
                    else:
                        logger.error(f"All generation attempts failed, final output length: {len(generated_text)} chars")
                
                # Calculate generation time and performance metrics
                generation_time = time.time() - start_time
                completion_tokens = response["usage"]["completion_tokens"]
                tokens_per_second = completion_tokens / generation_time if generation_time > 0 else 0
                
                # Log performance metrics
                logger.info(f"Generation completed: {completion_tokens} tokens in {generation_time:.2f}s "
                           f"({tokens_per_second:.1f} tokens/sec)")
                
                return {
                    "text": generated_text,
                    "generation_time": generation_time,
                    "tokens_per_second": tokens_per_second,
                    "completion_tokens": completion_tokens,
                    "prompt_tokens": response["usage"]["prompt_tokens"],
                    "total_tokens": response["usage"]["total_tokens"]
                }
                
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Generation attempt {attempt + 1} failed: {e}, retrying after model reset...")
                    try:
                        await self.reset_model_state()
                    except Exception as reset_error:
                        logger.error(f"Model reset failed: {reset_error}")
                        # If we can't reset, raise the original error
                        raise e
                    continue
                else:
                    # Final attempt failed, raise the error
                    logger.error(f"All generation attempts failed. Final error: {e}")
                    raise e
        
        # This should never be reached, but just in case
        raise RuntimeError("Generation failed after all retry attempts")

    async def cleanup(self) -> None:
        """Clean up local model resources."""
        if self.llm:
            # No explicit cleanup needed for llama-cpp-python
            # Just remove the reference to free memory
            self.llm = None
            
        # Clean up model file if it exists
        if hasattr(self, 'model_path') and self.model_path and self.model_path.exists():
            try:
                self.model_path.unlink()
                logger.info(f"Cleaned up model file: {self.model_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up model file: {str(cleanup_error)}")
    
    async def _download_model(self, max_retries: int = 3) -> Optional[Path]:
        """Download model from Hugging Face if not already present.
        
        Args:
            max_retries: Maximum number of download attempts
            
        Returns:
            Path to the downloaded model file, or None if download failed
            
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
                min_size = 1024  # At least 1KB to be considered valid
                file_size = model_path.stat().st_size
                if file_size > min_size:
                    logger.info(f"Using existing model file: {model_path} ({file_size/1024/1024:.1f}MB)")
                    return model_path
                    
                logger.warning(f"Existing model file appears too small ({file_size} bytes), will re-download: {model_path}")
                model_path.unlink()  # Remove corrupted file
            except OSError as e:
                logger.warning(f"Error checking existing model file, will re-download: {str(e)}")
                model_path.unlink(missing_ok=True)  # Remove if exists but can't be read
        
        # Try multiple times to download the file
        last_error = None
        for attempt in range(1, max_retries + 1):
            temp_path = model_path.with_suffix(f".download.{attempt}")
            
            try:
                # Show progress
                self._send_progress(0, f"Downloading {self.filename} (attempt {attempt}/{max_retries})...")
                
                # Download with progress using requests for better control
                url = f"https://huggingface.co/{self.repo_id}/resolve/main/"
                if self.subdirectory:
                    url += f"{self.subdirectory}/"
                url += self.filename
                
                # Use a session for connection pooling
                with requests.Session() as session:
                    # Get file size for progress tracking
                    response = session.head(url, allow_redirects=True, timeout=30)
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # Download file in chunks
                    with session.get(url, stream=True, timeout=60) as r:
                        r.raise_for_status()
                        
                        # Ensure parent directory exists
                        temp_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Download to temporary file first
                        with open(temp_path, 'wb') as f:
                            downloaded_size = 0
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    chunk_size = len(chunk)
                                    downloaded_size += chunk_size
                                    
                                    # Send progress updates periodically (every ~5%)
                                    if total_size > 0:
                                        progress = (downloaded_size / total_size) * 100
                                        if progress % 5 < (chunk_size / total_size) * 100:
                                            self._send_progress(
                                                progress,
                                                f"Downloading {self.filename}: {progress:.1f}% ({downloaded_size / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)"
                                            )
                    
                    # Rename to final filename
                    shutil.move(temp_path, model_path)
                    logger.info(f"Successfully downloaded model to {model_path}")
                    self._send_progress(100, f"Download complete: {self.filename}")
                    return model_path
                    
            except Exception as e:
                logger.warning(f"Direct download failed: {str(e)}")
                last_error = e
                
                # Only try huggingface_hub on the last attempt
                if attempt == max_retries:
                    logger.warning("Falling back to huggingface_hub...")
                    self._send_progress(0, "Direct download failed, trying alternative method...")
                    
                    try:
                        # Download model from Hugging Face
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
                else:
                    logger.warning(f"Download attempt {attempt}/{max_retries} failed, retrying...")
        
        # If we get here, all download attempts failed
        if last_error:
            error_msg = f"Failed to download model after {max_retries} attempts: {str(last_error)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # This should never be reached, but just in case
        raise RuntimeError("Failed to download model: Unknown error")
