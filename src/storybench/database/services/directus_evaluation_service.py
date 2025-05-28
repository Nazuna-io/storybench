"""
Directus-integrated LLM Evaluation Service for processing creative writing responses.

This service fetches evaluation criteria from Directus CMS at runtime instead of 
using local files or MongoDB storage.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import AsyncOpenAI

from ...clients.directus_client import DirectusClient
from ...clients.directus_models import StorybenchEvaluationStructure
from ..repositories.response_repo import ResponseRepository
from ..repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository
from ..models import Response, ResponseLLMEvaluation, CriterionEvaluation

logger = logging.getLogger(__name__)

class DirectusEvaluationService:
    """Service for evaluating creative writing responses using LLM with Directus-sourced criteria."""
    
    def __init__(self, database: AsyncIOMotorDatabase, openai_api_key: str, directus_client: DirectusClient = None):
        self.database = database
        self.response_repo = ResponseRepository(database)
        self.evaluation_repo = ResponseLLMEvaluationRepository(database)
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.directus_client = directus_client or DirectusClient()
        
    async def get_evaluation_criteria(self, version_number: Optional[int] = None) -> StorybenchEvaluationStructure:
        """Fetch evaluation criteria from Directus."""
        if version_number:
            directus_version = await self.directus_client.get_evaluation_version_by_number(version_number)
        else:
            directus_version = await self.directus_client.get_latest_published_evaluation_version()
        
        if not directus_version:
            raise ValueError(f"No evaluation version found" + (f" for version {version_number}" if version_number else " (latest published)"))
        
        evaluation_structure = await self.directus_client.convert_to_storybench_evaluation_format(directus_version)
        logger.info(f"Loaded evaluation criteria version {evaluation_structure.version}: {evaluation_structure.version_name}")
        
        return evaluation_structure
        
    async def evaluate_all_responses(self, evaluation_version: Optional[int] = None) -> Dict[str, Any]:
        """Evaluate all responses in the database that haven't been evaluated yet."""
        
        # Get evaluation criteria from Directus
        evaluation_criteria = await self.get_evaluation_criteria(evaluation_version)
        logger.info(f"Using evaluation criteria: {evaluation_criteria.version_name} (v{evaluation_criteria.version})")
        
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
            "evaluation_version": evaluation_criteria.version,
            "evaluation_version_name": evaluation_criteria.version_name,
            "errors": []
        }
        
        for i, response in enumerate(unevaluated_responses):
            try:
                print(f" Evaluating response {i+1}/{len(unevaluated_responses)}: {response.model_name} - {response.sequence} - {response.prompt_name}", flush=True)
                
                evaluation = await self.evaluate_single_response(response, evaluation_criteria)
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
    
    async def evaluate_single_response(self, response: Response, evaluation_criteria: StorybenchEvaluationStructure) -> Optional[ResponseLLMEvaluation]:
        """Evaluate a single response using the LLM."""
        
        try:
            # Build evaluation prompt using Directus criteria
            evaluation_prompt = self._build_evaluation_prompt(response, evaluation_criteria)
            
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
            criterion_evaluations = self._parse_evaluation_response(evaluation_text, evaluation_criteria)
            
            # Create and save evaluation document
            llm_evaluation = ResponseLLMEvaluation(
                response_id=response.id,
                evaluating_llm_provider="openai",
                evaluating_llm_model="gpt-4",
                evaluation_criteria_id=f"directus_v{evaluation_criteria.version}",  # Reference to Directus version
                criteria_results=criterion_evaluations,
                raw_evaluator_output=evaluation_text
            )
            
            saved_evaluation = await self.evaluation_repo.create(llm_evaluation)
            logger.info(f"Created evaluation for response {response.id} using Directus criteria v{evaluation_criteria.version}")
            
            return saved_evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating response {response.id}: {str(e)}")
            return None
    
    def _build_evaluation_prompt(self, response: Response, evaluation_criteria: StorybenchEvaluationStructure) -> str:
        """Build the evaluation prompt for the LLM using Directus criteria."""
        
        # Build criteria descriptions
        criteria_text = ""
        for criterion_key, criterion in evaluation_criteria.criteria.items():
            criteria_text += f"\n{criterion.name}:\n{criterion.criteria}\nScale: {criterion.scale[0]}-{criterion.scale[1]}\n"
        
        # Get all responses in sequence for context
        sequence_responses = response.responses if hasattr(response, 'responses') and response.responses else [response.text]
        
        prompt = f"""Evaluate this {len(sequence_responses)}-response creative writing sequence for coherence and quality.

EVALUATION CRITERIA:
{criteria_text}

SCORING GUIDELINES:
{evaluation_criteria.scoring_guidelines}

SEQUENCE TO EVALUATE:
"""
        
        for i, resp_text in enumerate(sequence_responses, 1):
            prompt += f"\n--- Response {i} ---\n{resp_text}\n"
        
        prompt += f"""
RESPONSE METADATA:
- Model: {response.model_name}
- Sequence: {response.sequence}
- Prompt: {response.prompt_name}

Please provide your evaluation in this exact format:

CREATIVITY: [score 1-5]
[brief justification]

COHERENCE: [score 1-5]
[brief justification]

CHARACTER_DEPTH: [score 1-5]
[brief justification]

[Continue for all criteria...]

OVERALL ASSESSMENT:
[summary paragraph]
"""
        
        return prompt
    
    def _parse_evaluation_response(self, evaluation_text: str, evaluation_criteria: StorybenchEvaluationStructure) -> List[CriterionEvaluation]:
        """Parse the LLM evaluation response into structured criterion evaluations."""
        
        criterion_evaluations = []
        lines = evaluation_text.split('\n')
        
        current_criterion = None
        current_score = None
        current_justification = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this line starts a new criterion evaluation
            for criterion_key in evaluation_criteria.criteria.keys():
                criterion_name = criterion_key.upper()
                if line.startswith(f"{criterion_name}:"):
                    # Save previous criterion if exists
                    if current_criterion and current_score is not None:
                        criterion_evaluations.append(CriterionEvaluation(
                            criterion_name=current_criterion,
                            score=current_score,
                            justification="\n".join(current_justification).strip()
                        ))
                    
                    # Start new criterion
                    current_criterion = criterion_key
                    # Extract score from the line
                    try:
                        score_part = line.split(':')[1].strip()
                        current_score = int(score_part.split()[0])
                    except (IndexError, ValueError):
                        current_score = 3  # Default score if parsing fails
                    current_justification = []
                    break
            else:
                # This line is part of the current justification
                if current_criterion and line and not line.startswith("OVERALL"):
                    current_justification.append(line)
        
        # Save the last criterion
        if current_criterion and current_score is not None:
            criterion_evaluations.append(CriterionEvaluation(
                criterion_name=current_criterion,
                score=current_score,
                justification="\n".join(current_justification).strip()
            ))
        
        # Ensure we have evaluations for all criteria
        evaluated_criteria = {ce.criterion_name for ce in criterion_evaluations}
        for criterion_key in evaluation_criteria.criteria.keys():
            if criterion_key not in evaluated_criteria:
                criterion_evaluations.append(CriterionEvaluation(
                    criterion_name=criterion_key,
                    score=3,  # Default score
                    justification="Evaluation not found in response"
                ))
        
        return criterion_evaluations
    
    async def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary statistics of evaluations in the database."""
        
        all_evaluations = await self.evaluation_repo.find_many({})
        
        if not all_evaluations:
            return {"message": "No evaluations found"}
        
        # Group by evaluation criteria version
        by_criteria_version = {}
        for eval_doc in all_evaluations:
            criteria_id = eval_doc.evaluation_criteria_id
            if criteria_id not in by_criteria_version:
                by_criteria_version[criteria_id] = []
            by_criteria_version[criteria_id].append(eval_doc)
        
        summary = {
            "total_evaluations": len(all_evaluations),
            "by_criteria_version": {}
        }
        
        for criteria_id, evaluations in by_criteria_version.items():
            # Calculate averages by criterion
            criterion_scores = {}
            for evaluation in evaluations:
                for criterion_eval in evaluation.criteria_results:
                    criterion_name = criterion_eval.criterion_name
                    if criterion_name not in criterion_scores:
                        criterion_scores[criterion_name] = []
                    criterion_scores[criterion_name].append(criterion_eval.score)
            
            # Calculate averages
            criterion_averages = {}
            for criterion_name, scores in criterion_scores.items():
                criterion_averages[criterion_name] = sum(scores) / len(scores)
            
            summary["by_criteria_version"][criteria_id] = {
                "count": len(evaluations),
                "criterion_averages": criterion_averages
            }
        
        return summary
