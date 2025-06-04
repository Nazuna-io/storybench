#!/usr/bin/env python3
"""
StoryBench Parallel Pipeline Runner

Integrates Phase 2.0 parallel execution with the existing Directus-based
evaluation pipeline for maximum performance.

Usage:
    python run_parallel_pipeline.py [--models model1,model2] [--max-concurrent 5]
"""

import os
import sys
import asyncio
import argparse
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.clients.directus_client import DirectusClient
from storybench.database.connection import init_database
from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner
from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator
from storybench.evaluators.api_evaluator import APIEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParallelPipelineRunner:
    """Integrated parallel pipeline with Directus and MongoDB."""
    
    def __init__(self, config_path: str = "config/models.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.api_keys = self._load_api_keys()
        self.database = None
        self.directus_client = None
        self.evaluation_runner = None
        
    def _load_config(self) -> Dict:
        """Load YAML configuration."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment."""
        return {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            "deepinfra": os.getenv("DEEPINFRA_API_KEY"),
        }
    
    async def setup_connections(self):
        """Setup database and Directus connections."""
        logger.info("🔌 Setting up connections...")
        
        # Database connection
        self.database = await init_database()
        logger.info("✅ Database connected")
        
        # Directus client
        directus_url = os.getenv("DIRECTUS_URL")
        directus_token = os.getenv("DIRECTUS_TOKEN")
        
        if directus_url and directus_token:
            self.directus_client = DirectusClient(base_url=directus_url, token=directus_token)
            logger.info("✅ Directus connected")
        else:
            logger.warning("⚠️  Directus credentials not found - using local prompts")
            self.directus_client = None
        
        # Initialize parallel evaluation runner
        self.evaluation_runner = DatabaseEvaluationRunner(
            database=self.database, 
            enable_parallel=True
        )
        logger.info("✅ Parallel evaluation runner initialized")
    
    async def get_prompts_and_sequences(self) -> Dict:
        """Get prompts from Directus or local config."""
        if self.directus_client:
            try:
                logger.info("📋 Fetching prompts from Directus...")
                directus_prompts = await self.directus_client.fetch_prompts()
                
                if directus_prompts:
                    # Convert Directus format to local format
                    sequences = {}
                    for sequence_name, prompts in directus_prompts.sequences.items():
                        sequences[sequence_name] = [
                            {"name": prompt.name, "text": prompt.text}
                            for prompt in prompts
                        ]
                    
                    logger.info(f"✅ Loaded {len(sequences)} sequences from Directus v{directus_prompts.version}")
                    return sequences
                else:
                    logger.warning("⚠️  No prompts found in Directus, falling back to local")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to fetch from Directus: {e}")
                logger.info("📋 Falling back to local prompts...")
        
        # Fallback to local prompts
        prompts_path = "config/prompts.json"
        with open(prompts_path, 'r') as f:
            sequences = json.load(f)
        
        logger.info(f"✅ Loaded {len(sequences)} sequences from local config")
        return sequences
    
    def create_evaluator_factory(self):
        """Create evaluator factory for parallel execution."""
        def evaluator_factory(model_config):
            provider = model_config.get("provider", "unknown")
            model_id = model_config["model_id"]
            
            # Get appropriate API key
            if provider == "openai":
                api_key = self.api_keys["openai"]
            elif provider == "anthropic":
                api_key = self.api_keys["anthropic"]
            elif provider == "google":
                api_key = self.api_keys["google"]
            elif provider == "deepinfra":
                api_key = self.api_keys["deepinfra"]
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            if not api_key:
                raise ValueError(f"Missing API key for provider: {provider}")
            
            # Create configuration for APIEvaluator
            evaluator_config = {
                "provider": provider,
                "model_name": model_id,
                "max_tokens": model_config.get("max_tokens", 32768),
                "temperature": 1.0
            }
            
            # Prepare API keys dict
            api_keys_dict = {provider: api_key}
            
            # Create APIEvaluator with correct signature
            try:
                return APIEvaluator(
                    name=f"{provider}_{model_config['name']}",
                    config=evaluator_config,
                    api_keys=api_keys_dict
                )
            except Exception as e:
                logger.error(f"Failed to create evaluator for {model_config['name']}: {e}")
                raise
        
        return evaluator_factory    
    async def run_parallel_pipeline(self, 
                                  selected_models: Optional[List[str]] = None,
                                  max_concurrent: int = 5,
                                  num_runs: int = 3) -> Dict:
        """Run the complete parallel evaluation pipeline."""
        
        logger.info("\n🚀 StoryBench Parallel Pipeline")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Setup connections
            await self.setup_connections()
            
            # Get prompts and sequences
            sequences = await self.get_prompts_and_sequences()
            
            # Get enabled models
            all_models = []
            for provider, models in self.config['models'].items():
                for model_config in models:
                    if model_config.get('enabled', True):
                        model_config['provider'] = provider
                        all_models.append(model_config)
            
            # Filter models if specified
            if selected_models:
                all_models = [m for m in all_models if m['name'] in selected_models]
            
            # Validate API keys for selected models
            self._validate_api_keys(all_models)
            
            logger.info(f"\n📊 Pipeline Configuration:")
            logger.info(f"   Models: {len(all_models)}")
            logger.info(f"   Sequences: {len(sequences)}")
            logger.info(f"   Runs per sequence: {num_runs}")
            logger.info(f"   Max concurrent sequences: {max_concurrent}")
            
            total_api_calls = len(all_models) * len(sequences) * 3 * num_runs
            logger.info(f"   Total API calls: {total_api_calls}")
            logger.info(f"   Expected speedup: ~{len(sequences)}x via parallel sequences")
            
            # Update parallel runner concurrency
            self.evaluation_runner.parallel_runner.max_concurrent_sequences = max_concurrent
            
            # Start evaluation
            logger.info(f"\n🚀 Starting parallel evaluation...")
            evaluation = await self.evaluation_runner.start_evaluation(
                models=[m['name'] for m in all_models],
                sequences=sequences,
                criteria={"pipeline_version": "parallel_v2.0"},
                global_settings={"num_runs": num_runs}
            )
            
            evaluation_id = str(evaluation.id)
            logger.info(f"📋 Evaluation ID: {evaluation_id}")
            
            # Create evaluator factory
            evaluator_factory = self.create_evaluator_factory()
            
            # Run parallel evaluation
            results = await self.evaluation_runner.run_parallel_evaluation(
                evaluation_id=evaluation_id,
                models=all_models,
                sequences=sequences,
                num_runs=num_runs,
                evaluator_factory=evaluator_factory
            )
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # Results summary
            logger.info("\n" + "=" * 60)
            logger.info("🎉 PARALLEL PIPELINE COMPLETE")
            logger.info("=" * 60)
            
            if results.get('success', False):
                logger.info(f"✅ Pipeline completed successfully!")
                logger.info(f"⏱️  Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
                logger.info(f"👥 Workers: {results['successful_workers']}/{results['total_workers']} successful")
                logger.info(f"💾 MongoDB: All responses saved to evaluation {evaluation_id}")
                
                if 'performance_metrics' in results:
                    metrics = results['performance_metrics']
                    throughput = metrics.get('average_throughput_per_minute', 0)
                    speedup = metrics.get('parallelization_speedup', 0)
                    
                    logger.info(f"📊 Throughput: {throughput:.1f} prompts/minute")
                    if speedup > 0:
                        logger.info(f"🚀 Speedup: {speedup:.1f}x vs sequential execution")
                
                # Provider performance
                if 'provider_stats' in results:
                    logger.info(f"\n📈 Provider Performance:")
                    for provider, stats in results['provider_stats'].items():
                        utilization = stats.get('utilization_percent', 0)
                        if utilization > 0:
                            logger.info(f"   {provider}: {utilization:.1f}% average utilization")
                
                return {
                    "success": True,
                    "evaluation_id": evaluation_id,
                    "duration_minutes": total_duration / 60,
                    "total_models": len(all_models),
                    "total_sequences": len(sequences),
                    "total_api_calls": total_api_calls,
                    "successful_workers": results['successful_workers'],
                    "failed_workers": results['failed_workers'],
                    "performance_metrics": results.get('performance_metrics', {})
                }
            else:
                logger.error(f"❌ Pipeline failed: {results.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": results.get('error', 'Unknown error'),
                    "evaluation_id": evaluation_id
                }
                
        except Exception as e:
            logger.error(f"❌ Pipeline failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_api_keys(self, models: List[Dict]):
        """Validate required API keys are present."""
        missing_keys = []
        for model in models:
            provider = model['provider']
            
            if provider == "openai" and not self.api_keys["openai"]:
                missing_keys.append("OPENAI_API_KEY")
            elif provider == "anthropic" and not self.api_keys["anthropic"]:
                missing_keys.append("ANTHROPIC_API_KEY")
            elif provider == "google" and not self.api_keys["google"]:
                missing_keys.append("GOOGLE_API_KEY")
            elif provider == "deepinfra" and not self.api_keys["deepinfra"]:
                missing_keys.append("DEEPINFRA_API_KEY")
        
        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(set(missing_keys))}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="StoryBench Parallel Pipeline Runner")
    parser.add_argument('--models', help='Comma-separated list of specific models to run')
    parser.add_argument('--config', default='config/models.yaml', help='Path to models config')
    parser.add_argument('--max-concurrent', type=int, default=5, help='Max concurrent sequences')
    parser.add_argument('--runs', type=int, default=3, help='Number of runs per sequence')
    parser.add_argument('--dry-run', action='store_true', help='Validate config without running')
    
    args = parser.parse_args()
    
    # Parse selected models
    selected_models = None
    if args.models:
        selected_models = [m.strip() for m in args.models.split(',')]
    
    # Initialize runner
    runner = ParallelPipelineRunner(config_path=args.config)
    
    if args.dry_run:
        print("🔍 Dry run - validating configuration...")
        try:
            await runner.setup_connections()
            sequences = await runner.get_prompts_and_sequences()
            
            # Get models
            all_models = []
            for provider, models in runner.config['models'].items():
                for model_config in models:
                    if model_config.get('enabled', True):
                        model_config['provider'] = provider
                        all_models.append(model_config)
            
            if selected_models:
                all_models = [m for m in all_models if m['name'] in selected_models]
            
            runner._validate_api_keys(all_models)
            
            total_calls = len(all_models) * len(sequences) * 3 * args.runs
            print(f"✅ Configuration valid!")
            print(f"   Models: {len(all_models)}")
            print(f"   Sequences: {len(sequences)}")
            print(f"   Total API calls: {total_calls}")
            print(f"   Estimated speedup: ~{len(sequences)}x")
            
        except Exception as e:
            print(f"❌ Configuration error: {e}")
        return
    
    # Run the pipeline
    results = await runner.run_parallel_pipeline(
        selected_models=selected_models,
        max_concurrent=args.max_concurrent,
        num_runs=args.runs
    )
    
    if results['success']:
        print(f"\n🎉 SUCCESS! Evaluation ID: {results['evaluation_id']}")
        print(f"Duration: {results['duration_minutes']:.1f} minutes")
    else:
        print(f"\n💥 FAILED: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
