#!/usr/bin/env python3
"""
Storybench Model Performance Analysis Report
==========================================
Analyzes evaluation results from the end-to-end test to rank models
and provide insights on their performance across different creative tasks.
"""

import os
import sys
import json
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple
import statistics

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient


class StorybenchAnalyzer:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=30000)
        self.db = self.client['storybench']
        self.responses_collection = self.db['responses']
        self.evaluations_collection = self.db['response_llm_evaluations']
        
        # Get latest test batch
        latest_response = self.responses_collection.find({'test_run': True}).sort('created_at', -1).limit(1)
        self.batch_id = None
        for doc in latest_response:
            self.batch_id = doc['test_batch']
            break
        
        if not self.batch_id:
            raise Exception("No test batch found")
        
        print(f"📦 Analyzing batch: {self.batch_id}")
    
    
    def extract_scores_from_evaluation(self, evaluation_text: str) -> Dict[str, float]:
        """Extract numerical scores from evaluation text using regex patterns."""
        scores = {}
        criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                   'visual_imagination', 'conceptual_depth', 'adaptability']
        
        for criterion in criteria:
            # Look for patterns like "creativity: 4", "creativity: 4.5", etc.
            patterns = [
                rf"{criterion}[:\s]+(\d+(?:\.\d+)?)",
                rf"\b{criterion}[:\s]*(\d+(?:\.\d+)?)",
                rf"**{criterion}**[:\s]*(\d+(?:\.\d+)?)"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, evaluation_text, re.IGNORECASE)
                if matches:
                    try:
                        score = float(matches[0])
                        if 1 <= score <= 5:  # Valid score range
                            scores[criterion] = score
                            break
                    except ValueError:
                        continue
        
        return scores
    
    
    def load_data(self) -> Tuple[List[Dict], List[Dict]]:
        """Load responses and evaluations from database."""
        print("📊 Loading data from database...")
        
        # Load responses
        responses = list(self.responses_collection.find({'test_batch': self.batch_id}))
        print(f"   📝 Loaded {len(responses)} responses")
        
        # Load evaluations
        evaluations = list(self.evaluations_collection.find({'test_batch': self.batch_id}))
        print(f"   🎯 Loaded {len(evaluations)} evaluations")
        
        return responses, evaluations
    
    
    def analyze_model_performance(self, responses: List[Dict], evaluations: List[Dict]) -> Dict[str, Any]:
        """Analyze performance of each model across all criteria."""
        print("🔍 Analyzing model performance...")
        
        # Create lookup for responses
        response_lookup = {str(r['_id']): r for r in responses}
        
        # Organize data by model
        model_data = defaultdict(lambda: {
            'scores': defaultdict(list),
            'response_count': 0,
            'evaluation_count': 0,
            'sequences': defaultdict(int),
            'total_tokens': 0,
            'avg_response_length': 0
        })
        
        # Process evaluations
        for eval_doc in evaluations:
            response_id = str(eval_doc['response_id'])
            if response_id not in response_lookup:
                continue
            
            response = response_lookup[response_id]
            model_name = response['model_name']
            sequence_name = response['sequence_name']
            
            # Extract scores from evaluation text
            scores = self.extract_scores_from_evaluation(eval_doc['evaluation_text'])
            
            # Store scores
            for criterion, score in scores.items():
                model_data[model_name]['scores'][criterion].append(score)
            
            model_data[model_name]['evaluation_count'] += 1
            model_data[model_name]['sequences'][sequence_name] += 1
        
        # Process responses for additional stats
        for response in responses:
            model_name = response['model_name']
            model_data[model_name]['response_count'] += 1
            model_data[model_name]['total_tokens'] += len(response['text'])
        
        # Calculate averages and rankings
        model_performance = {}
        
        for model_name, data in model_data.items():
            if data['response_count'] == 0:
                continue
            
            performance = {
                'model_name': model_name,
                'response_count': data['response_count'],
                'evaluation_count': data['evaluation_count'],
                'avg_response_length': data['total_tokens'] / data['response_count'],
                'sequence_distribution': dict(data['sequences']),
                'criterion_scores': {},
                'overall_average': 0
            }
            
            # Calculate average scores per criterion
            criterion_averages = []
            for criterion, scores in data['scores'].items():
                if scores:
                    avg_score = statistics.mean(scores)
                    std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
                    performance['criterion_scores'][criterion] = {
                        'average': round(avg_score, 2),
                        'std_dev': round(std_dev, 2),
                        'count': len(scores),
                        'scores': scores
                    }
                    criterion_averages.append(avg_score)
            
            # Overall average
            if criterion_averages:
                performance['overall_average'] = round(statistics.mean(criterion_averages), 2)
            
            model_performance[model_name] = performance
        
        return model_performance
    
    
    def analyze_by_sequence(self, responses: List[Dict], evaluations: List[Dict]) -> Dict[str, Any]:
        """Analyze performance by creative writing sequence."""
        print("📝 Analyzing performance by sequence...")
        
        response_lookup = {str(r['_id']): r for r in responses}
        sequence_analysis = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for eval_doc in evaluations:
            response_id = str(eval_doc['response_id'])
            if response_id not in response_lookup:
                continue
            
            response = response_lookup[response_id]
            model_name = response['model_name']
            sequence_name = response['sequence_name']
            
            scores = self.extract_scores_from_evaluation(eval_doc['evaluation_text'])
            
            for criterion, score in scores.items():
                sequence_analysis[sequence_name][model_name][criterion].append(score)
        
        # Calculate sequence performance
        sequence_performance = {}
        for sequence_name, models in sequence_analysis.items():
            sequence_perf = {
                'sequence_name': sequence_name,
                'model_rankings': {},
                'best_model': None,
                'worst_model': None,
                'sequence_characteristics': {}
            }
            
            model_averages = []
            for model_name, criteria in models.items():
                criterion_averages = []
                for criterion, scores in criteria.items():
                    if scores:
                        criterion_averages.append(statistics.mean(scores))
                
                if criterion_averages:
                    overall_avg = statistics.mean(criterion_averages)
                    sequence_perf['model_rankings'][model_name] = round(overall_avg, 2)
                    model_averages.append((model_name, overall_avg))
            
            if model_averages:
                model_averages.sort(key=lambda x: x[1], reverse=True)
                sequence_perf['best_model'] = model_averages[0]
                sequence_perf['worst_model'] = model_averages[-1]
            
            sequence_performance[sequence_name] = sequence_perf
        
        return sequence_performance
    
    
    def generate_rankings(self, model_performance: Dict[str, Any]) -> List[Tuple[str, float, Dict]]:
        """Generate overall model rankings."""
        print("🏆 Generating model rankings...")
        
        rankings = []
        for model_name, perf in model_performance.items():
            if perf['overall_average'] > 0:
                rankings.append((model_name, perf['overall_average'], perf))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    
    def identify_strengths_weaknesses(self, model_performance: Dict[str, Any]) -> Dict[str, Dict]:
        """Identify what each model is best and worst at."""
        print("💪 Identifying model strengths and weaknesses...")
        
        # Collect all scores by criterion across all models
        criterion_scores = defaultdict(list)
        for model_name, perf in model_performance.items():
            for criterion, data in perf['criterion_scores'].items():
                criterion_scores[criterion].append((model_name, data['average']))
        
        # Find best and worst for each criterion
        criterion_leaders = {}
        for criterion, model_scores in criterion_scores.items():
            if model_scores:
                model_scores.sort(key=lambda x: x[1], reverse=True)
                criterion_leaders[criterion] = {
                    'best': model_scores[0],
                    'worst': model_scores[-1],
                    'all_scores': model_scores
                }
        
        # Identify each model's strengths and weaknesses
        model_insights = {}
        for model_name, perf in model_performance.items():
            strengths = []
            weaknesses = []
            
            for criterion, data in perf['criterion_scores'].items():
                if criterion in criterion_leaders:
                    leaders = criterion_leaders[criterion]['all_scores']
                    model_rank = next((i for i, (name, score) in enumerate(leaders) if name == model_name), None)
                    
                    if model_rank is not None:
                        total_models = len(leaders)
                        percentile = (total_models - model_rank) / total_models
                        
                        if percentile >= 0.8:  # Top 20%
                            strengths.append((criterion, data['average'], model_rank + 1))
                        elif percentile <= 0.3:  # Bottom 30%
                            weaknesses.append((criterion, data['average'], model_rank + 1))
            
            model_insights[model_name] = {
                'strengths': strengths,
                'weaknesses': weaknesses,
                'overall_rank': None  # Will be filled in later
            }
        
        return model_insights, criterion_leaders
    
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report."""
        print("📊 Generating comprehensive report...")
        
        responses, evaluations = self.load_data()
        model_performance = self.analyze_model_performance(responses, evaluations)
        sequence_performance = self.analyze_by_sequence(responses, evaluations)
        rankings = self.generate_rankings(model_performance)
        model_insights, criterion_leaders = self.identify_strengths_weaknesses(model_performance)
        
        # Update overall ranks in insights
        for i, (model_name, score, perf) in enumerate(rankings):
            if model_name in model_insights:
                model_insights[model_name]['overall_rank'] = i + 1
        
        # Generate report
        report = []
        report.append("=" * 80)
        report.append(" STORYBENCH MODEL PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f" Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f" Test Batch: {self.batch_id}")
        report.append(f" Models Analyzed: {len(model_performance)}")
        report.append(f" Total Responses: {len(responses)}")
        report.append(f" Total Evaluations: {len(evaluations)}")
        report.append("")
        
        # Overall Rankings
        report.append("🏆 OVERALL MODEL RANKINGS")
        report.append("=" * 50)
        for i, (model_name, overall_score, perf) in enumerate(rankings):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1:2d}."
            report.append(f"{medal} {model_name:<45} | {overall_score:.2f}/5.0")
            report.append(f"    Responses: {perf['response_count']}/45 | Evaluations: {perf['evaluation_count']}")
        report.append("")
        
        # Criterion Leaders
        report.append("🎯 CRITERION LEADERS")
        report.append("=" * 50)
        criteria_order = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                         'visual_imagination', 'conceptual_depth', 'adaptability']
        
        for criterion in criteria_order:
            if criterion in criterion_leaders:
                best_model, best_score = criterion_leaders[criterion]['best']
                report.append(f"🏅 {criterion.replace('_', ' ').title():<20} | {best_model:<30} ({best_score:.2f})")
        report.append("")
        
        # Model Strengths and Weaknesses
        report.append("💪 MODEL STRENGTHS & WEAKNESSES")
        report.append("=" * 80)
        
        for model_name, overall_score, perf in rankings[:8]:  # Top 8 models
            insights = model_insights.get(model_name, {})
            report.append(f"\n🤖 {model_name}")
            report.append(f"   Overall Score: {overall_score:.2f}/5.0 (Rank #{insights.get('overall_rank', 'N/A')})")
            
            if insights.get('strengths'):
                report.append("   ✅ Strengths:")
                for criterion, score, rank in insights['strengths']:
                    report.append(f"      • {criterion.replace('_', ' ').title()}: {score:.2f} (#{rank})")
            
            if insights.get('weaknesses'):
                report.append("   ❌ Weaknesses:")
                for criterion, score, rank in insights['weaknesses']:
                    report.append(f"      • {criterion.replace('_', ' ').title()}: {score:.2f} (#{rank})")
            
            # Suggested use cases
            strengths = [s[0] for s in insights.get('strengths', [])]
            if 'creativity' in strengths and 'visual_imagination' in strengths:
                report.append("   🎯 Best for: Creative brainstorming, visual storytelling")
            elif 'coherence' in strengths and 'character_depth' in strengths:
                report.append("   🎯 Best for: Character development, narrative consistency")
            elif 'dialogue_quality' in strengths:
                report.append("   🎯 Best for: Screenplay writing, character interactions")
            elif 'conceptual_depth' in strengths:
                report.append("   🎯 Best for: Complex themes, philosophical content")
        
        # Sequence Analysis
        report.append(f"\n📝 PERFORMANCE BY CREATIVE SEQUENCE")
        report.append("=" * 80)
        
        for sequence_name, seq_perf in sequence_performance.items():
            report.append(f"\n📖 {sequence_name}")
            if seq_perf['best_model']:
                best_name, best_score = seq_perf['best_model']
                report.append(f"   🥇 Best: {best_name} ({best_score:.2f})")
            
            # Top 3 for this sequence
            sorted_models = sorted(seq_perf['model_rankings'].items(), key=lambda x: x[1], reverse=True)
            report.append("   Top performers:")
            for i, (model, score) in enumerate(sorted_models[:3]):
                medal = ["🥇", "🥈", "🥉"][i]
                report.append(f"      {medal} {model}: {score:.2f}")
        
        # Provider Analysis
        report.append(f"\n🏢 ANALYSIS BY API PROVIDER")
        report.append("=" * 50)
        
        provider_performance = defaultdict(list)
        for model_name, overall_score, perf in rankings:
            # Extract provider from model name or settings
            if 'claude' in model_name.lower():
                provider = 'Anthropic'
            elif 'gpt' in model_name.lower() or 'o4' in model_name.lower():
                provider = 'OpenAI'
            elif 'gemini' in model_name.lower():
                provider = 'Google'
            elif any(x in model_name.lower() for x in ['qwen', 'llama', 'deepseek']):
                provider = 'Deepinfra'
            else:
                provider = 'Unknown'
            
            provider_performance[provider].append((model_name, overall_score))
        
        for provider, models in provider_performance.items():
            if models:
                avg_score = statistics.mean([score for _, score in models])
                best_model = max(models, key=lambda x: x[1])
                report.append(f"\n🏢 {provider}")
                report.append(f"   Average Score: {avg_score:.2f}")
                report.append(f"   Best Model: {best_model[0]} ({best_model[1]:.2f})")
                report.append(f"   Models Tested: {len(models)}")
        
        # Key Insights
        report.append(f"\n🔍 KEY INSIGHTS")
        report.append("=" * 50)
        
        if rankings:
            top_model = rankings[0][0]
            top_score = rankings[0][1]
            bottom_model = rankings[-1][0] if len(rankings) > 1 else "N/A"
            bottom_score = rankings[-1][1] if len(rankings) > 1 else 0
            
            report.append(f"• Top performer: {top_model} ({top_score:.2f}/5.0)")
            if len(rankings) > 1:
                report.append(f"• Lowest performer: {bottom_model} ({bottom_score:.2f}/5.0)")
                report.append(f"• Performance spread: {top_score - bottom_score:.2f} points")
            
            # Find most consistent model (lowest std dev across criteria)
            most_consistent = None
            lowest_variance = float('inf')
            
            for model_name, overall_score, perf in rankings:
                criterion_scores = []
                for criterion_data in perf['criterion_scores'].values():
                    criterion_scores.append(criterion_data['average'])
                
                if len(criterion_scores) > 1:
                    variance = statistics.variance(criterion_scores)
                    if variance < lowest_variance:
                        lowest_variance = variance
                        most_consistent = model_name
            
            if most_consistent:
                report.append(f"• Most consistent: {most_consistent} (lowest variance across criteria)")
        
        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS")
        report.append("=" * 50)
        
        if rankings:
            # Creative tasks
            creative_leaders = []
            for model_name, _, perf in rankings:
                creativity_score = perf['criterion_scores'].get('creativity', {}).get('average', 0)
                visual_score = perf['criterion_scores'].get('visual_imagination', {}).get('average', 0)
                creative_avg = (creativity_score + visual_score) / 2 if creativity_score and visual_score else 0
                if creative_avg > 0:
                    creative_leaders.append((model_name, creative_avg))
            
            creative_leaders.sort(key=lambda x: x[1], reverse=True)
            
            if creative_leaders:
                report.append(f"🎨 For Creative Writing:")
                for i, (model, score) in enumerate(creative_leaders[:3]):
                    report.append(f"   {i+1}. {model} (creativity + visual: {score:.2f})")
            
            # Technical writing
            technical_leaders = []
            for model_name, _, perf in rankings:
                coherence_score = perf['criterion_scores'].get('coherence', {}).get('average', 0)
                conceptual_score = perf['criterion_scores'].get('conceptual_depth', {}).get('average', 0)
                technical_avg = (coherence_score + conceptual_score) / 2 if coherence_score and conceptual_score else 0
                if technical_avg > 0:
                    technical_leaders.append((model_name, technical_avg))
            
            technical_leaders.sort(key=lambda x: x[1], reverse=True)
            
            if technical_leaders:
                report.append(f"\n📚 For Technical/Analytical Writing:")
                for i, (model, score) in enumerate(technical_leaders[:3]):
                    report.append(f"   {i+1}. {model} (coherence + depth: {score:.2f})")
        
        report.append("\n" + "=" * 80)
        report.append(" End of Report")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    
    def save_report(self, report: str, filename: str = None):
        """Save report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"storybench_analysis_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Report saved to: {filename}")
        return filename
    
    
    def close(self):
        """Close database connection."""
        self.client.close()


