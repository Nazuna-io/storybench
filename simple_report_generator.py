#!/usr/bin/env python3
"""
Storybench Simple Report Generator

A streamlined version for quick report generation.
Run this script whenever you have new evaluation data.

Usage:
    python simple_report_generator.py [data_file.json]
    
Example:
    python simple_report_generator.py full_api_production_test_report_20250528_212154.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics
import re

def load_data(file_path):
    """Load and validate JSON data."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data.get('responses', []))} responses")
    print(f"✓ Loaded {len(data.get('evaluations', []))} evaluations")
    return data

def parse_scores_from_evaluation(eval_text):
    """Extract numerical scores from evaluation text."""
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality',
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    scores = {}
    for criterion in criteria:
        # Look for patterns like "creativity**: 5" or "creativity: 4.5"
        patterns = [
            rf'\*\*{criterion}\*\*:\s*(\d+(?:\.\d+)?)',
            rf'{criterion}:\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, eval_text, re.IGNORECASE)
            if match:
                scores[criterion] = float(match.group(1))
                break
    
    return scores

def calculate_model_stats(data):
    """Calculate statistics for each model."""
    # Group responses by model
    model_responses = defaultdict(list)
    for response in data['responses']:
        model_name = response.get('model_name')
        if model_name:
            model_responses[model_name].append(response)
    
    # Process evaluations
    evaluations_by_response = {}
    for eval_data in data['evaluations']:
        response_id = eval_data['response_id']
        scores = parse_scores_from_evaluation(eval_data.get('evaluation_text', ''))
        if scores:  # Only include if we found scores
            evaluations_by_response[response_id] = scores
    
    # Calculate model statistics
    model_stats = {}
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality',
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    for model_name, responses in model_responses.items():
        # Get scores for this model's responses
        model_scores = defaultdict(list)
        
        for response in responses:
            response_id = response.get('_id')
            if response_id in evaluations_by_response:
                scores = evaluations_by_response[response_id]
                for criterion, score in scores.items():
                    model_scores[criterion].append(score)
        
        # Calculate averages
        avg_scores = {}
        all_scores = []
        
        for criterion in criteria:
            if model_scores[criterion]:
                avg_score = statistics.mean(model_scores[criterion])
                avg_scores[criterion] = avg_score
                all_scores.extend(model_scores[criterion])
        
        # Overall average
        overall_score = statistics.mean(all_scores) if all_scores else 0
        
        # Determine provider
        provider = 'Unknown'
        if 'claude' in model_name.lower():
            provider = 'Anthropic'
        elif 'gemini' in model_name.lower():
            provider = 'Google'
        elif 'gpt' in model_name.lower() or 'o4' in model_name.lower():
            provider = 'OpenAI'
        elif '/' in model_name:
            provider = 'Deepinfra'
        
        model_stats[model_name] = {
            'overall_score': overall_score,
            'scores': avg_scores,
            'provider': provider,
            'response_count': len(responses),
            'evaluated_count': len([r for r in responses if r.get('_id') in evaluations_by_response])
        }
    
    return model_stats

def generate_report(model_stats, data):
    """Generate markdown report."""
    
    # Sort models by overall score
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['overall_score'], reverse=True)
    
    report = []
    
    # Header
    report.append(f"""# Storybench Model Performance Report

**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}
**Models Analyzed:** {len(model_stats)}
**Total Responses:** {len(data.get('responses', []))}
**Total Evaluations:** {len(data.get('evaluations', []))}

---""")
    
    # Rankings
    report.append("\\n## 🏆 Overall Rankings\\n")
    report.append("| Rank | Model | Score | Provider | Responses |")
    report.append("|------|-------|-------|----------|-----------|")
    
    medals = ["🥇", "🥈", "🥉"] + [""] * 20
    
    for i, (model_name, stats) in enumerate(sorted_models):
        medal = medals[i]
        report.append(f"| {medal} {i+1} | {model_name} | **{stats['overall_score']:.2f}** | {stats['provider']} | {stats['evaluated_count']}/{stats['response_count']} |")
    
    # Score matrix
    report.append("\\n## 📊 Detailed Scores\\n")
    
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality',
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    header = "| Model | Overall | " + " | ".join(c.replace('_', ' ').title() for c in criteria) + " |"
    separator = "|" + "|".join(["-" * 8] * (len(criteria) + 2)) + "|"
    
    report.append(header)
    report.append(separator)
    
    for model_name, stats in sorted_models:
        scores_str = []
        for criterion in criteria:
            score = stats['scores'].get(criterion, 0)
            scores_str.append(f"{score:.2f}")
        
        row = f"| {model_name} | **{stats['overall_score']:.2f}** | " + " | ".join(scores_str) + " |"
        report.append(row)
    
    return "\\n".join(report)

def save_report(content, output_file=None):
    """Save report to file or print to stdout."""
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Report saved to {output_file}")
    else:
        # Generate filename based on timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"storybench_report_{timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Report saved to {filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_report_generator.py <data_file.json> [output_file.md]")
        sys.exit(1)
    
    data_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Load data
        print(f"📊 Loading data from {data_file}...")
        data = load_data(data_file)
        
        # Calculate statistics
        print("🔢 Calculating model statistics...")
        model_stats = calculate_model_stats(data)
        print(f"✓ Analyzed {len(model_stats)} models")
        
        # Generate report
        print("📝 Generating report...")
        report_content = generate_report(model_stats, data)
        
        # Save report
        save_report(report_content, output_file)
        
        # Show top 3
        sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['overall_score'], reverse=True)
        print("\\n🏆 Top 3 Models:")
        for i, (model_name, stats) in enumerate(sorted_models[:3]):
            print(f"  {i+1}. {model_name}: {stats['overall_score']:.2f}/5.0")
        
    except FileNotFoundError:
        print(f"❌ Error: Data file '{data_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
