#!/usr/bin/env python3
"""
Corrected Storybench Analysis with Fixed Score Extraction
"""

import os
import re
from collections import defaultdict
from datetime import datetime
import statistics

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

def improved_extract_scores(text):
    """Improved score extraction with multiple parsing strategies."""
    scores = {}
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    text_lower = text.lower()
    
    for criterion in criteria:
        score_found = False
        
        # Strategy 1: Multiple patterns
        patterns = [
            rf'{criterion}[:\s-]+([1-5](?:\.\d)?)',
            rf'\\*\\*{criterion}\\*\\*[:\s-]+([1-5](?:\.\d)?)',
            rf'{criterion}[:\s]*([1-5](?:\.\d)?)[/\s]*5',
            rf'{criterion.replace("_", " ")}[:\s-]+([1-5](?:\.\d)?)',
        ]
        
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text_lower)
                if matches:
                    score = float(matches[0])
                    if 1 <= score <= 5:
                        scores[criterion] = score
                        score_found = True
                        break
            except (ValueError, re.error):
                continue
        
        # Strategy 2: Context-based search
        if not score_found:
            criterion_pos = text_lower.find(criterion)
            if criterion_pos >= 0:
                start = max(0, criterion_pos - 50)
                end = min(len(text_lower), criterion_pos + 50)
                context = text_lower[start:end]
                
                number_matches = re.findall(r'([1-5](?:\.\d)?)', context)
                for match in number_matches:
                    try:
                        score = float(match)
                        if 1 <= score <= 5:
                            scores[criterion] = score
                            break
                    except ValueError:
                        continue
    
    return scores

# Connect to database
client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=30000)
db = client['storybench']

# Get latest batch
latest_response = db.responses.find({'test_run': True}).sort('created_at', -1).limit(1)
batch_id = None
for doc in latest_response:
    batch_id = doc['test_batch']
    break

print(f"📦 Analyzing corrected batch: {batch_id}")

# Load data
responses = list(db.responses.find({'test_batch': batch_id}))
evaluations = list(db.response_llm_evaluations.find({'test_batch': batch_id}))

print(f"📊 {len(responses)} responses, {len(evaluations)} evaluations")

# Create response lookup
response_lookup = {str(r['_id']): r for r in responses}

# Analyze with improved extraction
model_stats = defaultdict(lambda: {
    'scores': defaultdict(list),
    'response_count': 0,
    'eval_count': 0,
    'parsed_count': 0
})

total_parsed = 0
for eval_doc in evaluations:
    response_id = str(eval_doc['response_id'])
    if response_id not in response_lookup:
        continue
    
    response = response_lookup[response_id]
    model_name = response['model_name']
    
    scores = improved_extract_scores(eval_doc['evaluation_text'])
    
    if scores:
        total_parsed += 1
        model_stats[model_name]['parsed_count'] += 1
        for criterion, score in scores.items():
            model_stats[model_name]['scores'][criterion].append(score)
    
    model_stats[model_name]['eval_count'] += 1

# Count responses
for response in responses:
    model_name = response['model_name']
    model_stats[model_name]['response_count'] += 1

parsing_rate = total_parsed / len(evaluations) * 100
print(f"✅ Parsed {total_parsed}/{len(evaluations)} evaluations ({parsing_rate:.1f}%)")

# Calculate performance
model_performance = []

for model_name, stats in model_stats.items():
    if stats['response_count'] == 0:
        continue
    
    criterion_averages = {}
    overall_scores = []
    
    for criterion, scores in stats['scores'].items():
        if scores:
            avg = round(statistics.mean(scores), 2)
            criterion_averages[criterion] = {
                'average': avg,
                'count': len(scores)
            }
            overall_scores.append(avg)
    
    overall_avg = round(statistics.mean(overall_scores), 2) if overall_scores else 0
    
    model_performance.append({
        'model': model_name,
        'overall': overall_avg,
        'responses': stats['response_count'],
        'evaluations': stats['eval_count'],
        'parsed': stats['parsed_count'],
        'criteria': criterion_averages
    })

# Sort by performance
model_performance.sort(key=lambda x: x['overall'], reverse=True)

