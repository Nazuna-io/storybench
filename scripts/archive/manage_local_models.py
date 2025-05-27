#!/usr/bin/env python3
"""Local Models System Management Script."""

import argparse
import asyncio
import subprocess
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def check_system():
    """Check system health and status."""
    print("=== Local Models System Health Check ===\n")
    
    try:
        # Check database connection
        print("1. Database Connection...")
        os.environ.setdefault("MONGODB_URI", 
            "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0")
        
        from storybench.database.connection import init_database
        database = await init_database()
        
        # Count local model data
        evaluations = await database.evaluations.find({"models": {"$regex": "local_"}}).to_list(length=100)
        responses = await database.responses.find({"model_name": {"$regex": "local_"}}).to_list(length=100)
        
        print(f"   ✅ Connected to MongoDB Atlas")
        print(f"   📊 Local evaluations: {len(evaluations)}")
        print(f"   📝 Local responses: {len(responses)}")
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Check model files
    print("\n2. Model Files...")
    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.rglob("*.gguf"))
        total_size = sum(f.stat().st_size for f in model_files) / (1024**3)  # GB
        
        print(f"   ✅ Models directory exists")
        print(f"   📁 GGUF files: {len(model_files)}")
        print(f"   💾 Total size: {total_size:.1f} GB")
        
        for model_file in model_files:
            size_gb = model_file.stat().st_size / (1024**3)
            print(f"      - {model_file.name}: {size_gb:.1f} GB")
    else:
        print(f"   ⚠️ Models directory not found")
    
    # Check configuration
    print("\n3. Configuration...")
    config_file = Path("config/local_models.json")
    if config_file.exists():
        import json
        with open(config_file) as f:
            config = json.load(f)
        
        print(f"   ✅ Configuration file exists")
        print(f"   🔧 Generation model: {config.get('generation_model', {}).get('filename', 'Not set')}")
        print(f"   📊 Temperature: {config.get('settings', {}).get('temperature', 'Not set')}")
        print(f"   🔢 Max tokens: {config.get('settings', {}).get('max_tokens', 'Not set')}")
    else:
        print(f"   ⚠️ Configuration file not found")
    
    # Check hardware
    print("\n4. Hardware...")
    try:
        from storybench.web.services.local_model_service import LocalModelService
        service = LocalModelService(database=None)
        hardware = await service.get_hardware_info()
        
        print(f"   🖥️ CPU cores: {hardware['cpu_cores']}")
        print(f"   💾 RAM: {hardware['ram_gb']:.1f} GB")
        print(f"   🎮 GPU available: {hardware['gpu_available']}")
        if hardware['gpu_available']:
            print(f"   🎮 GPU: {hardware['gpu_name']}")
            print(f"   🎮 VRAM: {hardware['vram_gb']:.1f} GB")
    except Exception as e:
        print(f"   ❌ Hardware check failed: {e}")
    
    print("\n✅ System health check complete!")
    return True

def run_tests():
    """Run automated tests."""
    print("=== Running Automated Tests ===\n")
    
    # Quick tests
    print("1. Running quick tests...")
    result = subprocess.run([
        "./venv-storybench/bin/python", "-m", "pytest", 
        "tests/local_models/", "-v", "-m", "not slow", "--tb=short"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ Quick tests passed")
    else:
        print("   ❌ Quick tests failed")
        print(result.stdout)
        print(result.stderr)
        return False
    
    # Integration test
    print("\n2. Running integration test...")
    result = subprocess.run([
        "./venv-storybench/bin/python", "test_comprehensive.py"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ Integration test passed")
        # Show last few lines of output
        lines = result.stdout.split('\n')
        for line in lines[-5:]:
            if line.strip():
                print(f"   {line}")
    else:
        print("   ❌ Integration test failed")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print("\n✅ All tests passed!")
    return True

def cleanup_models():
    """Clean up old model files."""
    print("=== Cleaning Up Model Files ===\n")
    
    models_dir = Path("models")
    if not models_dir.exists():
        print("No models directory found.")
        return
    
    # Find all model files
    model_files = list(models_dir.rglob("*.gguf"))
    temp_files = list(models_dir.rglob("*.temp"))
    
    print(f"Found {len(model_files)} model files and {len(temp_files)} temp files")
    
    # Clean up temp files
    for temp_file in temp_files:
        print(f"Removing temp file: {temp_file.name}")
        temp_file.unlink()
    
    # List model files with sizes
    total_size = 0
    for model_file in model_files:
        size_gb = model_file.stat().st_size / (1024**3)
        total_size += size_gb
        print(f"Model: {model_file.name} ({size_gb:.1f} GB)")
    
    print(f"\nTotal model storage: {total_size:.1f} GB")

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Local Models System Management")
    parser.add_argument("command", choices=["check", "test", "cleanup", "all"],
                       help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "check":
        asyncio.run(check_system())
    elif args.command == "test":
        success = run_tests()
        sys.exit(0 if success else 1)
    elif args.command == "cleanup":
        cleanup_models()
    elif args.command == "all":
        print("Running all maintenance tasks...\n")
        success = True
        success &= asyncio.run(check_system())
        print("\n" + "="*50 + "\n")
        success &= run_tests()
        print("\n" + "="*50 + "\n")
        cleanup_models()
        
        if success:
            print("\n🎉 All maintenance tasks completed successfully!")
        else:
            print("\n❌ Some maintenance tasks failed.")
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