def main():
    try:
        analyzer = StorybenchAnalyzer()
        report = analyzer.generate_report()
        
        # Print report to console
        print(report)
        
        # Save to file
        filename = analyzer.save_report(report)
        
        analyzer.close()
        return filename
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
response['text'])
    
    # Calculate averages and create model performance data
    model_performance = {}
    
    for model_name, stats in model_stats.items():
        if stats['total_responses'] == 0:
            continue
        
        perf = {
            'model_name': model_name,
            'responses': stats['total_responses'],
            'evaluations': stats['total_evaluations'],
            'avg_length': stats['total_chars'] / stats['total_responses'],
            'criterion_averages': {},
            'overall_average': 0
        }
        
        # Calculate criterion averages
        criterion_scores = []
        for criterion, scores in stats['scores'].items():
            if scores:
                avg = statistics.mean(scores)
                perf['criterion_averages'][criterion] = {
                    'average': round(avg, 2),
                    'count': len(scores),
                    'min': min(scores),
                    'max': max(scores)
                }
                criterion_scores.append(avg)
        
        # Overall average
        if criterion_scores:
            perf['overall_average'] = round(statistics.mean(criterion_scores), 2)
        
        model_performance[model_name] = perf
    
    # Sort models by overall performance
    rankings = sorted(model_performance.items(), key=lambda x: x[1]['overall_average'], reverse=True)
    
    # Generate report
    report = []
    report.append("=" * 80)
    report.append(" STORYBENCH MODEL PERFORMANCE ANALYSIS")
    report.append("=" * 80)
    report.append(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f" Test Batch: {batch_id}")
    report.append(f" Total Responses: {len(responses)}")
    report.append(f" Total Evaluations: {len(evaluations)}")
    report.append(f" Parsed Evaluations: {parsed_evaluations}")
    report.append("")
    
    # Overall Rankings
    report.append("🏆 OVERALL MODEL RANKINGS")
    report.append("=" * 60)
    
    for i, (model_name, perf) in enumerate(rankings):
        if perf['overall_average'] > 0:
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1:2d}."
            report.append(f"{medal} {model_name:<50} {perf['overall_average']:.2f}/5.0")
            report.append(f"    Responses: {perf['responses']}/45 | Evaluations: {perf['evaluations']}")
    
    report.append("")
    
    # Detailed Model Analysis
    report.append("📊 DETAILED MODEL ANALYSIS")
    report.append("=" * 60)
    
    criteria_names = {
        'creativity': 'Creativity',
        'coherence': 'Coherence', 
        'character_depth': 'Character Depth',
        'dialogue_quality': 'Dialogue Quality',
        'visual_imagination': 'Visual Imagination',
        'conceptual_depth': 'Conceptual Depth',
        'adaptability': 'Adaptability'
    }
    
    for i, (model_name, perf) in enumerate(rankings[:8]):  # Top 8 models
        if perf['overall_average'] == 0:
            continue
            
        report.append(f"\n🤖 #{i+1} {model_name}")
        report.append(f"   Overall Score: {perf['overall_average']:.2f}/5.0")
        report.append(f"   Avg Response Length: {perf['avg_length']:.0f} characters")
        report.append("   Criterion Scores:")
        
        # Sort criteria by score for this model
        criterion_items = [(crit, data) for crit, data in perf['criterion_averages'].items()]
        criterion_items.sort(key=lambda x: x[1]['average'], reverse=True)
        
        for criterion, data in criterion_items:
            display_name = criteria_names.get(criterion, criterion.replace('_', ' ').title())
            report.append(f"      {display_name:<18}: {data['average']:.2f} ({data['count']} evaluations)")
    
    # Find best in each category
    report.append(f"\n🎯 CATEGORY LEADERS")
    report.append("=" * 60)
    
    category_leaders = {}
    for criterion in criteria_names.keys():
        best_model = None
        best_score = 0
        
        for model_name, perf in model_performance.items():
            if criterion in perf['criterion_averages']:
                score = perf['criterion_averages'][criterion]['average']
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        if best_model:
            category_leaders[criterion] = (best_model, best_score)
            display_name = criteria_names[criterion]
            report.append(f"🏅 {display_name:<18}: {best_model} ({best_score:.2f})")
    
    # Provider Analysis
    report.append(f"\n🏢 PROVIDER ANALYSIS")
    report.append("=" * 60)
    
    providers = {
        'Anthropic': [],
        'OpenAI': [],
        'Google': [],
        'Deepinfra': []
    }
    
    for model_name, perf in model_performance.items():
        if 'claude' in model_name.lower():
            providers['Anthropic'].append((model_name, perf['overall_average']))
        elif 'gpt' in model_name.lower() or 'o4' in model_name.lower():
            providers['OpenAI'].append((model_name, perf['overall_average']))
        elif 'gemini' in model_name.lower():
            providers['Google'].append((model_name, perf['overall_average']))
        else:
            providers['Deepinfra'].append((model_name, perf['overall_average']))
    
    for provider, models in providers.items():
        if models:
            avg_score = statistics.mean([score for _, score in models if score > 0])
            best_model = max(models, key=lambda x: x[1])
            models.sort(key=lambda x: x[1], reverse=True)
            
            report.append(f"\n🏢 {provider}")
            report.append(f"   Average Score: {avg_score:.2f}")
            report.append(f"   Best Model: {best_model[0]} ({best_model[1]:.2f})")
            report.append("   All Models:")
            for model, score in models:
                if score > 0:
                    report.append(f"      • {model}: {score:.2f}")
    
    # Recommendations
    report.append(f"\n💡 RECOMMENDATIONS")
    report.append("=" * 60)
    
    if rankings:
        top_3 = [model for model, perf in rankings[:3] if perf['overall_average'] > 0]
        
        report.append("🎯 Best Overall Models:")
        for i, model in enumerate(top_3):
            perf = model_performance[model]
            report.append(f"   {i+1}. {model} ({perf['overall_average']:.2f}/5.0)")
        
        # Specialized recommendations
        report.append(f"\n🎨 Best for Creative Writing:")
        creative_models = []
        for model_name, perf in model_performance.items():
            creativity = perf['criterion_averages'].get('creativity', {}).get('average', 0)
            visual = perf['criterion_averages'].get('visual_imagination', {}).get('average', 0)
            if creativity > 0 and visual > 0:
                creative_score = (creativity + visual) / 2
                creative_models.append((model_name, creative_score))
        
        creative_models.sort(key=lambda x: x[1], reverse=True)
        for i, (model, score) in enumerate(creative_models[:3]):
            report.append(f"   {i+1}. {model} (avg creative score: {score:.2f})")
        
        report.append(f"\n📚 Best for Technical Writing:")
        technical_models = []
        for model_name, perf in model_performance.items():
            coherence = perf['criterion_averages'].get('coherence', {}).get('average', 0)
            depth = perf['criterion_averages'].get('conceptual_depth', {}).get('average', 0)
            if coherence > 0 and depth > 0:
                technical_score = (coherence + depth) / 2
                technical_models.append((model_name, technical_score))
        
        technical_models.sort(key=lambda x: x[1], reverse=True)
        for i, (model, score) in enumerate(technical_models[:3]):
            report.append(f"   {i+1}. {model} (avg technical score: {score:.2f})")
    
    # Key Insights
    report.append(f"\n🔍 KEY INSIGHTS")
    report.append("=" * 60)
    
    if rankings:
        top_model = rankings[0][0]
        top_score = rankings[0][1]['overall_average']
        
        report.append(f"• Best Overall: {top_model} ({top_score:.2f}/5.0)")
        
        if len(rankings) > 1:
            bottom_model = rankings[-1][0]
            bottom_score = rankings[-1][1]['overall_average']
            if bottom_score > 0:
                report.append(f"• Lowest Scorer: {bottom_model} ({bottom_score:.2f}/5.0)")
                report.append(f"• Score Range: {top_score - bottom_score:.2f} points")
        
        # Most consistent performer
        consistency_scores = []
        for model_name, perf in model_performance.items():
            if len(perf['criterion_averages']) >= 5:  # Has scores for most criteria
                scores = [data['average'] for data in perf['criterion_averages'].values()]
                if len(scores) > 1:
                    consistency = statistics.stdev(scores)  # Lower is more consistent
                    consistency_scores.append((model_name, consistency, statistics.mean(scores)))
        
        if consistency_scores:
            # Sort by consistency (low std dev) among high performers
            high_performers = [(m, c, a) for m, c, a in consistency_scores if a >= 3.5]
            if high_performers:
                most_consistent = min(high_performers, key=lambda x: x[1])
                report.append(f"• Most Consistent High Performer: {most_consistent[0]} (std dev: {most_consistent[1]:.2f})")
    
    report.append("\n" + "=" * 80)
    report.append(" END OF ANALYSIS")
    report.append("=" * 80)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"storybench_analysis_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n📄 Report saved to: {filename}")
    
    # Print to console
    for line in report:
        print(line)
    
    client.close()
    return filename

if __name__ == "__main__":
    generate_simple_report()
