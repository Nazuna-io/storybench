#!/usr/bin/env python3
"""
DEEPINFRA PRODUCTION TEST: DeepSeek-R1 Generation + Evaluation (Production Ready)
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.evaluators.api_evaluator import APIEvaluator


async def test_deepinfra_production():
    """Test full DeepInfra production workflow with generation and evaluation."""
    
    print("\n" + "=" * 70)
    print(" DEEPINFRA PRODUCTION TEST")
    print(" DeepSeek-R1 Generation + Evaluation")
    print("=" * 70)
    
    if not os.getenv("DEEPINFRA_API_KEY"):
        print("❌ DEEPINFRA_API_KEY not found")
        return
    
    api_keys = {"deepinfra": os.getenv("DEEPINFRA_API_KEY")}
    start_time = datetime.now()
    
    test_results = {
        "status": "in_progress",
        "generation_model": "deepseek-ai/DeepSeek-R1",
        "evaluation_model": "deepseek-ai/DeepSeek-R1",
        "responses": [],
        "evaluations": [],
        "performance": {},
        "errors": []
    }
    
    try:
        # Setup Generator
        print("\n🌟 SETUP DEEPINFRA GENERATOR")
        print("-" * 40)
        
        generator_config = {
            "provider": "deepinfra",
            "model_name": "deepseek-ai/DeepSeek-R1",
            "temperature": 0.8,
            "max_tokens": 1024
        }
        
        generator = APIEvaluator("deepseek-r1-gen", generator_config, api_keys)
        if not await generator.setup():
            raise Exception("Generator setup failed")
        print("   ✅ Generator ready")
        
        # Setup Evaluator
        print("\n🎯 SETUP DEEPINFRA EVALUATOR")
        print("-" * 40)
        
        evaluator_config = {
            "provider": "deepinfra",
            "model_name": "deepseek-ai/DeepSeek-R1", 
            "temperature": 0.3,
            "max_tokens": 512
        }        
        evaluator = APIEvaluator("deepseek-r1-eval", evaluator_config, api_keys)
        if not await evaluator.setup():
            raise Exception("Evaluator setup failed")
        print("   ✅ Evaluator ready")
        
        # Test Generation & Evaluation
        print("\n📝 GENERATION + EVALUATION TEST")
        print("-" * 40)
        
        prompts = [
            "Write a short story about AI discovering creativity (150 words)",
            "Explain quantum computing to a 10-year-old (100 words)", 
            "Create a haiku about technology and nature"
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n   Test {i}: {prompt[:40]}...")
            
            # Generate response
            response_data = await generator.generate_response(prompt)
            response_text = response_data.get("response", "")
            generation_time = response_data.get("generation_time", 0)
            
            print(f"   ✅ Generated: {len(response_text)} chars ({generation_time:.2f}s)")
            
            # Evaluate response
            eval_prompt = f"Rate this response 1-10 for quality and relevance to: '{prompt}'\nResponse: {response_text}"
            eval_data = await evaluator.generate_response(eval_prompt)
            eval_text = eval_data.get("response", "")
            eval_time = eval_data.get("generation_time", 0)
            
            print(f"   🎯 Evaluated: {len(eval_text)} chars ({eval_time:.2f}s)")
            
            test_results["responses"].append({
                "prompt": prompt,
                "response": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "generation_time": generation_time
            })
            
            test_results["evaluations"].append({
                "evaluation": eval_text[:150] + "..." if len(eval_text) > 150 else eval_text,
                "evaluation_time": eval_time
            })
        
        # Results
        total_time = (datetime.now() - start_time).total_seconds()
        test_results["performance"] = {
            "total_time": total_time,
            "prompts_processed": len(prompts),
            "avg_generation_time": sum(r["generation_time"] for r in test_results["responses"]) / len(prompts),
            "avg_evaluation_time": sum(e["evaluation_time"] for e in test_results["evaluations"]) / len(prompts)
        }
        
        test_results["status"] = "completed"
        
        print(f"\n📊 PERFORMANCE SUMMARY")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Prompts: {len(prompts)}")
        print(f"   Avg generation: {test_results['performance']['avg_generation_time']:.2f}s")
        print(f"   Avg evaluation: {test_results['performance']['avg_evaluation_time']:.2f}s")
        print(f"\n🎉 SUCCESS: DeepInfra production test completed!")
        
        await generator.cleanup()
        await evaluator.cleanup()
        
    except Exception as e:
        test_results["status"] = "failed"
        test_results["errors"].append(str(e))
        print(f"\n❌ TEST FAILED: {e}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"deepinfra_production_test_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"📄 Results: {report_file}")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_deepinfra_production())
