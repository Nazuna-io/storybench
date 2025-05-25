"""
LLM Evaluation Service for processing creative writing responses.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import AsyncOpenAI

from ..repositories.response_repo import ResponseRepository
from ..repositories.criteria_repo import CriteriaRepository
from ..repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository
from ..models import Response, ResponseLLMEvaluation, CriterionEvaluation, EvaluationCriteria

logger = logging.getLogger(__name__)

class LLMEvaluationService:
    """Service for evaluating creative writing responses using LLM."""
    
    def __init__(self, database: AsyncIOMotorDatabase, openai_api_key: str):
        self.database = database
        self.response_repo = ResponseRepository(database)
        self.criteria_repo = CriteriaRepository(database)
        self.evaluation_repo = ResponseLLMEvaluationRepository(database)
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        
    async def evaluate_all_responses(self) -> Dict[str, Any]:
        """Evaluate all responses in the database that haven't been evaluated yet."""
        
        # Get active evaluation criteria
        criteria_config = await self.criteria_repo.find_active()
        if not criteria_config:
            raise ValueError("No active evaluation criteria found")
        
        # Get all responses
        all_responses = await self.response_repo.find_many({})
        logger.info(f"Found {len(all_responses)} total responses")
        
        # Filter out already evaluated responses
        unevaluated_responses = []
        for response in all_responses:
            existing_evals = await self.evaluation_repo.get_evaluations_by_response_id(response.id)
            if not existing_evals:
                unevaluated_responses.append(response)
        
        logger.info(f"Found {len(unevaluated_responses)} unevaluated responses")
        
        # Evaluate each response
        results = {
            "total_responses": len(all_responses),
            "unevaluated_responses": len(unevaluated_responses),
            "evaluations_created": 0,
            "errors": []
        }
        
        for i, response in enumerate(unevaluated_responses):
            try:
                print(f" Evaluating response {i+1}/{len(unevaluated_responses)}: {response.model_name} - {response.sequence} - {response.prompt_name}", flush=True)
                
                evaluation = await self.evaluate_single_response(response, criteria_config)
                if evaluation:
                    results["evaluations_created"] += 1
                    print(f" Success! Total completed: {results['evaluations_created']}", flush=True)
                else:
                    print(f" Failed to evaluate", flush=True)
                    
                # Add small delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Failed to evaluate response {response.id}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    async def evaluate_single_response(self, response: Response, criteria_config: EvaluationCriteria) -> Optional[ResponseLLMEvaluation]:
        """Evaluate a single response using the LLM."""
        
        try:
            # Build evaluation prompt
            evaluation_prompt = self._build_evaluation_prompt(response, criteria_config)
            
            # Call OpenAI API
            completion = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of creative writing. Provide detailed, objective assessments based on the given criteria."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            evaluation_text = completion.choices[0].message.content
            
            # Parse the evaluation response
            criterion_evaluations = self._parse_evaluation_response(evaluation_text, criteria_config)
            
            # Create and save evaluation document
            llm_evaluation = ResponseLLMEvaluation(
                response_id=response.id,
                evaluating_llm_provider="openai",
                evaluating_llm_model="gpt-4",
                evaluation_criteria_id=criteria_config.id,
                criteria_results=criterion_evaluations,
                raw_evaluator_output=evaluation_text
            )
            
            saved_evaluation = await self.evaluation_repo.create(llm_evaluation)
            logger.info(f"Created evaluation for response {response.id}")
            
            return saved_evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating response {response.id}: {str(e)}")
            return None
    
    def _build_evaluation_prompt(self, response: Response, criteria_config: EvaluationCriteria) -> str:
        """Build the evaluation prompt for the LLM."""
        
        criteria_descriptions = []
        for criterion_name, criterion in criteria_config.criteria.items():
            criteria_descriptions.append(
                f"**{criterion_name.upper()}** (Scale 1-{criterion.scale}): {criterion.description}"
            )
        
        prompt = f"""
Please evaluate the following creative writing response based on these criteria:

{chr(10).join(criteria_descriptions)}

**CONTEXT:**
- Model: {response.model_name}
- Sequence: {response.sequence}
- Prompt: {response.prompt_name}
- Prompt Text: {response.prompt_text}

**RESPONSE TO EVALUATE:**
{response.response}

**INSTRUCTIONS:**
For each criterion, provide:
1. A score from 1 to {list(criteria_config.criteria.values())[0].scale}
2. A detailed justification (2-3 sentences)

Format your response as:
CREATIVITY: [score]
Justification: [your justification]

COHERENCE: [score]
Justification: [your justification]

[Continue for all criteria...]

Be objective, specific, and constructive in your evaluations.
"""
        return prompt
    
    def _parse_evaluation_response(self, evaluation_text: str, criteria_config: EvaluationCriteria) -> List[CriterionEvaluation]:
        """Parse the LLM's evaluation response into structured data."""
        
        criterion_evaluations = []
        lines = evaluation_text.strip().split('\n')
        
        current_criterion = None
        current_score = None
        current_justification = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line contains a criterion score
            for criterion_name in criteria_config.criteria.keys():
                if line.upper().startswith(criterion_name.upper() + ":"):
                    # Save previous criterion if exists
                    if current_criterion and current_score is not None:
                        criterion_evaluations.append(CriterionEvaluation(
                            criterion_name=current_criterion,
                            score=current_score,
                            justification=current_justification.strip()
                        ))
                    
                    # Start new criterion
                    current_criterion = criterion_name
                    try:
                        score_part = line.split(':', 1)[1].strip()
                        current_score = float(score_part)
                    except (ValueError, IndexError):
                        current_score = None
                    current_justification = ""
                    break
            else:
                # Check if this is a justification line
                if line.lower().startswith("justification:"):
                    current_justification = line.split(':', 1)[1].strip()
                elif current_criterion and not line.upper().startswith(tuple(c.upper() + ":" for c in criteria_config.criteria.keys())):
                    # Continue building justification
                    if current_justification:
                        current_justification += " " + line
                    else:
                        current_justification = line
        
        # Don't forget the last criterion
        if current_criterion and current_score is not None:
            criterion_evaluations.append(CriterionEvaluation(
                criterion_name=current_criterion,
                score=current_score,
                justification=current_justification.strip()
            ))
        
        return criterion_evaluations
    
    async def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get a summary of all evaluations."""
        
        all_evaluations = await self.evaluation_repo.find_many({})
        all_responses = await self.response_repo.find_many({})
        
        # Group evaluations by model
        model_stats = {}
        for evaluation in all_evaluations:
            # Find the corresponding response
            response = next((r for r in all_responses if r.id == evaluation.response_id), None)
            if not response:
                continue
                
            model_name = response.model_name
            if model_name not in model_stats:
                model_stats[model_name] = {
                    "total_evaluations": 0,
                    "criteria_scores": {}
                }
            
            model_stats[model_name]["total_evaluations"] += 1
            
            # Aggregate scores by criteria
            for criterion_eval in evaluation.criteria_results:
                criterion_name = criterion_eval.criterion_name
                if criterion_name not in model_stats[model_name]["criteria_scores"]:
                    model_stats[model_name]["criteria_scores"][criterion_name] = []
                
                if criterion_eval.score is not None:
                    model_stats[model_name]["criteria_scores"][criterion_name].append(criterion_eval.score)
        
        # Calculate averages
        for model_name in model_stats:
            for criterion_name in model_stats[model_name]["criteria_scores"]:
                scores = model_stats[model_name]["criteria_scores"][criterion_name]
                if scores:
                    model_stats[model_name]["criteria_scores"][criterion_name] = {
                        "average": sum(scores) / len(scores),
                        "count": len(scores),
                        "scores": scores
                    }
        
        return {
            "total_evaluations": len(all_evaluations),
            "total_responses": len(all_responses),
            "evaluation_coverage": len(all_evaluations) / len(all_responses) if all_responses else 0,
            "model_statistics": model_stats
        }
