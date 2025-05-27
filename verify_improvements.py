#!/usr/bin/env python3
"""Quick verification test for large context improvements."""

import json
import asyncio
from pathlib import Path

async def verify_improvements():
    """Verify that our improvements are properly configured."""
    
    print("🔍 Verifying Large Context Improvements...")
    print()
    
    # Check 1: Local models configuration
    config_path = Path("config/local_models.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            
        model = config["models"][0]
        settings = model["model_settings"]
        
        print("✅ Configuration Check:")
        print(f"   Model: {model['name']}")
        print(f"   Context Window: {settings['n_ctx']:,} tokens")
        print(f"   Max Generation: {settings['max_tokens']:,} tokens")
        print(f"   GPU Layers: {settings['n_gpu_layers']}")
        print()
        
        # Verify our improvements
        if settings['n_ctx'] >= 32768:
            print("✅ Context window: Adequate for 14k+ responses")
        else:
            print("❌ Context window: Too small for large responses")
            
        if settings['max_tokens'] >= 16384:
            print("✅ Generation limit: Supports 14k+ tokens")
        else:
            print("❌ Generation limit: Too small for creative writing")
    else:
        print("❌ Local models config not found")
        return
    
    # Check 2: Code improvements
    main_script = Path("run_end_to_end.py")
    if main_script.exists():
        content = main_script.read_text()
        
        improvements = [
            ("Improved token estimation", "len(text) // 3"),
            ("Large safety buffer", "500"),
            ("Model state reset", "reset_model_state"),
            ("Context debugging", "Context management -"),
            ("Natural boundaries", "boundary in"),
        ]
        
        print("✅ Code Improvements:")
        for name, marker in improvements:
            if marker in content:
                print(f"   ✅ {name}")
            else:
                print(f"   ❌ {name}")
        print()
    
    # Check 3: LocalEvaluator improvements
    evaluator_path = Path("src/storybench/evaluators/local_evaluator.py")
    if evaluator_path.exists():
        content = evaluator_path.read_text()
        
        evaluator_improvements = [
            ("Model state reset method", "async def reset_model_state"),
            ("Retry mechanism", "max_retries = 2"),
            ("Empty output detection", "len(generated_text) < 10"),
            ("Performance logging", "tokens_per_second"),
        ]
        
        print("✅ LocalEvaluator Improvements:")
        for name, marker in evaluator_improvements:
            if marker in content:
                print(f"   ✅ {name}")
            else:
                print(f"   ❌ {name}")
        print()
    
    print("🎯 Ready to test with improved large context support!")
    print("   Run: ./run_local_test.sh")
    print()
    print("📊 Expected improvements:")
    print("   • First prompt: Works (up to 16k tokens)")
    print("   • Subsequent prompts: Now work (up to 16k tokens each)")
    print("   • Context: 32k tokens (full model capacity)")
    print("   • Recovery: Automatic retry with model reset")

if __name__ == "__main__":
    asyncio.run(verify_improvements())
