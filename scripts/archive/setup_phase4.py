#!/usr/bin/env python3
"""Quick setup verification for Phase 4 MongoDB migration."""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all Phase 4 requirements are met."""
    print("🔍 Phase 4 Setup Verification")
    print("=" * 40)
    
    checks = []
    
    # Check environment file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        if "MONGODB_URI=" in env_content:
            print("✅ MONGODB_URI found in .env")
            
            # Check if it's still the placeholder
            if "localhost:27017" in env_content:
                print("⚠️  Using localhost MongoDB (testing only)")
                print("   For production, set up MongoDB Atlas and update MONGODB_URI")
            elif "mongodb+srv://" in env_content:
                print("✅ MongoDB Atlas URI configured")
            else:
                print("❓ Custom MongoDB URI detected")
                
            checks.append(True)
        else:
            print("❌ MONGODB_URI not found in .env")
            checks.append(False)
    else:
        print("❌ .env file not found")
        checks.append(False)
    
    # Check source files
    migration_file = Path("src/storybench/database/migrations/import_existing.py")
    if migration_file.exists():
        print("✅ Migration module found")
        checks.append(True)
    else:
        print("❌ Migration module missing")
        checks.append(False)
    
    # Check data files
    output_dir = Path("output")
    if output_dir.exists():
        json_files = list(output_dir.glob("*.json"))
        if json_files:
            print(f"✅ Found {len(json_files)} JSON files to migrate:")
            for f in json_files:
                print(f"   • {f.name}")
            checks.append(True)
        else:
            print("⚠️  No JSON files found in output/ directory")
            checks.append(False)
    else:
        print("❌ output/ directory not found")
        checks.append(False)
    
    # Check CLI
    cli_file = Path("src/storybench/cli.py")
    if cli_file.exists():
        with open(cli_file, 'r') as f:
            cli_content = f.read()
        if "def migrate(" in cli_content:
            print("✅ CLI migrate command available")
            checks.append(True)
        else:
            print("❌ CLI migrate command missing")
            checks.append(False)
    else:
        print("❌ CLI module not found")
        checks.append(False)
    
    print("\n" + "=" * 40)
    
    if all(checks):
        print("🎉 All Phase 4 requirements met!")
        print("\nTo run migration:")
        print("  python -m storybench migrate --validate --cleanup")
        return True
    else:
        print("❌ Some requirements missing. Check items above.")
        return False

def show_next_steps():
    """Show next steps for completing Phase 4."""
    print("\n📋 Next Steps:")
    print("1. Configure MongoDB:")
    print("   • Set up MongoDB Atlas cluster (recommended)")
    print("   • Update MONGODB_URI in .env file")
    print("   • Test connection: python -c 'from src.storybench.database.connection import init_database; import asyncio; asyncio.run(init_database())'")
    print("\n2. Run Migration:")
    print("   • python -m storybench migrate --validate --cleanup")
    print("\n3. Verify Results:")
    print("   • python test_phase4_migration.py")
    print("\n4. Check imported data:")
    print("   • Use MongoDB Compass or CLI to verify data import")

if __name__ == "__main__":
    if check_requirements():
        print("\n✨ Ready to execute Phase 4 migration!")
    else:
        show_next_steps()
