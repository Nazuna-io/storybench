#!/usr/bin/env python3
"""Test script to verify configuration loader functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.config_loader import ConfigLoader, load_config

def test_config_loader():
    """Test the configuration loader with our models.yaml."""
    print("Testing StoryBench v1.5 Configuration Loader")
    print("=" * 60)
    
    try:
        # Load configuration
        print("\n1. Loading configuration from config/models.yaml...")
        config = load_config("config/models.yaml")
        print("✅ Configuration loaded successfully!")
        
        # Display model summary
        print("\n2. Model Summary:")
        print("-" * 40)
        for provider, models in config.models.items():
            enabled = [m for m in models if m.enabled]
            disabled = [m for m in models if not m.enabled]
            print(f"  {provider.upper()}:")
            print(f"    - Total: {len(models)} models")
            print(f"    - Enabled: {len(enabled)}")
            print(f"    - Disabled: {len(disabled)}")
            for model in models:
                status = "✓" if model.enabled else "✗"
                print(f"      {status} {model.name} ({model.max_tokens:,} tokens)")
        
        # Display evaluation settings
        print("\n3. Evaluation Settings:")
        print("-" * 40)
        print(f"  Evaluator: {config.evaluation.evaluator_model}")
        print(f"  Provider: {config.evaluation.evaluator_provider}")
        print(f"  Generation temp: {config.evaluation.temperature_generation}")
        print(f"  Evaluation temp: {config.evaluation.temperature_evaluation}")
        
        # Display pipeline settings
        print("\n4. Pipeline Settings:")
        print("-" * 40)
        print(f"  Runs per sequence: {config.pipeline.runs_per_sequence}")
        print(f"  Reset context between sequences: {config.pipeline.reset_context_between_sequences}")
        print(f"  Checkpoint interval: {config.pipeline.checkpoint_interval}")
        
        # Validate configuration
        print("\n5. Validating Configuration...")
        warnings = config.validate()
        if warnings:
            print("⚠️  Validation warnings:")
            for warning in warnings:
                print(f"    - {warning}")
        else:
            print("✅ No validation warnings!")
        
        # Test specific model lookup
        print("\n6. Testing Model Lookup:")
        print("-" * 40)
        test_cases = [
            ("anthropic", "claude-opus-4"),
            ("google", "gemini-2.5-pro-preview-05-06"),
            ("deepinfra", "deepseek-r1")
        ]
        
        for provider, model_name in test_cases:
            model = config.get_model(provider, model_name)
            if model:
                print(f"  ✅ Found {provider}/{model_name}: {model.max_tokens:,} tokens")
            else:
                print(f"  ❌ Not found: {provider}/{model_name}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print(f"  Total models: {len(config.all_models)}")
        print(f"  Enabled models: {len(config.enabled_models)}")
        print(f"  Configuration is valid: {'Yes' if not warnings else 'Has warnings'}")
        print("\n✅ Configuration loader is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_config_loader()
    sys.exit(0 if success else 1)
