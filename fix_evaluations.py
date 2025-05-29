#!/usr/bin/env python3
"""
Fix Storybench Evaluation Issues
===============================
1. Remove duplicate evaluations (keeping most recent)
2. Improve score extraction and re-run analysis
"""

import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime

def cleanup_duplicate_evaluations():
    """Remove duplicate evaluations, keeping the most recent."""
    
    client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=30000)
    db = client['storybench']
    
    # Get latest batch
    latest_response = db.responses.find({'test_run': True}).sort('created_at', -1).limit(1)
    batch_id = None
    for doc in latest_response:
        batch_id = doc['test_batch']
        break
    
    print(f"🧹 Cleaning duplicates for batch: {batch_id}")
    
    # Find all evaluations for this batch
    evaluations = list(db.response_llm_evaluations.find({'test_batch': batch_id}))
    print(f"Found {len(evaluations)} total evaluations")
    
    # Group by response_id
    response_groups = defaultdict(list)
    for eval_doc in evaluations:
        response_id = str(eval_doc['response_id'])
        response_groups[response_id].append(eval_doc)
    
    # Find duplicates and keep most recent
    duplicates_found = 0
    removed_count = 0
    
    for response_id, eval_list in response_groups.items():
        if len(eval_list) > 1:
            duplicates_found += 1
            
            # Sort by created_at, keep most recent
            eval_list.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Remove all but the first (most recent)
            for eval_doc in eval_list[1:]:
                db.response_llm_evaluations.delete_one({'_id': eval_doc['_id']})
                removed_count += 1
    
    print(f"✅ Cleanup complete:")
    print(f"   Responses with duplicates: {duplicates_found}")
    print(f"   Duplicate evaluations removed: {removed_count}")
    
    # Verify cleanup
    remaining = db.response_llm_evaluations.count_documents({'test_batch': batch_id})
    print(f"   Remaining evaluations: {remaining}")
    
    client.close()
    return removed_count

def improved_score_extraction(text):
    """Improved score extraction with multiple parsing strategies."""
    import re
    
    scores = {}
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    # Clean up text
    text_lower = text.lower()
    
    for criterion in criteria:
        score_found = False
        
        # Strategy 1: Look for "criterion: score" patterns
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
        
        # Strategy 2: Look for criterion in context with nearby numbers
        if not score_found:
            # Find the criterion and look for numbers nearby
            criterion_pos = text_lower.find(criterion)
            if criterion_pos >= 0:
                # Look in a 100-character window around the criterion
                start = max(0, criterion_pos - 50)
                end = min(len(text_lower), criterion_pos + 50)
                context = text_lower[start:end]
                
                # Find all numbers in context
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

def test_improved_extraction():
    """Test the improved extraction on actual evaluation data."""
    
    client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=30000)
    db = client['storybench']
    
    # Get latest batch
    latest_response = db.responses.find({'test_run': True}).sort('created_at', -1).limit(1)
    batch_id = None
    for doc in latest_response:
        batch_id = doc['test_batch']
        break
    
    print(f"🧪 Testing improved extraction on batch: {batch_id}")
    
    # Sample a few evaluations
    evaluations = list(db.response_llm_evaluations.find({'test_batch': batch_id}).limit(10))
    
    old_extraction_success = 0
    new_extraction_success = 0
    
    for eval_doc in evaluations:
        text = eval_doc['evaluation_text']
        
        # Old method (simple)
        old_scores = simple_extract_scores(text)
        
        # New method
        new_scores = improved_score_extraction(text)
        
        if old_scores:
            old_extraction_success += 1
        if new_scores:
            new_extraction_success += 1
        
        if len(new_scores) > len(old_scores):
            print(f"✅ Improved extraction found {len(new_scores)} vs {len(old_scores)} scores")
    
    print(f"📊 Extraction test results:")
    print(f"   Old method success: {old_extraction_success}/10")
    print(f"   New method success: {new_extraction_success}/10")
    
    client.close()

def simple_extract_scores(text):
    """Simple extraction method for comparison."""
    import re
    scores = {}
    criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
               'visual_imagination', 'conceptual_depth', 'adaptability']
    
    text_lower = text.lower()
    
    for criterion in criteria:
        pattern = rf'{criterion}[:\s-]+([1-5](?:\.\d)?)'
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                score = float(matches[0])
                if 1 <= score <= 5:
                    scores[criterion] = score
            except ValueError:
                continue
    
    return scores

if __name__ == "__main__":
    print("🔧 FIXING STORYBENCH EVALUATION ISSUES")
    print("=" * 50)
    
    # Step 1: Clean up duplicates
    removed = cleanup_duplicate_evaluations()
    
    # Step 2: Test improved extraction
    print(f"\\n🧪 TESTING IMPROVED SCORE EXTRACTION")
    print("=" * 50)
    test_improved_extraction()
    
    print(f"\\n✅ READY FOR RE-ANALYSIS")
    print("=" * 50)
    print("Next steps:")
    print("1. ✅ Removed duplicate evaluations")
    print("2. 🧪 Tested improved score extraction")
    print("3. 🚀 Ready to re-run analysis with better parsing")
