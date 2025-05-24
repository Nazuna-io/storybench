#!/usr/bin/env python3
# API-based model evaluation script with multiple trials per prompt
# For evaluating proprietary LLMs via their APIs

import os
import json
import time
import argparse
import logging
from datetime import datetime
import random
import asyncio
import aiohttp
import backoff
from tqdm.asyncio import tqdm_asyncio

# API clients
from openai import OpenAI, AsyncOpenAI
from anthropic import Anthropic
import google.generativeai as genai

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("api_evaluation.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_prompts(prompts_file):
    """Load the prompt sequences from a JSON file"""
    with open(prompts_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_variant_prompt(base_prompt, run_index):
    """Create a variant prompt for multiple runs"""
    variant_additions = [
        "For this response, explore a completely different direction than you might normally take. Be original and surprising in your approach.",
        "Think outside conventional narratives for this response. Create something unique that demonstrates creative thinking and fresh ideas.",
        "For your third approach to this prompt, push boundaries with innovative concepts and perspectives unlike typical responses."
    ]
    
    return f"{base_prompt}\n\n{variant_additions[run_index % len(variant_additions)]}"

def format_prompt(prompt_text, conversation_history=None):
    """Format the prompt based on conversation history"""
    if conversation_history:
        return f"{conversation_history}\n\nHuman: {prompt_text}\n\nAssistant:"
    else:
        return f"Human: {prompt_text}\n\nAssistant:"

def create_model_directory(base_dir, model_name):
    """Create directory for model outputs"""
    model_dir = os.path.join(base_dir, model_name)
    os.makedirs(model_dir, exist_ok=True)
    return model_dir

# === API CLIENT FUNCTIONS ===

class APIEvaluator:
    """Base class for API evaluation"""
    def __init__(self, api_key, model_name, base_url=None):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.client = None
        self.setup_client()
    
    def setup_client(self):
        pass
    
    async def generate_response(self, prompt, temperature=0.9, max_tokens=4096):
        pass

class OpenAIEvaluator(APIEvaluator):
    """Evaluator for OpenAI-compatible APIs (OpenAI, Grok)"""
    def setup_client(self):
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def generate_response(self, prompt, temperature=0.9, max_tokens=4096):
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=["Human:", "\nHuman:"]
            )
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "completion_tokens": response.usage.completion_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class AnthropicEvaluator(APIEvaluator):
    """Evaluator for Anthropic Claude models"""
    def setup_client(self):
        self.client = Anthropic(api_key=self.api_key)
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def generate_response(self, prompt, temperature=0.9, max_tokens=4096):
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop_sequences=["Human:", "\nHuman:"]
            )
            return {
                "text": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

class GeminiEvaluator(APIEvaluator):
    """Evaluator for Google Gemini models"""
    def setup_client(self):
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_name)
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def generate_response(self, prompt, temperature=0.9, max_tokens=4096):
        try:
            response = await asyncio.to_thread(
                self.client.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    stop_sequences=["Human:", "\nHuman:"]
                )
            )
            return {
                "text": response.text,
                "usage": {}  # Google doesn't provide token counts in the same way
            }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

class QwenEvaluator(APIEvaluator):
    """Evaluator for Qwen models via OpenAI-compatible API"""
    def setup_client(self):
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def generate_response(self, prompt, temperature=0.9, max_tokens=4096):
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=["Human:", "\nHuman:"]
            )
            
            # Debug information
            logger.info(f"Qwen response type: {type(response)}")
            
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "completion_tokens": response.usage.completion_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Qwen API error: {e}")
            # Log more detailed error information
            import traceback
            logger.error(traceback.format_exc())
            raise

