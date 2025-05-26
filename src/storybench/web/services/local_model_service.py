"""Service for managing local GGUF models."""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

import torch
from huggingface_hub import hf_hub_download

from ..models.requests import ModelConfigRequest

# Import evaluators using relative imports to avoid module not found errors
from ...evaluators.local_evaluator import LocalEvaluator
from ...evaluators.api_evaluator import APIEvaluator
from ...evaluators.factory import EvaluatorFactory

# Import database services
from ...database.services.config_service import ConfigService

logger = logging.getLogger(__name__)

# Default models directory
MODELS_DIR = Path(os.environ.get("STORYBENCH_MODELS_DIR", Path.cwd() / "models"))

# Ensure models directory exists
MODELS_DIR.mkdir(exist_ok=True, parents=True)

# Local models configuration file
LOCAL_CONFIG_FILE = Path(os.environ.get("STORYBENCH_LOCAL_CONFIG", Path.cwd() / "config" / "local_models.json"))

# Ensure config directory exists
LOCAL_CONFIG_FILE.parent.mkdir(exist_ok=True, parents=True)


class LocalModelService:
    """Service for managing local GGUF models."""
    
    def __init__(self, database = None):
        """Initialize local model service.
        
        Args:
            database: Database connection for operations (optional)
        """
        self.database = database
        self.config_service = None
        if database:
            try:
                from ...database.services.config_service import ConfigService
                self.config_service = ConfigService(database)
            except Exception as e:
                logger.warning(f"Could not initialize config service: {str(e)}")
        self._clients = {}
        self._output_callbacks = set()
        
    def register_output_callback(self, callback):
        """Register a callback for console output."""
        self._output_callbacks.add(callback)
        
    def unregister_output_callback(self, callback):
        """Unregister a callback for console output."""
        if callback in self._output_callbacks:
            self._output_callbacks.remove(callback)
            
    def _send_output(self, message: str, message_type: str = "info"):
        """Send output to all registered callbacks."""
        for callback in self._output_callbacks:
            try:
                callback(message, message_type)
            except Exception as e:
                logger.error(f"Error in output callback: {str(e)}")
    
    async def get_hardware_info(self) -> Dict[str, Any]:
        """Get information about available hardware.
        
        Returns:
            Dict with hardware information
        """
        info = {
            "gpu_available": torch.cuda.is_available(),
            "gpu_name": "",
            "vram_gb": 0,
            "cpu_cores": os.cpu_count() or 0,
            "ram_gb": 0
        }
        
        # Get RAM information
        try:
            import psutil
            mem = psutil.virtual_memory()
            info["ram_gb"] = mem.total / (1024**3)  # Convert to GB
        except ImportError:
            logger.warning("psutil not available, RAM information will be incomplete")
            
        # Get GPU information if available
        if info["gpu_available"]:
            try:
                device = torch.cuda.current_device()
                info["gpu_name"] = torch.cuda.get_device_name(device)
                info["vram_gb"] = torch.cuda.get_device_properties(device).total_memory / (1024**3)  # GB
            except Exception as e:
                logger.error(f"Error getting GPU information: {str(e)}")
                info["gpu_available"] = False
                
        return info
    
    async def load_configuration(self) -> Dict[str, Any]:
        """Load local model configuration.
        
        Returns:
            Dict with configuration
        """
        if not LOCAL_CONFIG_FILE.exists():
            return {
                "generation_model": {
                    "repo_id": "",
                    "filename": "",
                    "subdirectory": ""
                },
                "evaluation_model": {
                    "repo_id": "",
                    "filename": "",
                    "subdirectory": ""
                },
                "use_local_evaluator": False,
                "settings": {
                    "temperature": 0.8,
                    "max_tokens": 2048,
                    "num_runs": 3,
                    "vram_limit_percent": 80,
                    "auto_evaluate": True
                }
            }
            
        try:
            with open(LOCAL_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading local model configuration: {str(e)}")
            raise
    
    async def save_configuration(self, config: Dict[str, Any]) -> None:
        """Save local model configuration.
        
        Args:
            config: Configuration to save
        """
        try:
            with open(LOCAL_CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving local model configuration: {str(e)}")
            raise
    
    async def run_local_evaluation(
        self, 
        generation_model: Dict[str, str],
        evaluation_model: Optional[Dict[str, str]],
        use_local_evaluator: bool,
        sequences: List[str],
        settings: Dict[str, Any],
        api_keys: Dict[str, str] = None
    ) -> None:
        """Run evaluation using local models.
        
        Args:
            generation_model: Generation model configuration
            evaluation_model: Evaluation model configuration (if using local evaluator)
            use_local_evaluator: Whether to use local evaluator
            sequences: Sequences to evaluate
            settings: Generation settings
            api_keys: API keys for API evaluator (if not using local evaluator)
        """
        # For demonstration purposes, we'll use some sample prompts if database is not available
        prompts_dict = {}
        
        if self.config_service:
            try:
                # Load prompts from database if available
                prompts_config = await self.config_service.get_active_prompts()
                if prompts_config and hasattr(prompts_config, 'prompts') and isinstance(prompts_config.prompts, dict):
                    prompts_dict = prompts_config.prompts
            except Exception as e:
                self._send_output(f"Error loading prompts from database: {str(e)}", "warning")
        
        # If no prompts from database, use sample prompts
        if not prompts_dict:
            self._send_output("Using sample prompts for demonstration", "info")
            prompts_dict = {
                "FilmNarrative": [
                    {"name": "Premise", "text": "Write a film premise about a character who discovers an unexpected talent."},
                    {"name": "Character", "text": "Describe the main character in detail, including their background, personality, and motivations. {{context}}"},
                    {"name": "Scene", "text": "Write a key scene where the character's talent is revealed. {{context}}"}
                ],
                "LiteraryNarrative": [
                    {"name": "Setting", "text": "Create a vivid setting for a short story."},
                    {"name": "Character", "text": "Introduce the protagonist who inhabits this setting. {{context}}"},
                    {"name": "Conflict", "text": "Describe the central conflict that drives the story. {{context}}"}
                ]
            }
            
        # Filter sequences
        available_sequences = set(prompts_dict.keys())
        selected_sequences = [seq for seq in sequences if seq in available_sequences]
        
        if not selected_sequences:
            self._send_output("No valid sequences selected", "error")
            return
            
        self._send_output(f"Starting evaluation with {len(selected_sequences)} sequences", "info")
        
        # Create generation model
        gen_model_name = f"local_{generation_model['filename']}"
        gen_model_config = {
            "type": "local",
            "repo_id": generation_model["repo_id"],
            "filename": generation_model["filename"],
            "subdirectory": generation_model.get("subdirectory", ""),
            "vram_limit_percent": settings.get("vram_limit_percent", 80)
        }
        
        try:
            # Initialize generation model
            self._send_output(f"Initializing generation model: {gen_model_name}", "info")
            generation_evaluator = LocalEvaluator(gen_model_name, gen_model_config)
            
            # Setup generation model
            self._send_output("Setting up generation model...", "info")
            setup_success = await generation_evaluator.setup()
            
            if not setup_success:
                self._send_output("Failed to setup generation model", "error")
                return
                
            self._send_output("Generation model ready", "info")
            
            # Initialize evaluation model if using local evaluator
            evaluation_evaluator = None
            if use_local_evaluator and evaluation_model:
                eval_model_name = f"local_{evaluation_model['filename']}"
                eval_model_config = {
                    "type": "local",
                    "repo_id": evaluation_model["repo_id"],
                    "filename": evaluation_model["filename"],
                    "subdirectory": evaluation_model.get("subdirectory", ""),
                    "vram_limit_percent": settings.get("vram_limit_percent", 80)
                }
                
                self._send_output(f"Initializing evaluation model: {eval_model_name}", "info")
                evaluation_evaluator = LocalEvaluator(eval_model_name, eval_model_config)
                
                # Setup evaluation model
                self._send_output("Setting up evaluation model...", "info")
                eval_setup_success = await evaluation_evaluator.setup()
                
                if not eval_setup_success:
                    self._send_output("Failed to setup evaluation model, falling back to API evaluator", "error")
                    evaluation_evaluator = None
                    use_local_evaluator = False
                else:
                    self._send_output("Evaluation model ready", "info")
            
            # Process each sequence
            for sequence_name in selected_sequences:
                sequence_prompts = prompts_dict.get(sequence_name, [])
                if not sequence_prompts:
                    self._send_output(f"No prompts found for sequence: {sequence_name}", "warning")
                    continue
                    
                self._send_output(f"Processing sequence: {sequence_name} ({len(sequence_prompts)} prompts)", "info")
                
                # Run each prompt in the sequence
                for run_idx in range(settings.get("num_runs", 1)):
                    self._send_output(f"Run {run_idx + 1}/{settings.get('num_runs', 1)}", "info")
                    
                    responses = []
                    context = ""
                    
                    for prompt_idx, prompt_data in enumerate(sequence_prompts):
                        prompt_name = prompt_data.get("name", f"Prompt {prompt_idx + 1}")
                        prompt_text = prompt_data.get("text", "")
                        
                        if not prompt_text:
                            self._send_output(f"Empty prompt text for: {prompt_name}", "warning")
                            continue
                            
                        # Add context from previous responses
                        full_prompt = prompt_text
                        if context and "{{context}}" in prompt_text:
                            full_prompt = prompt_text.replace("{{context}}", context)
                            
                        self._send_output(f"Generating response for: {prompt_name}", "info")
                        
                        try:
                            # Generate response
                            response = await generation_evaluator.generate_response(
                                full_prompt,
                                temperature=settings.get("temperature", 0.8),
                                max_tokens=settings.get("max_tokens", 2048)
                            )
                            
                            response_text = response.get("text", "")
                            tokens = response.get("usage", {}).get("total_tokens", 0)
                            
                            self._send_output(
                                f"Response generated: {len(response_text)} chars, {tokens} tokens", 
                                "output"
                            )
                            
                            # Store response
                            responses.append({
                                "prompt_name": prompt_name,
                                "prompt_text": prompt_text,
                                "response_text": response_text,
                                "tokens": tokens
                            })
                            
                            # Update context for next prompt
                            context += response_text + "\n\n"
                            
                        except Exception as e:
                            self._send_output(f"Error generating response: {str(e)}", "error")
                            break
                    
                    # Store responses in database
                    try:
                        if self.database:
                            from ...database.repositories.response_repo import ResponseRepository
                            from ...database.models import Response, ResponseStatus
                            from datetime import datetime
                            
                            # Create response repository
                            response_repo = ResponseRepository(self.database)
                            
                            # Generate a unique evaluation ID for this run
                            from bson import ObjectId
                            evaluation_id = str(ObjectId())
                            
                            # Store each response in the database
                            for prompt_idx, response_data in enumerate(responses):
                                response_obj = Response(
                                    evaluation_id=evaluation_id,
                                    model_name=gen_model_name,
                                    sequence=sequence_name,
                                    run=run_idx,
                                    prompt_index=prompt_idx,
                                    prompt_name=response_data["prompt_name"],
                                    prompt_text=response_data["prompt_text"],
                                    response=response_data["response_text"],
                                    generation_time=0.0,  # We don't track this yet
                                    completed_at=datetime.utcnow(),
                                    status=ResponseStatus.COMPLETED
                                )
                                
                                await response_repo.create(response_obj)
                                
                            self._send_output(f"Stored {len(responses)} responses in database with evaluation ID: {evaluation_id}", "info")
                        else:
                            self._send_output("Database not available, responses not stored", "warning")
                        
                        # Run evaluation if enabled
                        if settings.get("auto_evaluate", True) and responses:
                            if use_local_evaluator and evaluation_evaluator:
                                self._send_output("Running local evaluation...", "info")
                                
                                # Get evaluation criteria
                                criteria = None
                                if self.database and self.config_service:
                                    try:
                                        criteria_config = await self.config_service.get_active_criteria()
                                        if criteria_config and hasattr(criteria_config, 'criteria'):
                                            criteria = criteria_config.criteria
                                    except Exception as e:
                                        self._send_output(f"Error loading criteria from database: {str(e)}", "warning")
                                
                                if not criteria:
                                    # Use sample criteria if database is not available
                                    self._send_output("Using sample evaluation criteria", "info")
                                    criteria = {
                                        "creativity": "Rate the creativity of the response on a scale of 1-10",
                                        "coherence": "Rate the coherence of the response on a scale of 1-10",
                                        "relevance": "Rate how relevant the response is to the prompt on a scale of 1-10"
                                    }
                                
                                # Run evaluation for each response
                                for prompt_idx, response_data in enumerate(responses):
                                    try:
                                        # Create evaluation prompt
                                        eval_prompt = f"""You are an expert evaluator. Please evaluate the following response to a prompt.
                                        
                                        PROMPT: {response_data['prompt_text']}
                                        
                                        RESPONSE: {response_data['response_text']}
                                        
                                        Please evaluate the response on the following criteria:
                                        """
                                        
                                        for criterion_name, criterion_desc in criteria.items():
                                            eval_prompt += f"\n- {criterion_name}: {criterion_desc}"
                                        
                                        eval_prompt += "\n\nProvide your evaluation as a JSON object with scores for each criterion on a scale of 1-10 and brief explanations."
                                        
                                        # Generate evaluation
                                        eval_response = await evaluation_evaluator.generate_response(
                                            eval_prompt,
                                            temperature=0.3,
                                            max_tokens=1024
                                        )
                                        
                                        eval_text = eval_response.get("text", "")
                                        
                                        # Store evaluation in database if available
                                        if self.database:
                                            from ...database.repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository
                                            from ...database.models import ResponseLLMEvaluation
                                            
                                            # Create evaluation repository
                                            eval_repo = ResponseLLMEvaluationRepository(self.database)
                                            
                                            # Parse evaluation results (simple approach)
                                            import re
                                            import json
                                            
                                            # Try to extract JSON from the response
                                            json_match = re.search(r'\{[\s\S]*\}', eval_text)
                                            scores = {}
                                            
                                            if json_match:
                                                try:
                                                    json_str = json_match.group(0)
                                                    scores = json.loads(json_str)
                                                except:
                                                    self._send_output("Failed to parse evaluation JSON", "warning")
                                            
                                            # Create evaluation object
                                            from ...database.models import CriterionEvaluation
                                            
                                            # Create criterion evaluations from scores
                                            criteria_results = []
                                            for criterion_name, score_info in scores.items():
                                                # Extract score and explanation from the score_info
                                                score = score_info.get('score', 0) if isinstance(score_info, dict) else score_info
                                                explanation = score_info.get('explanation', '') if isinstance(score_info, dict) else ''
                                                
                                                criteria_results.append(CriterionEvaluation(
                                                    criterion_name=criterion_name,
                                                    score=float(score),
                                                    justification=explanation
                                                ))
                                            
                                            # Get or create a dummy evaluation criteria ID
                                            from bson import ObjectId
                                            evaluation_criteria_id = ObjectId()
                                            
                                            eval_obj = ResponseLLMEvaluation(
                                                response_id=ObjectId(),  # This should be the actual response ID
                                                evaluating_llm_provider='local',
                                                evaluating_llm_model=eval_model_name,
                                                evaluation_criteria_id=evaluation_criteria_id,
                                                criteria_results=criteria_results
                                            )
                                            
                                            await eval_repo.create(eval_obj)
                                            
                                        self._send_output(f"Evaluated response for {response_data['prompt_name']}", "info")
                                        
                                    except Exception as e:
                                        self._send_output(f"Error evaluating response: {str(e)}", "error")
                            else:
                                self._send_output("Running API evaluation...", "info")
                                
                                # If API keys are available, use API evaluator
                                if api_keys and any(api_keys.values()):
                                    try:
                                        from ...evaluators.factory import EvaluatorFactory
                                        
                                        # Get evaluation model from config
                                        eval_model_config = None
                                        if self.database and self.config_service:
                                            try:
                                                models_config = await self.config_service.get_active_models()
                                                if models_config and hasattr(models_config, 'models'):
                                                    for model in models_config.models:
                                                        if model.get('is_evaluator', False):
                                                            eval_model_config = model
                                                            break
                                            except Exception as e:
                                                self._send_output(f"Error loading models from database: {str(e)}", "warning")
                                        
                                        if eval_model_config:
                                            # Create API evaluator
                                            api_evaluator = EvaluatorFactory.create_evaluator(
                                                eval_model_config['name'],
                                                eval_model_config,
                                                api_keys
                                            )
                                            
                                            # Setup API evaluator
                                            await api_evaluator.setup()
                                            
                                            # TODO: Implement API evaluation similar to local evaluation
                                            self._send_output("API evaluation integration not fully implemented", "warning")
                                        else:
                                            self._send_output("No evaluation model configured", "warning")
                                    except Exception as e:
                                        self._send_output(f"Error setting up API evaluator: {str(e)}", "error")
                                else:
                                    self._send_output("No API keys available for evaluation", "warning")
                    except Exception as e:
                        self._send_output(f"Error storing responses: {str(e)}", "error")
                
            self._send_output("Evaluation completed successfully", "info")
            
        except Exception as e:
            self._send_output(f"Error running evaluation: {str(e)}", "error")
        finally:
            # Cleanup resources
            if generation_evaluator:
                await generation_evaluator.cleanup()
            if evaluation_evaluator:
                await evaluation_evaluator.cleanup()
