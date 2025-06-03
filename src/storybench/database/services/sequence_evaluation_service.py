"""
Sequence-aware LLM Evaluation Service for evaluating creative writing responses in context.
This service evaluates responses by sequence to properly assess coherence across related prompts.
"""

import asyncio
from bson import ObjectId
import logging
from typing import List, Dict, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

# Removed: from openai import AsyncOpenAI
from ...evaluators.factory import EvaluatorFactory # Added
from ...models.config import ModelConfig as StoryBenchModelConfig # ModelConfig is our updated one
from ..repositories.response_repo import ResponseRepository
from ..repositories.criteria_repo import CriteriaRepository
from ..repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository
from ..models import Response, ResponseLLMEvaluation, CriterionEvaluation, EvaluationCriteria

logger = logging.getLogger(__name__)

class SequenceEvaluationService:
    """Service for evaluating creative writing responses with sequence context for proper coherence assessment."""
    
    def __init__(self, database: AsyncIOMotorDatabase, 
                 evaluator_model_config: StoryBenchModelConfig, 
                 api_keys: Dict[str, str]):
        self.database = database
        self.response_repo = ResponseRepository(database)
        self.criteria_repo = CriteriaRepository(database)
        self.evaluation_repo = ResponseLLMEvaluationRepository(database)
        
        self.evaluator_model_config = evaluator_model_config # Store for later use

        factory_eval_config = {
            "type": evaluator_model_config.type,
            "provider": evaluator_model_config.provider,
            "model_name": evaluator_model_config.model_name,
        }

        if evaluator_model_config.type == "local":
            if evaluator_model_config.repo_id:
                factory_eval_config["repo_id"] = evaluator_model_config.repo_id
            if evaluator_model_config.filename:
                factory_eval_config["filename"] = evaluator_model_config.filename
            if evaluator_model_config.subdirectory:
                factory_eval_config["subdirectory"] = evaluator_model_config.subdirectory
            
            # Merge model_settings if they exist. These are parameters like temperature, n_gpu_layers, etc.
            if evaluator_model_config.model_settings:
                factory_eval_config.update(evaluator_model_config.model_settings)
                logger.info(f"SequenceEvaluationService: Using model_settings for local evaluator {evaluator_model_config.name}: {evaluator_model_config.model_settings}")

        self.evaluator = EvaluatorFactory.create_evaluator(
            name=evaluator_model_config.name, # This is the display name / identifier
            config=factory_eval_config, # This dict goes to the evaluator's __init__ as 'config'
            api_keys=api_keys if evaluator_model_config.type == "api" else {}
        )

    async def initialize(self):
        """Initializes the evaluator by calling its setup method."""
        if hasattr(self.evaluator, 'setup') and callable(self.evaluator.setup):
            logger.info(f"Setting up evaluator {self.evaluator.name} for SequenceEvaluationService...")
            await self.evaluator.setup()
            logger.info(f"Evaluator {self.evaluator.name} setup complete for SequenceEvaluationService.")
        else:
            logger.warning(f"Evaluator {self.evaluator.name} does not have a callable setup method.")

    async def evaluate_all_sequences(self) -> Dict[str, Any]:
        """Evaluate all response sequences that haven't been evaluated yet."""
        
        # Get active evaluation criteria
        criteria_config = await self.criteria_repo.find_active()
        if not criteria_config:
            raise ValueError("No active evaluation criteria found")
        
        # Get all responses and group by sequence context
        all_responses = await self.response_repo.find_many({})
        logger.info(f"Found {len(all_responses)} total responses")
        
        # Group responses by (model, sequence, run) to create complete sequences
        sequence_groups = self._group_responses_by_sequence(all_responses)
        
        # Filter out already evaluated sequences
        unevaluated_sequences = []
        for sequence_key, responses in sequence_groups.items():
            # Check if any response in this sequence has been evaluated
            sequence_evaluated = False
            for response in responses:
                existing_evals = await self.evaluation_repo.get_evaluations_by_response_id(response.id)
                if existing_evals:
                    sequence_evaluated = True
                    break
            
            if not sequence_evaluated:
                unevaluated_sequences.append((sequence_key, responses))
        
        logger.info(f"Found {len(unevaluated_sequences)} unevaluated sequences")
        
        # Evaluate each sequence
        results = {
            "total_sequences": len(sequence_groups),
            "unevaluated_sequences": len(unevaluated_sequences),
            "sequences_evaluated": 0,
            "total_evaluations_created": 0,
            "errors": []
        }
        
        for i, (sequence_key, responses) in enumerate(unevaluated_sequences):
            try:
                model_name, sequence_name, run = sequence_key
                print(f"🔍 Evaluating sequence {i+1}/{len(unevaluated_sequences)}: {model_name} - {sequence_name} - Run {run}", flush=True)
                
                sequence_evaluations = await self.evaluate_sequence(responses, criteria_config)
                if sequence_evaluations:
                    results["sequences_evaluated"] += 1
                    results["total_evaluations_created"] += len(sequence_evaluations)
                    print(f"✅ Success! Created {len(sequence_evaluations)} evaluations", flush=True)
                    
                # Add delay to avoid rate limiting
                await asyncio.sleep(3)
                
            except Exception as e:
                error_msg = f"Failed to evaluate sequence {sequence_key}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}", flush=True)
        
        return results
    
    def _group_responses_by_sequence(self, responses: List[Response]) -> Dict[Tuple[str, str, int], List[Response]]:
        """Group responses by (model_name, sequence, run) and sort by prompt_index."""
        
        sequence_groups = {}
        
        for response in responses:
            # Create key for grouping
            sequence_key = (response.model_name, response.sequence, response.run)
            
            if sequence_key not in sequence_groups:
                sequence_groups[sequence_key] = []
            
            sequence_groups[sequence_key].append(response)
        
        # Sort each group by prompt_index to ensure proper order
        for sequence_key in sequence_groups:
            sequence_groups[sequence_key].sort(key=lambda r: r.prompt_index)
        
        return sequence_groups
    
    async def evaluate_sequence(self, responses: List[Response], criteria_config: EvaluationCriteria) -> Optional[List[ResponseLLMEvaluation]]:
        """Evaluate a complete sequence of responses with full context for coherence assessment."""
        
        if not responses:
            return None
        
        try:
            # Build sequence evaluation prompt with all responses in context
            evaluation_prompt = self._build_sequence_evaluation_prompt(responses, criteria_config)
            
            # System prompt for the evaluator
            system_prompt_content = "You are an expert evaluator of creative writing sequences. Evaluate how well responses work together as a coherent narrative, with particular attention to how each response builds upon previous ones."
            # User prompt containing the actual sequence and criteria
            user_prompt_content = self._build_sequence_evaluation_prompt(responses, criteria_config)

            # Combine prompts. Specific formatting might be needed depending on the evaluator model.
            # For many models, prepending system prompt to user prompt is a common approach.
            full_prompt_for_evaluator = f"{system_prompt_content}\n\n{user_prompt_content}"
            
            # CRITICAL: Pre-evaluation context size validation for entire sequence
            try:
                context_analytics = self.evaluator.get_context_analytics(full_prompt_for_evaluator)
                logger.info(f"Sequence evaluation context validation: "
                           f"sequence={responses[0].sequence}, "
                           f"model={responses[0].model_name}, "
                           f"responses_count={len(responses)}, "
                           f"hash={context_analytics['prompt_hash']}, "
                           f"tokens={context_analytics['estimated_tokens']}/{context_analytics['max_tokens']}, "
                           f"utilization={context_analytics['utilization_percent']:.1f}%")
                
                if not context_analytics['fits']:
                    # This is critical - if sequence context exceeds limits, evaluation will fail
                    error_msg = (f"Sequence evaluation context exceeds limits: "
                               f"sequence={responses[0].sequence}, "
                               f"model={responses[0].model_name}, "
                               f"responses={len(responses)}, "
                               f"tokens={context_analytics['estimated_tokens']}/{context_analytics['max_tokens']}, "
                               f"hash={context_analytics['prompt_hash']}")
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                    
            except Exception as e:
                logger.error(f"Context validation failed for sequence evaluation: {e}")
                raise
            
            evaluator_call_settings = {
                "temperature": 0.3, # Consistent with original settings
                "max_tokens": 4096  # Consistent with original settings
            }

            # Call the generic evaluator
            eval_result_dict = await self.evaluator.generate_response(
                prompt=full_prompt_for_evaluator,  
                **evaluator_call_settings          
            )
        
            evaluation_text = eval_result_dict.get("text")  
            if not evaluation_text:
                logger.error(f"Evaluator {self.evaluator.name} did not return a response text for sequence evaluation.")
                # Consider how to handle this - perhaps raise an error or return None to skip this sequence.
                # For now, returning None as the original code did on other exceptions.
                return None
            
            # Parse the evaluation response for each response in the sequence
            sequence_evaluations = self._parse_sequence_evaluation_response(
                evaluation_text, responses, criteria_config
            )
            
            # Create and save evaluation documents
            saved_evaluations = []
            for response, criterion_evaluations in sequence_evaluations:
                llm_evaluation = ResponseLLMEvaluation(
                    response_id=response.id,
                    evaluating_llm_provider=self.evaluator_model_config.provider,
                    evaluating_llm_model=self.evaluator_model_config.name, # Or model_name if more specific
                    evaluation_criteria_id=criteria_config.id,
                    criteria_results=criterion_evaluations,
                    raw_evaluator_output=evaluation_text
                )
                
                saved_evaluation = await self.evaluation_repo.create(llm_evaluation)
                saved_evaluations.append(saved_evaluation)
                logger.info(f"Created sequence evaluation for response {response.id}")
            
            return saved_evaluations
            
        except Exception as e:
            logger.error(f"Error evaluating sequence: {str(e)}")
            return None

    async def get_evaluation_summary(self) -> Dict[str, Any]:
        """Calculate and return a summary of all evaluations in the database."""
        all_responses = await self.response_repo.find_many({})
        all_evaluations = await self.evaluation_repo.find_many({})

        total_responses_count = len(all_responses)
        total_evaluations_count = len(all_evaluations)

        evaluation_coverage = (total_evaluations_count / total_responses_count) if total_responses_count > 0 else 0

        # For model_sequence_statistics, we need to map evaluations back to responses to get model and sequence names
        # Create a lookup for responses by ID
        response_map: Dict[str, Response] = {str(r.id): r for r in all_responses}
        
        model_sequence_stats: Dict[Tuple[str, str], Dict[str, Any]] = {}

        active_criteria_config = await self.criteria_repo.find_active()
        criteria_names = list(active_criteria_config.criteria.keys()) if active_criteria_config else []

        for evaluation in all_evaluations:
            response = response_map.get(str(evaluation.response_id))
            if not response:
                logger.warning(f"Evaluation {evaluation.id} references a non-existent response {evaluation.response_id}. Skipping.")
                continue

            key = (response.model_name, response.sequence)
            if key not in model_sequence_stats:
                model_sequence_stats[key] = {
                    "model_name": response.model_name,
                    "sequence_name": response.sequence,
                    "count": 0, # Number of responses in this model/sequence group that have evaluations
                    "criteria_scores": {cn: {"total_score": 0, "count": 0, "average": 0.0} for cn in criteria_names}
                }
            
            model_sequence_stats[key]["count"] += 1
            for crit_eval in evaluation.criteria_results:
                if crit_eval.criterion_name in model_sequence_stats[key]["criteria_scores"]:
                    stat_entry = model_sequence_stats[key]["criteria_scores"][crit_eval.criterion_name]
                    stat_entry["total_score"] += crit_eval.score
                    stat_entry["count"] += 1
        
        # Calculate averages for criteria scores
        for stats in model_sequence_stats.values():
            for crit_name in stats["criteria_scores"]:
                entry = stats["criteria_scores"][crit_name]
                if entry["count"] > 0:
                    entry["average"] = entry["total_score"] / entry["count"]
                del entry["total_score"] # Clean up intermediate calculation field

        return {
            "total_responses": total_responses_count,
            "total_evaluations": total_evaluations_count,
            "evaluation_coverage": evaluation_coverage,
            "model_sequence_statistics": {f"{k[0]}_{k[1]}": v for k, v in model_sequence_stats.items()} # Flatten key for JSON
        }
    
    def _build_sequence_evaluation_prompt(self, responses: List[Response], criteria_config: EvaluationCriteria) -> str:
        """Build the sequence evaluation prompt that includes all responses in context."""
        
        # Build concise criteria descriptions
        criteria_list = []
        for criterion_name, criterion in criteria_config.criteria.items():
            criteria_list.append(f"• {criterion_name}: {criterion.description}")
        
        # Build the sequence context
        sequence_context = []
        for i, response in enumerate(responses):
            sequence_context.append(f"""
=== RESPONSE {i+1}: {response.prompt_name} ===
PROMPT: {response.prompt_text}

RESPONSE: {response.response}
""")
        
        model_name = responses[0].model_name
        sequence_name = responses[0].sequence
        
        prompt = f"""Evaluate this {len(responses)}-response creative writing sequence for coherence and quality.

MODEL: {model_name} | SEQUENCE: {sequence_name}

CRITICAL EVALUATION STANDARDS:
- Use the FULL 1-5 scale. Most responses should score 2-3 (competent work)
- Score 4 only for genuinely exceptional quality that exceeds professional standards
- Score 5 ONLY for masterwork-level writing that redefines expectations
- Be critical and realistic - even good AI responses have significant limitations
- Compare against published professional fiction, not just other AI writing

EVALUATION CRITERIA (1-5 scale):
{chr(10).join(criteria_list)}

SEQUENCE TO EVALUATE:
{chr(10).join(sequence_context)}

INSTRUCTIONS:
Evaluate each response individually AND as part of the sequence. Pay special attention to COHERENCE - how well each response builds upon and connects with previous responses. Be stringent in your evaluation - most AI writing has room for improvement.

OUTPUT FORMAT:
R1 EVALUATION:
creativity: [score] - [justification]
coherence: [score] - [justification focusing on internal consistency]
character_depth: [score] - [justification]
dialogue_quality: [score] - [justification]
visual_imagination: [score] - [justification]
conceptual_depth: [score] - [justification]
adaptability: [score] - [justification]

R2 EVALUATION:
creativity: [score] - [justification]
coherence: [score] - [justification focusing on how it builds on R1]
character_depth: [score] - [justification]
dialogue_quality: [score] - [justification]
visual_imagination: [score] - [justification]
conceptual_depth: [score] - [justification]
adaptability: [score] - [justification]

R3 EVALUATION:
creativity: [score] - [justification]
coherence: [score] - [justification focusing on sequence progression]
character_depth: [score] - [justification]
dialogue_quality: [score] - [justification]
visual_imagination: [score] - [justification]
conceptual_depth: [score] - [justification]
adaptability: [score] - [justification]"""
        
        return prompt
    
    def _parse_sequence_evaluation_response(self, evaluation_text: str, responses: List[Response], criteria_config: EvaluationCriteria) -> List[Tuple[Response, List[CriterionEvaluation]]]:
        """Parse the LLM's sequence evaluation response into structured data for each response."""
        
        sequence_evaluations = []
        lines = evaluation_text.strip().split('\n')
        
        current_response_index = None
        current_criterion = None
        current_score = None
        current_justification = ""
        current_evaluations = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line indicates a new response evaluation
            if "R" in line and "EVALUATION" in line.upper():
                # Save previous response evaluations if they exist
                if current_response_index is not None and current_evaluations:
                    if current_criterion and current_score is not None:
                        current_evaluations.append(CriterionEvaluation(
                            criterion_name=current_criterion,
                            score=current_score,
                            justification=current_justification.strip()
                        ))
                    
                    if current_response_index < len(responses):
                        sequence_evaluations.append((responses[current_response_index], current_evaluations))
                
                # Start new response evaluation
                try:
                    # Extract response number (1-based)
                    response_num = int(line.split()[0][1:])
                    current_response_index = response_num - 1  # Convert to 0-based
                except (ValueError, IndexError):
                    current_response_index = len(sequence_evaluations)  # Fallback
                
                current_evaluations = []
                current_criterion = None
                current_score = None
                current_justification = ""
                continue
            
            # Check if this line contains a criterion score
            for criterion_name in criteria_config.criteria.keys():
                if line.lower().startswith(criterion_name.lower() + ":"):
                    # Save previous criterion if exists
                    if current_criterion and current_score is not None:
                        current_evaluations.append(CriterionEvaluation(
                            criterion_name=current_criterion,
                            score=current_score,
                            justification=current_justification.strip()
                        ))
                    
                    # Start new criterion - parse score and justification from same line
                    current_criterion = criterion_name
                    try:
                        # Format: "criterion: score - justification"
                        content = line.split(':', 1)[1].strip()
                        if ' - ' in content:
                            score_part, justification_part = content.split(' - ', 1)
                            current_score = float(score_part.strip())
                            current_justification = justification_part.strip()
                        else:
                            current_score = float(content.strip())
                            current_justification = ""
                    except (ValueError, IndexError):
                        current_score = None
                        current_justification = ""
                    break
            else:
                # Continue building justification if we're in a criterion
                if current_criterion and line and not line.lower().startswith(tuple(c.lower() + ":" for c in criteria_config.criteria.keys())):
                    if current_justification:
                        current_justification += " " + line
                    else:
                        current_justification = line
        
        # Don't forget the last response and criterion
        if current_criterion and current_score is not None:
            current_evaluations.append(CriterionEvaluation(
                criterion_name=current_criterion,
                score=current_score,
                justification=current_justification.strip()
            ))
        
        if current_response_index is not None and current_evaluations and current_response_index < len(responses):
            sequence_evaluations.append((responses[current_response_index], current_evaluations))
        
        return sequence_evaluations
    
    async def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get a summary of all sequence evaluations."""
        
        all_evaluations = await self.evaluation_repo.find_many({})
        all_responses = await self.response_repo.find_many({})
        
        # Group evaluations by model and sequence
        model_sequence_stats = {}
        for evaluation in all_evaluations:
            # Find the corresponding response
            response = next((r for r in all_responses if r.id == evaluation.response_id), None)
            if not response:
                continue
                
            model_name = response.model_name
            sequence_name = response.sequence
            
            key = f"{model_name}_{sequence_name}"
            if key not in model_sequence_stats:
                model_sequence_stats[key] = {
                    "model_name": model_name,
                    "sequence_name": sequence_name,
                    "total_evaluations": 0,
                    "criteria_scores": {}
                }
            
            model_sequence_stats[key]["total_evaluations"] += 1
            
            # Aggregate scores by criteria
            for criterion_eval in evaluation.criteria_results:
                criterion_name = criterion_eval.criterion_name
                if criterion_name not in model_sequence_stats[key]["criteria_scores"]:
                    model_sequence_stats[key]["criteria_scores"][criterion_name] = []
                
                if criterion_eval.score is not None:
                    model_sequence_stats[key]["criteria_scores"][criterion_name].append(criterion_eval.score)
        
        # Calculate averages
        for key in model_sequence_stats:
            for criterion_name in model_sequence_stats[key]["criteria_scores"]:
                scores = model_sequence_stats[key]["criteria_scores"][criterion_name]
                if scores:
                    model_sequence_stats[key]["criteria_scores"][criterion_name] = {
                        "average": sum(scores) / len(scores),
                        "count": len(scores),
                        "scores": scores
                    }
        
        return {
            "total_evaluations": len(all_evaluations),
            "total_responses": len(all_responses),
            "evaluation_coverage": len(all_evaluations) / len(all_responses) if all_responses else 0,
            "model_sequence_statistics": model_sequence_stats
        }
