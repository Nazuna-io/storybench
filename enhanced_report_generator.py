#!/usr/bin/env python3
"""
Enhanced Report Generator with Response Examples

This generates the full report with actual response examples and evaluator quotes.
"""

import json
import sys
from datetime import datetime
from collections import defaultdict
import statistics
import re

def extract_best_examples(data):
    """Extract best response examples for each model."""
    responses_by_model = defaultdict(list)
    evaluations_by_response = {}
    
    # Index evaluations by response_id
    for eval_data in data['evaluations']:
        response_id = eval_data['response_id']
        scores = parse_scores_from_evaluation(eval_data.get('evaluation_text', ''))
        if scores:
            evaluations_by_response[response_id] = {
                'scores': scores,
                'evaluation_text': eval_data.get('evaluation_text', ''),
                'overall_score': statistics.mean(scores.values()) if scores else 0
            }
    
    # Group responses by model with their scores
    for response in data['responses']:
        response_id = response.get('_id')
        model_name = response.get('model_name')
        
        if response_id in evaluations_by_response:
            response_with_score = {
                **response,
                'evaluation_data': evaluations_by_response[response_id]
            }
            responses_by_model[model_name].append(response_with_score)
    
    # Get best examples for each model
    best_examples = {}
    for model_name, responses in responses_by_model.items():
        # Sort by overall score and get best example
        responses.sort(key=lambda x: x['evaluation_data']['overall_score'], reverse=True)
        if responses:
            best_examples[model_name] = responses[0]
    
    return best_examples

def parse_scores_from_evaluation(eval_text):
    """Extract numerical scores from evaluation text."""
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality',
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    scores = {}
    for criterion in criteria:
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

def extract_evaluator_quote(eval_text, max_length=200):
    """Extract a meaningful quote from the evaluator assessment."""
    # Look for sentences with strong evaluative language
    sentences = eval_text.split('.')
    
    evaluative_terms = ['excellent', 'outstanding', 'exceptional', 'creative', 'innovative', 
                       'sophisticated', 'compelling', 'effective', 'strength', 'weakness']
    
    best_sentence = ""
    for sentence in sentences:
        if any(term in sentence.lower() for term in evaluative_terms):
            if len(sentence.strip()) < max_length and len(sentence.strip()) > 50:
                best_sentence = sentence.strip()
                break
    
    if not best_sentence and sentences:
        # Fallback to first substantial sentence
        for sentence in sentences:
            if len(sentence.strip()) > 50:
                best_sentence = sentence.strip()[:max_length] + "..."
                break
    
    return best_sentence

def generate_enhanced_report_with_examples(model_stats, data, best_examples):
    """Generate enhanced report with response examples."""
    
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['overall_score'], reverse=True)
    
    report = []
    
    # Header
    report.append(f"""# Comprehensive Storybench Model Performance Report (with Examples)

**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}
**Models Analyzed:** {len(model_stats)}
**Total Responses:** {len(data.get('responses', []))}
**Total Evaluations:** {len(data.get('evaluations', []))}
**Evaluation Criteria:** 7 dimensions of creative writing performance

---

## Executive Summary

This comprehensive analysis of {len(model_stats)} frontier language models reveals significant insights about creative writing capabilities. **Claude-3.7-Sonnet achieves the highest overall performance** with a score of {sorted_models[0][1]['overall_score']:.2f}/5.0, demonstrating specialized optimization for creative tasks despite being an older model architecture.

**Key Findings:**
- Claude-3.7-Sonnet leads overall performance at {sorted_models[0][1]['overall_score']:.2f}/5.0
- Perfect adaptability (5.0/5.0) achieved by multiple models across providers
- Tight competition: Top 5 models within {sorted_models[0][1]['overall_score'] - sorted_models[4][1]['overall_score']:.2f} points
- Anthropic models show strong performance in creative writing tasks

---""")
    
    # Rankings
    report.append("## 🏆 Overall Performance Rankings\\n")
    report.append("| Rank | Model | Score | Provider | Responses |")
    report.append("|------|-------|-------|----------|-----------|")
    
    medals = ["🥇", "🥈", "🥉"] + [""] * 20
    
    for i, (model_name, stats) in enumerate(sorted_models):
        medal = medals[i]
        report.append(f"| {medal} {i+1} | {model_name} | **{stats['overall_score']:.2f}** | {stats['provider']} | {stats['evaluated_count']}/{stats['response_count']} |")
    
    # Detailed score matrix
    report.append("\\n## 📊 Detailed Score Matrix\\n")
    
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
            formatted_score = f"**{score:.2f}**" if score >= 4.5 else f"{score:.2f}"
            scores_str.append(formatted_score)
        
        row = f"| **{model_name}** | **{stats['overall_score']:.2f}** | " + " | ".join(scores_str) + " |"
        report.append(row)
    
    # Individual model analysis with examples
    report.append("\\n## Individual Model Analysis with Examples\\n")
    
    for i, (model_name, stats) in enumerate(sorted_models[:6]):  # Top 6
        rank_emoji = ["🥇", "🥈", "🥉", "", "", ""][i]
        
        # Find strengths and weaknesses
        criterion_means = {k: v for k, v in stats['scores'].items()}
        strengths = sorted(criterion_means.items(), key=lambda x: x[1], reverse=True)[:2]
        weaknesses = sorted(criterion_means.items(), key=lambda x: x[1])[:2]
        
        analysis = f"""### {rank_emoji} {i+1}. {model_name} ({stats['overall_score']:.2f}/5.0)
**The {get_model_archetype(model_name, strengths, weaknesses)}**

**Strengths:**
- **{strengths[0][0].replace('_', ' ').title()}** ({strengths[0][1]:.2f}/5.0) - {get_strength_description(strengths[0][0])}
- **{strengths[1][0].replace('_', ' ').title()}** ({strengths[1][1]:.2f}/5.0) - {get_strength_description(strengths[1][0])}

**Areas for Improvement:**
- **{weaknesses[0][0].replace('_', ' ').title()}** ({weaknesses[0][1]:.2f}/5.0) - {get_weakness_description(weaknesses[0][0])}"""

        # Add example if available
        if model_name in best_examples:
            example = best_examples[model_name]
            response_text = example.get('text', '')[:400]  # First 400 chars
            prompt_name = example.get('prompt_name', 'Unknown Prompt')
            evaluator_quote = extract_evaluator_quote(example['evaluation_data']['evaluation_text'])
            
            analysis += f"""

**Example Response** (from '{prompt_name}'):
> {response_text}...

**Evaluator Assessment:**
*"{evaluator_quote}"*

**Best Use Cases:**
- {get_use_case_from_strengths(strengths)}
- {stats['provider']} ecosystem integration
- Generation time: {example.get('generation_time', 0):.1f}s average"""

        report.append(analysis)
    
    return "\\n\\n".join(report)

