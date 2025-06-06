#!/usr/bin/env python3
"""
Automated StoryBench Evaluation Runner
Runs evaluation pipeline with resume/skip capabilities using YAML configuration
"""

import os
import sys
import asyncio
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from dotenv import load_dotenv
import logging
from dataclasses import dataclass, asdict
import json

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.clients.directus_client import DirectusClient
from storybench.database.connection import DatabaseConnection
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator
from storybench.evaluators.api_evaluator_adapter import APIEvaluatorAdapter
from storybench.models.directus_models import (
    StorybenchPromptSequences,
    StorybenchEvaluationStructure,
    CriterionEvaluation
)
from storybench.models.response import Response, ResponseLLMEvaluation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationProgress:
    """Track evaluation progress for reporting."""
    total_models: int = 0
    completed_models: int = 0
    skipped_models: int = 0
    failed_models: int = 0
    current_model: Optional[str] = None
    current_sequence: Optional[str] = None
    current_prompt: Optional[str] = None
    current_run: Optional[int] = None
    total_cost: float = 0.0
    model_costs: Dict[str, float] = None
    
    def __post_init__(self):
        if self.model_costs is None:
            self.model_costs = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return asdict(self)


class AutomatedEvaluationRunner:
    """Automated evaluation pipeline with configuration-based model management."""
    
    def __init__(self, config_path: str = "config/models.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.api_keys = self._load_api_keys()
        self.db_connection = None
        self.directus_client = None
        self.database = None
        self.progress = EvaluationProgress()
        self.openai_client = None
        
    def _load_config(self) -> Dict:
        """Load YAML configuration."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment."""
        return {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "gemini": os.getenv("GOOGLE_API_KEY"),
            "deepinfra": os.getenv("DEEPINFRA_API_KEY"),
        }
    
    async def setup_connections(self):
        """Setup database and Directus connections."""
        # Database connection
        self.db_connection = DatabaseConnection()
        self.database = await self.db_connection.connect(
            connection_string=os.getenv("MONGODB_URI"),
            database_name="storybench"
        )
        
        # Directus client
        self.directus_client = DirectusClient(
            url=os.getenv("DIRECTUS_URL"),
            token=os.getenv("DIRECTUS_TOKEN")
        )
        
        # OpenAI client for evaluations
        if self.api_keys.get("openai"):
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(api_key=self.api_keys["openai"])
        
        logger.info("✅ Connections established")
    
    async def get_completed_evaluations(self, prompt_version: str, criteria_version: str) -> Set[str]:
        """Get models that have completed evaluation for current versions."""
        responses_collection = self.database[self.config['storage']['responses_collection']]
        evaluations_collection = self.database[self.config['storage']['evaluations_collection']]
        
        # Find models with complete response sets
        response_pipeline = [
            {
                "$match": {
                    "prompt_version": prompt_version,
                }
            },
            {
                "$group": {
                    "_id": {
                        "model_name": "$model_name",
                        "sequence_name": "$sequence_name",
                        "prompt_name": "$prompt_name"
                    },
                    "runs": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.model_name",
                    "sequences_completed": {"$sum": 1},
                    "total_runs": {"$sum": "$runs"}
                }
            }
        ]        
        # Find models with evaluations
        eval_pipeline = [
            {
                "$match": {
                    "evaluation_criteria_id": f"directus_v{criteria_version}",
                }
            },
            {
                "$group": {
                    "_id": "$model_name",
                    "evaluations_count": {"$sum": 1}
                }
            }
        ]
        
        completed_responses = {}
        async for doc in responses_collection.aggregate(response_pipeline):
            completed_responses[doc['_id']] = {
                'sequences_completed': doc['sequences_completed'],
                'total_runs': doc['total_runs']
            }
        
        completed_evaluations = {}
        async for doc in evaluations_collection.aggregate(eval_pipeline):
            completed_evaluations[doc['_id']] = doc['evaluations_count']
        
        # A model is complete if it has all responses AND evaluations
        completed = set()
        expected_sequences = 5  # Based on config or dynamic
        expected_prompts_per_sequence = 3
        expected_runs = self.config['pipeline']['runs_per_sequence']
        expected_total = expected_sequences * expected_prompts_per_sequence * expected_runs
        
        for model_name, response_data in completed_responses.items():
            if (response_data['total_runs'] >= expected_total and 
                model_name in completed_evaluations and
                completed_evaluations[model_name] > 0):
                completed.add(model_name)
                logger.info(f"Model {model_name} has complete data for v{prompt_version}/v{criteria_version}")
        
        return completed    
    async def create_evaluator(self, provider: str, model_config: Dict) -> Optional[LiteLLMEvaluator]:
        """Create evaluator for a model."""
        try:
            # Use adapter for backwards compatibility
            evaluator = APIEvaluatorAdapter(
                name=model_config['name'],
                provider=provider,
                model_id=model_config['model_id'],
                context_size=model_config.get('max_tokens', 32768),
                temperature=self.config['evaluation']['temperature_generation'],
                api_keys=self.api_keys
            )
            
            # Test setup
            if await evaluator.setup():
                return evaluator
            else:
                logger.error(f"Failed to setup {provider}/{model_config['model_id']}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating evaluator for {provider}/{model_config['model_id']}: {str(e)}")
            return None
    
    def _build_evaluation_prompt(self, responses: List[Dict], evaluation_criteria: StorybenchEvaluationStructure) -> str:
        """Build the evaluation prompt for the LLM using Directus criteria."""
        
        # Build criteria descriptions
        criteria_text = ""
        for criterion_key, criterion in evaluation_criteria.criteria.items():
            criteria_text += f"\n{criterion.name}:\n{criterion.criteria}\nScale: {criterion.scale[0]}-{criterion.scale[1]}\n"
        
        prompt = f"""Evaluate this {len(responses)}-response creative writing sequence for coherence and quality.

EVALUATION CRITERIA:
{criteria_text}

SCORING GUIDELINES:
{evaluation_criteria.scoring_guidelines}

SEQUENCE TO EVALUATE:
"""        
        for i, resp in enumerate(responses, 1):
            prompt += f"\n--- Response {i} ---\n{resp['response']}\n"
        
        prompt += f"""
RESPONSE METADATA:
- Model: {responses[0]['model_name']}
- Sequence: {responses[0]['sequence_name']}

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
    
    async def evaluate_sequence(self, sequence_responses: List[Dict], eval_criteria: StorybenchEvaluationStructure) -> Optional[Dict]:
        """Evaluate a complete sequence of responses."""
        if not self.openai_client:
            logger.error("OpenAI client not initialized for evaluations")
            return None
        
        try:
            # Build evaluation prompt
            evaluation_prompt = self._build_evaluation_prompt(sequence_responses, eval_criteria)
            
            # Call OpenAI API for evaluation
            completion = await self.openai_client.chat.completions.create(
                model=self.config['evaluation']['evaluator_model'],
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert evaluator of creative writing. Provide detailed, objective assessments based on the given criteria."
                    },
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=self.config['evaluation']['temperature_evaluation'],
                max_tokens=2000
            )            
            evaluation_text = completion.choices[0].message.content
            
            # Track evaluation cost
            if hasattr(completion, 'usage'):
                # Rough cost estimation (adjust based on actual pricing)
                cost = (completion.usage.prompt_tokens * 0.01 + completion.usage.completion_tokens * 0.03) / 1000
                self.progress.total_cost += cost
            
            # Parse the evaluation response
            criterion_evaluations = self._parse_evaluation_response(evaluation_text, eval_criteria)
            
            return {
                "raw_output": evaluation_text,
                "criteria_results": criterion_evaluations,
                "evaluator_model": self.config['evaluation']['evaluator_model']
            }
            
        except Exception as e:
            logger.error(f"Error evaluating sequence: {str(e)}")
            return None    
    async def run_model_evaluation(self, evaluator, model_info: Dict, prompts: StorybenchPromptSequences, eval_criteria: StorybenchEvaluationStructure):
        """Run evaluation for a single model."""
        provider = model_info['provider']
        model_name = model_info['model_config']['name']
        model_id = model_info['model_config']['model_id']
        
        logger.info(f"\n🤖 Evaluating {provider}/{model_id}")
        logger.info("=" * 60)
        
        # Update progress
        self.progress.current_model = f"{provider}/{model_id}"
        
        responses_collection = self.database[self.config['storage']['responses_collection']]
        evaluations_collection = self.database[self.config['storage']['evaluations_collection']]
        
        total_sequences = len(prompts.sequences)
        runs_per_sequence = self.config['pipeline']['runs_per_sequence']
        model_cost = 0.0
        
        for sequence_idx, (sequence_name, sequence_prompts) in enumerate(prompts.sequences.items(), 1):
            logger.info(f"\n📝 Sequence {sequence_idx}/{total_sequences}: {sequence_name}")
            self.progress.current_sequence = sequence_name
            
            for run in range(1, runs_per_sequence + 1):
                logger.info(f"   🔄 Run {run}/{runs_per_sequence}")
                self.progress.current_run = run
                
                # Reset context between sequences as configured
                if self.config['pipeline']['reset_context_between_sequences']:
                    evaluator.reset_context()
                
                # Process prompts in sequence
                sequence_responses = []                
                for prompt_idx, prompt in enumerate(sequence_prompts, 1):
                    self.progress.current_prompt = prompt['name']
                    
                    # Generate response
                    response_data = await evaluator.generate_response(
                        prompt=prompt['text'],
                        temperature=self.config['evaluation']['temperature_generation'],
                        max_tokens=8192
                    )
                    
                    # Track generation cost
                    if 'usage' in response_data and 'total_cost' in response_data['usage']:
                        cost = response_data['usage']['total_cost']
                        model_cost += cost
                        self.progress.total_cost += cost
                    
                    # Store response
                    response_doc = {
                        "model_name": model_name,
                        "provider": provider,
                        "model_id": model_id,
                        "sequence_name": sequence_name,
                        "prompt_name": prompt['name'],
                        "prompt_text": prompt['text'],
                        "prompt_version": prompts.version,
                        "run": run,
                        "response": response_data['response'],
                        "metadata": response_data.get('usage', {}),
                        "context_info": response_data.get('context_info', {}),
                        "timestamp": datetime.utcnow()
                    }
                    
                    result = await responses_collection.insert_one(response_doc)
                    response_doc['_id'] = result.inserted_id
                    sequence_responses.append(response_doc)                
                # Evaluate the complete sequence
                logger.info(f"   📊 Evaluating sequence...")
                evaluation_result = await self.evaluate_sequence(sequence_responses, eval_criteria)
                
                if evaluation_result:
                    # Create evaluation document
                    evaluation_doc = {
                        "model_name": model_name,
                        "model_id": model_id,
                        "provider": provider,
                        "sequence_name": sequence_name,
                        "run": run,
                        "response_ids": [r['_id'] for r in sequence_responses],
                        "evaluating_llm_provider": "openai",
                        "evaluating_llm_model": evaluation_result['evaluator_model'],
                        "evaluation_criteria_id": f"directus_v{eval_criteria.version}",
                        "criteria_results": [asdict(cr) for cr in evaluation_result['criteria_results']],
                        "raw_evaluator_output": evaluation_result['raw_output'],
                        "timestamp": datetime.utcnow()
                    }
                    
                    await evaluations_collection.insert_one(evaluation_doc)
                    logger.info(f"   ✅ Evaluation saved")
                else:
                    logger.error(f"   ❌ Evaluation failed")
        
        # Update model cost tracking
        self.progress.model_costs[f"{provider}/{model_id}"] = model_cost
        logger.info(f"\n✅ Completed evaluation for {provider}/{model_id} (Cost: ${model_cost:.4f})")
    
    async def save_progress(self):
        """Save current progress to a file for monitoring."""
        progress_file = Path("evaluation_progress.json")
        with open(progress_file, 'w') as f:
            json.dump(self.progress.to_dict(), f, indent=2)    
    async def run_pipeline(self, resume: bool = True, force_rerun: List[str] = None):
        """Run the complete evaluation pipeline."""
        logger.info("\n🚀 StoryBench Automated Evaluation Pipeline")
        logger.info("=" * 60)
        
        # Setup connections
        await self.setup_connections()
        
        # Get current versions from Directus
        prompts = await self.directus_client.get_prompt_sequences()
        eval_criteria = await self.directus_client.get_evaluation_criteria()
        
        prompt_version = prompts.version
        criteria_version = eval_criteria.version
        
        logger.info(f"📋 Prompt version: {prompt_version}")
        logger.info(f"📋 Criteria version: {criteria_version}")
        
        # Get completed evaluations if resuming
        if resume:
            completed = await self.get_completed_evaluations(prompt_version, criteria_version)
            logger.info(f"✅ Found {len(completed)} completed model evaluations")
        else:
            completed = set()
            logger.info("🔄 Starting fresh (no resume)")
        
        # Process each provider's models
        enabled_models = []
        for provider, models in self.config['models'].items():
            for model_config in models:
                if model_config.get('enabled', True):
                    model_name = model_config['name']
                    enabled_models.append({
                        'provider': provider,
                        'model_config': model_config,
                        'model_name': model_name
                    })
        
        logger.info(f"\n📊 Found {len(enabled_models)} enabled models")
        self.progress.total_models = len(enabled_models)        
        # Run evaluations
        successful = 0
        failed = 0
        skipped = 0
        
        for idx, model_info in enumerate(enabled_models, 1):
            model_name = model_info['model_name']
            
            # Check if should skip
            if model_name in completed and model_name not in (force_rerun or []):
                logger.info(f"\n⏭️  [{idx}/{len(enabled_models)}] Skipping completed: {model_name}")
                skipped += 1
                self.progress.skipped_models += 1
                continue
            
            logger.info(f"\n🔄 [{idx}/{len(enabled_models)}] Processing: {model_name}")
            
            # Create evaluator
            evaluator = await self.create_evaluator(
                model_info['provider'],
                model_info['model_config']
            )
            
            if not evaluator:
                failed += 1
                self.progress.failed_models += 1
                continue
            
            try:
                # Run evaluation
                await self.run_model_evaluation(evaluator, model_info, prompts, eval_criteria)
                successful += 1
                self.progress.completed_models += 1
                
                # Save progress after each model
                await self.save_progress()
                
            except Exception as e:
                logger.error(f"❌ Error during evaluation: {str(e)}")
                failed += 1
                self.progress.failed_models += 1
                
            finally:
                await evaluator.cleanup()        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"⏭️  Skipped: {skipped}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📊 Total: {len(enabled_models)}")
        logger.info(f"💰 Total Cost: ${self.progress.total_cost:.4f}")
        
        # Save final progress
        await self.save_progress()
        
        # Cleanup
        if self.db_connection:
            await self.db_connection.close()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run StoryBench evaluation pipeline with automated model management'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/models.yaml',
        help='Path to models configuration file'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Start fresh, ignore completed evaluations'
    )
    parser.add_argument(
        '--rerun',
        type=str,
        help='Force rerun specific models (comma-separated model names)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be run without executing'
    )    
    args = parser.parse_args()
    
    # Parse rerun list
    force_rerun = args.rerun.split(',') if args.rerun else None
    
    # Create and run pipeline
    runner = AutomatedEvaluationRunner(config_path=args.config)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No evaluations will be executed")
        # Just show config and exit
        config = runner._load_config()
        logger.info(f"\n📋 Configuration: {args.config}")
        logger.info(f"📊 Enabled models:")
        for provider, models in config['models'].items():
            enabled = [m for m in models if m.get('enabled', True)]
            if enabled:
                logger.info(f"  {provider}: {len(enabled)} models")
                for model in enabled:
                    logger.info(f"    - {model['name']}")
        return
    
    # Run the pipeline
    await runner.run_pipeline(
        resume=not args.no_resume,
        force_rerun=force_rerun
    )


if __name__ == "__main__":
    asyncio.run(main())