class AI21Evaluator(APIEvaluator):
    """Evaluator for AI21 Jamba models"""
    def setup_client(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # Map common display names to API model names from the allowed list
        model_mapping = {
            "Jamba 1.5 Instruct": "jamba-instruct",
            "jamba 1.5 instruct": "jamba-instruct",
            "jamba-1.5-instruct": "jamba-instruct",  # Add this specific mapping
            "Jamba1.5Instruct": "jamba-instruct",
            "Jamba 1.5 Large": "jamba-large-1.5",
            "Jamba 1.5 Mini": "jamba-mini-1.5",
            "Jamba 1.6 Large": "jamba-large-1.6",
            "Jamba 1.6 Mini": "jamba-mini-1.6",
        }
        
        # Use the mapped model name if available, otherwise keep the original
        self.api_model_name = model_mapping.get(self.model_name, self.model_name)
        logger.info(f"Using AI21 model: {self.api_model_name} (from: {self.model_name})")
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def generate_response(self, prompt, temperature=0.9, max_tokens=4096):
        try:
            # Direct API call using the documented format
            payload = {
                "model": self.api_model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "system": "You are a helpful assistant.",
                "temperature": temperature,
                "maxTokens": max_tokens
            }
            
            # Make direct API call
            async with self.session.post("https://api.ai21.com/studio/v1/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Debug - print the full response structure
                logger.info(f"AI21 response structure: {json.dumps(result, indent=2)}")
                
                # Extract response text - we now know the exact structure
                completion_text = result["choices"][0]["message"]["content"]
                
                # Extract token usage from the response
                usage = {}
                if "usage" in result:
                    usage = {
                        "prompt_tokens": result["usage"].get("prompt_tokens", 0),
                        "completion_tokens": result["usage"].get("completion_tokens", 0),
                        "total_tokens": result["usage"].get("total_tokens", 0)
                    }
                
                return {
                    "text": completion_text,
                    "usage": usage
                }
                
        except Exception as e:
            logger.error(f"AI21 API error: {e}")
            raise
    
    async def close(self):
        """Close the aiohttp session when done"""
        if hasattr(self, 'session'):
            await self.session.close()

# Factory function to create the right evaluator
def create_evaluator(model_config):
    api_type = model_config["api_type"].lower()
    api_key = model_config["api_key"]
    model_name = model_config["model_name"]
    base_url = model_config.get("base_url")
    
    if api_type == "openai":
        return OpenAIEvaluator(api_key, model_name, base_url)
    elif api_type == "anthropic":
        return AnthropicEvaluator(api_key, model_name)
    elif api_type == "gemini":
        return GeminiEvaluator(api_key, model_name)
    elif api_type == "qwen":
        return QwenEvaluator(api_key, model_name)
    elif api_type == "jamba" or api_type == "ai21":
        return AI21Evaluator(api_key, model_name)
    else:
        raise ValueError(f"Unsupported API type: {api_type}")

async def run_api_evaluation(model_config, prompts, output_dir, num_runs=3):
    """Run evaluation on a model via API with multiple runs per prompt"""
    model_name = model_config["display_name"]
    
    logger.info(f"Starting API evaluation for {model_name}")
    
    # Create model directory
    model_dir = create_model_directory(output_dir, model_name)
    
    try:
        # Create appropriate evaluator for this model
        evaluator = create_evaluator(model_config)
        
        # Process each prompt sequence
        for sequence_name, sequence_prompts in prompts.items():
            # Create multiple sequence files for different runs
            for run in range(num_runs):
                sequence_output_file = os.path.join(model_dir, f"{sequence_name}_run{run+1}.txt")
                conversation_history = ""
                
                with open(sequence_output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Model: {model_name}\n")
                    f.write(f"Sequence: {sequence_name}\n")
                    f.write(f"Run: {run+1} of {num_runs}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    for i, prompt_data in enumerate(sequence_prompts):
                        prompt_name = prompt_data["name"]
                        base_prompt_text = prompt_data["text"]
                        
                        # Create a variant of the prompt for this run
                        prompt_text = get_variant_prompt(base_prompt_text, run)
                        
                        logger.info(f"Running {model_name} on {sequence_name} - {prompt_name} (Run {run+1})")
                        
                        # Format prompt with conversation history
                        full_prompt = format_prompt(prompt_text, conversation_history)
                        
                        # Generate response
                        generation_start = time.time()
                        
                        response = await evaluator.generate_response(
                            full_prompt, 
                            temperature=0.9,
                            max_tokens=4096
                        )
                        
                        generation_time = time.time() - generation_start
                        response_text = response["text"].strip()
                        
                        # Try to extract token counts if available
                        usage = response.get("usage", {})
                        token_info = ""
                        if usage:
                            for k, v in usage.items():
                                token_info += f", {k}: {v}"
                        
                        logger.info(f"Generated response in {generation_time:.2f} seconds{token_info}")
                        
                        # Update conversation history for next prompt
                        if not conversation_history:
                            conversation_history = full_prompt + " " + response_text
                        else:
                            conversation_history += f"\n\nHuman: {prompt_text}\n\nAssistant: {response_text}"
                        
                        # Write to output file
                        f.write(f"\n{'='*50}\n")
                        f.write(f"PROMPT {i+1}: {prompt_name}\n")
                        f.write(f"{'='*50}\n\n")
                        f.write(f"{prompt_text}\n\n")
                        f.write(f"{'='*50}\n")
                        f.write(f"RESPONSE:\n")
                        f.write(f"{'='*50}\n\n")
                        f.write(f"{response_text}\n\n")
                        f.write(f"Generation time: {generation_time:.2f} seconds{token_info}\n\n")
                
                logger.info(f"Completed sequence {sequence_name} run {run+1} for {model_name}")
        
        # Clean up
        if hasattr(evaluator, 'close'):
            await evaluator.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error in API evaluation for {model_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main_async():
    parser = argparse.ArgumentParser(description="Evaluate creative capabilities of LLMs via API")
    parser.add_argument("--models_config", required=True, help="JSON file containing API model configurations")
    parser.add_argument("--prompts_file", required=True, help="JSON file containing prompt sequences")
    parser.add_argument("--output_dir", default="api_results", help="Directory to save results")
    parser.add_argument("--num_runs", type=int, default=3, help="Number of runs per prompt sequence")
    parser.add_argument("--parallel", type=int, default=3, help="Number of parallel API evaluations")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load prompts and model configurations
    prompts = load_prompts(args.prompts_file)
    
    with open(args.models_config, 'r', encoding='utf-8') as f:
        models_config = json.load(f)
    
    logger.info(f"Starting API-based evaluation with {args.num_runs} runs per prompt")
    
    # Run evaluations with concurrency control
    semaphore = asyncio.Semaphore(args.parallel)
    
    async def bounded_run_api_evaluation(model_config):
        async with semaphore:
            return await run_api_evaluation(model_config, prompts, args.output_dir, args.num_runs)
    
    tasks = [bounded_run_api_evaluation(model_config) for model_config in models_config]
    results = await tqdm_asyncio.gather(*tasks)
    
    # Check results
    success_count = sum(1 for r in results if r)
    logger.info(f"Completed evaluations: {success_count}/{len(models_config)}")
    
    logger.info("All API evaluations complete")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
