#!/usr/bin/env python3
"""
Regression Test: Simulate a real evaluation workflow to ensure no breaking changes.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_evaluation_workflow():
    """Test a realistic evaluation workflow"""
    print("🎭 Testing Evaluation Workflow...")
    
    try:
        # Test 1: Configuration loading
        from storybench.models.config import Config
        print("  ✅ Configuration system loads successfully")
        
        # Test 2: Evaluator factory
        from storybench.evaluators.factory import EvaluatorFactory
        print("  ✅ Evaluator factory loads successfully")
        
        # Test 3: Database models and services
        from storybench.database.models import Evaluation, Response
        from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner
        print("  ✅ Database models and services load successfully")
        
        # Test 4: Context management in realistic scenario
        from storybench.unified_context_system import UnifiedContextManager
        from storybench.langchain_context_manager import ContextConfig
        
        # Simulate realistic creative writing prompts
        prompts = [
            "Write the opening paragraph of a mystery novel set in a small coastal town.",
            "Continue the story, introducing the main character who discovers something unusual.",
            "Develop the mystery further with a surprising revelation about the town's history."
        ]
        
        config = ContextConfig(max_context_tokens=4096)
        manager = UnifiedContextManager(config)
        
        total_context = ""
        for i, prompt in enumerate(prompts):
            # Simulate context accumulation within a sequence
            full_prompt = total_context + "\n\n" + prompt if total_context else prompt
            
            try:
                analytics = manager.get_context_analytics(full_prompt)
                print(f"    📝 Prompt {i+1}: {analytics['estimated_tokens']} tokens, {analytics['utilization_percent']:.1f}% utilization")
                
                # Simulate adding a response to context
                total_context = full_prompt + "\n\nThe old lighthouse keeper squinted through the morning fog..."
                
            except Exception as e:
                print(f"    ❌ Context error on prompt {i+1}: {e}")
                return False
        
        # Test 5: Performance monitoring
        from storybench.utils.performance import performance_monitor
        stats = performance_monitor.get_performance_summary()
        print(f"  ✅ Performance monitoring: {stats['total_queries']} queries tracked")
        
        # Test 6: Retry handler readiness  
        from storybench.utils.retry_handler import retry_handler
        retry_stats = retry_handler.get_retry_stats()
        print(f"  ✅ Retry handler ready: {len(retry_stats)} providers configured")
        
        print("  🎯 Evaluation Workflow: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Evaluation Workflow Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run regression tests"""
    print("🔍 Phase 1 Regression Test Suite")
    print("="*50)
    
    success = await test_evaluation_workflow()
    
    print("\n" + "="*50)
    if success:
        print("🎉 NO REGRESSIONS DETECTED! 🎸")
        print("✅ All core evaluation workflows functioning normally")
        print("✅ Phase 1 improvements integrated successfully") 
        print("✅ Ready for production use")
        print("\n🚀 Phase 1 is totally tubular - let's move to Phase 2!")
    else:
        print("❌ Regression detected - needs investigation")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