print("\n" + "=" * 90)
print(" CORRECTED STORYBENCH ANALYSIS")
print("=" * 90)
print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f" Parsing Success: {parsing_rate:.1f}%")
print()

print("🏆 CORRECTED OVERALL RANKINGS")
print("=" * 70)

for i, perf in enumerate(model_performance):
    if perf['overall'] > 0:
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1:2d}."
        parsing_pct = perf['parsed'] / perf['evaluations'] * 100 if perf['evaluations'] > 0 else 0
        print(f"{medal} {perf['model']:<50} {perf['overall']:.2f}/5.0")
        print(f"    Responses: {perf['responses']}/45 | Parsed: {perf['parsed']}/{perf['evaluations']} ({parsing_pct:.0f}%)")

print()
print("📊 TOP MODEL DETAILS")
print("=" * 70)

criteria_names = {
    'creativity': 'Creativity',
    'coherence': 'Coherence',
    'character_depth': 'Character Depth',
    'dialogue_quality': 'Dialogue Quality',
    'visual_imagination': 'Visual Imagination',
    'conceptual_depth': 'Conceptual Depth',
    'adaptability': 'Adaptability'
}

for i, perf in enumerate(model_performance[:6]):
    if perf['overall'] == 0:
        continue
        
    print(f"\n🤖 #{i+1} {perf['model']}")
    print(f"   Overall Score: {perf['overall']:.2f}/5.0")
    print("   Detailed Scores:")
    
    # Sort criteria by score
    sorted_criteria = sorted(perf['criteria'].items(), key=lambda x: x[1]['average'], reverse=True)
    
    for criterion, data in sorted_criteria:
        display_name = criteria_names.get(criterion, criterion.replace('_', ' ').title())
        print(f"      {display_name:<18}: {data['average']:.2f} ({data['count']} evals)")

# Claude comparison
print(f"\n🔍 CLAUDE 3 vs CLAUDE 4 ANALYSIS")
print("=" * 70)

claude_3_models = [m for m in model_performance if 'claude-3' in m['model'].lower() and m['overall'] > 0]
claude_4_models = [m for m in model_performance if ('opus-4' in m['model'].lower() or 'sonnet-4' in m['model'].lower()) and m['overall'] > 0]

if claude_3_models and claude_4_models:
    print("Claude-3 Models:")
    for model in claude_3_models:
        print(f"  • {model['model']}: {model['overall']:.2f}")
    
    print("Claude-4 Models:")
    for model in claude_4_models:
        print(f"  • {model['model']}: {model['overall']:.2f}")
    
    claude_3_avg = statistics.mean([m['overall'] for m in claude_3_models])
    claude_4_avg = statistics.mean([m['overall'] for m in claude_4_models])
    
    print(f"\nAverage Scores:")
    print(f"  Claude-3: {claude_3_avg:.2f}")
    print(f"  Claude-4: {claude_4_avg:.2f}")
    
    if claude_3_avg > claude_4_avg:
        diff = claude_3_avg - claude_4_avg
        print(f"\n🔍 FINDING: Claude-3 outperforms Claude-4 by {diff:.2f} points!")
        print("  This suggests Claude-3.7-Sonnet may be specifically optimized for creative tasks")

# Key insights
print(f"\n💡 KEY INSIGHTS")
print("=" * 70)

if model_performance:
    reliable_models = [m for m in model_performance if m['overall'] > 0 and m['parsed'] >= 20]
    
    if reliable_models:
        best = reliable_models[0]
        print(f"🥇 Best Overall: {best['model']} ({best['overall']:.2f}/5.0)")
        
        # Creative leaders
        creative_models = []
        for perf in reliable_models:
            creativity = perf['criteria'].get('creativity', {}).get('average', 0)
            visual = perf['criteria'].get('visual_imagination', {}).get('average', 0)
            if creativity > 0 and visual > 0:
                creative_score = (creativity + visual) / 2
                creative_models.append((perf['model'], creative_score))
        
        if creative_models:
            creative_models.sort(key=lambda x: x[1], reverse=True)
            best_creative = creative_models[0]
            print(f"🎨 Best Creative: {best_creative[0]} ({best_creative[1]:.2f})")

print("\n" + "=" * 90)
print(" CORRECTED ANALYSIS COMPLETE")
print("=" * 90)

client.close()
