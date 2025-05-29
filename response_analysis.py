#!/usr/bin/env python3
"""
Response Analysis Report Generator

Analyzes response data without evaluation scores.
Shows response patterns, model characteristics, and examples.
"""

import json
import sys
from datetime import datetime
from collections import defaultdict
import statistics

def analyze_responses(data):
    """Analyze response data without evaluation scores."""
    
    responses = data.get('responses', [])
    
    # Group by model
    model_data = defaultdict(list)
    for response in responses:
        model = response.get('model_name', 'unknown')
        model_data[model].append(response)
    
    # Calculate response statistics
    model_stats = {}
    for model, responses in model_data.items():
        avg_length = statistics.mean([len(r.get('text', '')) for r in responses])
        avg_gen_time = statistics.mean([r.get('generation_time', 0) for r in responses if r.get('generation_time')])
        
        # Determine provider
        provider = 'Unknown'
        if 'claude' in model.lower():
            provider = 'Anthropic'
        elif 'gemini' in model.lower():
            provider = 'Google'
        elif 'gpt' in model.lower() or 'o4' in model.lower():
            provider = 'OpenAI'
        elif '/' in model:
            provider = 'Deepinfra'
        
        model_stats[model] = {
            'provider': provider,
            'response_count': len(responses),
            'avg_length': avg_length,
            'avg_generation_time': avg_gen_time,
            'responses': responses[:3]  # Keep first 3 for examples
        }
    
    return model_stats

def generate_response_analysis_report(model_stats, data):
    """Generate analysis report focusing on response characteristics."""
    
    report = []
    
    # Header
    report.append(f"""# Storybench Response Analysis Report

**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}
**Total Responses:** {len(data.get('responses', []))}
**Models Analyzed:** {len(model_stats)}
**Status:** Awaiting Evaluation Scores

---

## 🚨 Note: Evaluation Pending
This report analyzes response patterns and characteristics. 
**Evaluation scores are not yet available** - run evaluations to get performance metrics.

---""")

    # Model overview
    report.append("## 📊 Model Response Overview\n")
    report.append("| Model | Provider | Responses | Avg Length | Avg Gen Time |")
    report.append("|-------|----------|-----------|------------|--------------|")
    
    for model, stats in sorted(model_stats.items(), key=lambda x: x[1]['response_count'], reverse=True):
        report.append(f"| {model} | {stats['provider']} | {stats['response_count']} | {stats['avg_length']:.0f} chars | {stats['avg_generation_time']:.1f}s |")
    
    # Response examples
    report.append("\n## 📝 Response Examples\n")
    
    for model, stats in sorted(model_stats.items(), key=lambda x: x[1]['avg_length'], reverse=True)[:5]:
        report.append(f"### {model} ({stats['provider']})")
        report.append(f"**Average Length:** {stats['avg_length']:.0f} characters")
        report.append(f"**Generation Time:** {stats['avg_generation_time']:.1f}s average")
        
        if stats['responses']:
            example = stats['responses'][0]
            text = example.get('text', '')[:500]  # First 500 chars
            prompt = example.get('prompt_name', 'Unknown Prompt')
            
            report.append(f"**Example Response** (from '{prompt}'):")
            report.append(f"> {text}...")
            report.append("")
    
    return "\n".join(report)

def main():
    if len(sys.argv) < 2:
        print("Usage: python response_analysis.py <data_file.json> [output_file.md]")
        sys.exit(1)
    
    data_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        print(f"📊 Analyzing {len(data.get('responses', []))} responses...")
        
        model_stats = analyze_responses(data)
        report_content = generate_response_analysis_report(model_stats, data)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✓ Response analysis saved to {output_file}")
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"response_analysis_{timestamp}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✓ Response analysis saved to {filename}")
        
        print(f"\n📈 Summary:")
        print(f"   - {len(model_stats)} models analyzed")
        print(f"   - {len(data.get('responses', []))} total responses")
        print(f"   - Evaluation scores: Not available yet")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
