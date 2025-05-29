#!/usr/bin/env python3
"""
Quick Storybench Report Runner

This script automatically finds the latest data file and generates a report.
Perfect for quick analysis after running evaluations.

Usage:
    python run_report.py [--examples] [--output filename]
    
Examples:
    python run_report.py                           # Basic report from latest data
    python run_report.py --examples               # Report with response examples  
    python run_report.py --output my_report.md    # Custom output filename
"""

import os
import glob
import argparse
from pathlib import Path
from datetime import datetime

def find_latest_data_file():
    """Find the most recent data file."""
    patterns = [
        "full_api_production_test_report_*.json",
        "*_test_report_*.json", 
        "evaluation_results.json",
        "*.json"
    ]
    
    latest_file = None
    latest_time = 0
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            if os.path.isfile(file):
                mtime = os.path.getmtime(file)
                if mtime > latest_time:
                    latest_time = mtime
                    latest_file = file
    
    return latest_file

def run_simple_report(data_file, output_file=None):
    """Run the simple report generator."""
    cmd_parts = ["python", "simple_report_generator.py", data_file]
    
    if output_file:
        cmd_parts.append(output_file)
    
    cmd = " ".join(cmd_parts)
    print(f"🚀 Running: {cmd}")
    
    result = os.system(cmd)
    return result == 0

def main():
    parser = argparse.ArgumentParser(description="Quick Storybench report generation")
    parser.add_argument("--examples", action="store_true", 
                       help="Include response examples (slower but more detailed)")
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument("--data", help="Specific data file to use")
    
    args = parser.parse_args()
    
    # Find data file
    if args.data:
        data_file = args.data
        if not os.path.exists(data_file):
            print(f"❌ Data file not found: {data_file}")
            return 1
    else:
        print("🔍 Looking for latest data file...")
        data_file = find_latest_data_file()
        
        if not data_file:
            print("❌ No data files found. Expected files like:")
            print("  - full_api_production_test_report_*.json")
            print("  - *_test_report_*.json") 
            print("  - evaluation_results.json")
            return 1
    
    print(f"📊 Using data file: {data_file}")
    
    # Generate output filename
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        if args.examples:
            args.output = f"storybench_report_with_examples_{timestamp}.md"
        else:
            args.output = f"storybench_report_{timestamp}.md"
    
    # Run report generation
    print(f"📝 Generating report: {args.output}")
    
    if args.examples:
        # Use the more detailed generator (if it exists)
        if os.path.exists("generate_storybench_report.py"):
            cmd = f"python generate_storybench_report.py {data_file} --output {args.output} --examples"
            print(f"🚀 Running: {cmd}")
            result = os.system(cmd)
        else:
            print("⚠️  Full report generator not found, using simple version")
            result = run_simple_report(data_file, args.output)
    else:
        result = run_simple_report(data_file, args.output)
    
    if result:
        print(f"✅ Report generated successfully: {args.output}")
        print(f"📖 Open with: open {args.output}")
        return 0
    else:
        print("❌ Report generation failed")
        return 1

if __name__ == "__main__":
    exit(main())