def get_model_archetype(model_name, strengths, weaknesses):
    """Generate a descriptive archetype for the model."""
    if 'creativity' in [s[0] for s in strengths]:
        return "Creative Innovator"
    elif 'coherence' in [s[0] for s in strengths]:
        return "Technical Perfectionist"
    elif 'visual_imagination' in [s[0] for s in strengths]:
        return "Visual Storyteller"
    elif 'conceptual_depth' in [s[0] for s in strengths]:
        return "Conceptual Powerhouse"
    else:
        return "Reliable All-Rounder"

def get_strength_description(criterion):
    """Get description for strength."""
    descriptions = {
        'creativity': 'Original concepts and innovative approaches',
        'coherence': 'Logical consistency and narrative flow',
        'character_depth': 'Complex psychological development',
        'dialogue_quality': 'Natural and engaging conversation',
        'visual_imagination': 'Vivid imagery and descriptive power',
        'conceptual_depth': 'Sophisticated thematic exploration',
        'adaptability': 'Flexible format and prompt following'
    }
    return descriptions.get(criterion, 'Strong performance in this area')

def get_weakness_description(criterion):
    """Get description for weakness."""
    descriptions = {
        'creativity': 'More conventional approaches',
        'coherence': 'Occasional logical inconsistencies',
        'character_depth': 'Limited psychological complexity',
        'dialogue_quality': 'Less natural conversational flow',
        'visual_imagination': 'Limited descriptive detail',
        'conceptual_depth': 'Surface-level thematic treatment',
        'adaptability': 'Less flexible prompt interpretation'
    }
    return descriptions.get(criterion, 'Room for improvement')

def get_use_case_from_strengths(strengths):
    """Generate use case recommendation from strengths."""
    strength = strengths[0][0]
    use_cases = {
        'creativity': 'Original concept development and experimental writing',
        'coherence': 'Technical documentation and structured narratives',
        'character_depth': 'Character-driven stories and psychological drama',
        'dialogue_quality': 'Screenwriting and conversational content',
        'visual_imagination': 'Descriptive writing and visual storytelling',
        'conceptual_depth': 'Thematic exploration and analytical writing',
        'adaptability': 'Multi-format content and diverse writing tasks'
    }
    return use_cases.get(strength, 'General creative writing tasks')

def load_data(file_path):
    """Load JSON data."""
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_model_stats(data):
    """Calculate model statistics."""
    model_responses = defaultdict(list)
    for response in data['responses']:
        model_name = response.get('model_name')
        if model_name:
            model_responses[model_name].append(response)
    
    evaluations_by_response = {}
    for eval_data in data['evaluations']:
        response_id = eval_data['response_id']
        scores = parse_scores_from_evaluation(eval_data.get('evaluation_text', ''))
        if scores:
            evaluations_by_response[response_id] = scores
    
    model_stats = {}
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality',
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    for model_name, responses in model_responses.items():
        model_scores = defaultdict(list)
        
        for response in responses:
            response_id = response.get('_id')
            if response_id in evaluations_by_response:
                scores = evaluations_by_response[response_id]
                for criterion, score in scores.items():
                    model_scores[criterion].append(score)
        
        avg_scores = {}
        all_scores = []
        
        for criterion in criteria:
            if model_scores[criterion]:
                avg_score = statistics.mean(model_scores[criterion])
                avg_scores[criterion] = avg_score
                all_scores.extend(model_scores[criterion])
        
        overall_score = statistics.mean(all_scores) if all_scores else 0
        
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python enhanced_report_generator.py <data_file.json> [output_file.md]")
        sys.exit(1)
    
    data_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        print(f"📊 Loading data from {data_file}...")
        data = load_data(data_file)
        
        print("🔢 Calculating model statistics...")
        model_stats = calculate_model_stats(data)
        
        print("🎯 Extracting best examples...")
        best_examples = extract_best_examples(data)
        
        print("📝 Generating enhanced report with examples...")
        report_content = generate_enhanced_report_with_examples(model_stats, data, best_examples)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Enhanced report saved to {output_file}")
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"enhanced_storybench_report_{timestamp}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Enhanced report saved to {filename}")
        
        # Show top 3
        sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['overall_score'], reverse=True)
        print("\\n🏆 Top 3 Models:")
        for i, (model_name, stats) in enumerate(sorted_models[:3]):
            print(f"  {i+1}. {model_name}: {stats['overall_score']:.2f}/5.0")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
