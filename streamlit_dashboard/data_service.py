"""
Data service for StoryBench dashboard
Handles MongoDB connections and data processing
"""

import os
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pymongo import MongoClient
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DataService:
    """Handles data access and processing for the dashboard."""
    
    def __init__(self):
        self._client = None
        self._db = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB."""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                st.error("MONGODB_URI not found in environment variables")
                return
            
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
            self._db = self._client['storybench']
            
            # Test connection
            self._client.admin.command('ping')
            
        except Exception as e:
            st.error(f"Failed to connect to MongoDB: {e}")
            self._client = None
            self._db = None
    
    def get_database_stats(self) -> Dict:
        """Get basic database statistics."""
        if self._db is None:
            return {}
        
        try:
            stats = {}
            
            # Get response counts
            responses = list(self._db.responses.find())
            stats['total_responses'] = len(responses)
            
            # Get unique models
            models = set(r.get('model_name') for r in responses if r.get('model_name'))
            stats['unique_models'] = len(models)
            stats['models'] = sorted(list(models))
            
            # Get evaluations
            evaluations = list(self._db.response_llm_evaluations.find())
            stats['total_evaluations'] = len(evaluations)
            
            # Get model counts
            model_counts = {}
            for response in responses:
                model = response.get('model_name')
                if model:
                    model_counts[model] = model_counts.get(model, 0) + 1
            stats['model_counts'] = model_counts
            
            # Get latest evaluation date
            if evaluations:
                latest_eval = max(evaluations, key=lambda x: x.get('created_at', datetime.min))
                stats['latest_evaluation'] = latest_eval.get('created_at')
            
            return stats
            
        except Exception as e:
            st.error(f"Error getting database stats: {e}")
            return {}
    
    def extract_scores_from_evaluation(self, evaluation_text: str = None, eval_doc: dict = None) -> Dict[str, float]:
        """Extract numerical scores from evaluation text or structured criteria_results."""
        scores = {}
        
        # New format: structured criteria_results (preferred)
        if eval_doc and 'criteria_results' in eval_doc:
            for criterion_eval in eval_doc['criteria_results']:
                criterion_name = criterion_eval.get('criterion_name')
                score = criterion_eval.get('score')
                if criterion_name and score is not None:
                    scores[criterion_name] = float(score)
            return scores
        
        # Old format: parse from evaluation_text (fallback)
        if not evaluation_text:
            return scores
            
        criteria = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                   'visual_imagination', 'conceptual_depth', 'adaptability']
        
        text_lower = evaluation_text.lower()
        
        for criterion in criteria:
            # Look for "**criterion**: X" or "criterion: X" patterns
            patterns = [
                rf'\*\*{criterion}\*\*\s*:\s*([1-5](?:\.\d)?)',
                rf'{criterion}\s*:\s*([1-5](?:\.\d)?)',
                rf'{criterion}\s*-\s*([1-5](?:\.\d)?)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    try:
                        score = float(matches[0])
                        if 1 <= score <= 5:
                            scores[criterion] = score
                            break
                    except ValueError:
                        continue
        
        return scores
    
    def get_model_performance_data(self) -> pd.DataFrame:
        """Get model performance data with extracted scores."""
        if self._db is None:
            return pd.DataFrame()
        
        try:
            # Get responses and evaluations
            responses = list(self._db.responses.find())
            evaluations = list(self._db.response_llm_evaluations.find())
            
            # Create mapping of response_id to evaluation
            eval_map = {}
            for eval_doc in evaluations:
                response_id = eval_doc.get('response_id')
                if response_id:
                    eval_map[str(response_id)] = eval_doc
            
            # Process data
            performance_data = []
            
            for response in responses:
                response_id = str(response.get('_id'))
                model_name = response.get('model_name')
                
                if not model_name or response_id not in eval_map:
                    continue
                
                eval_doc = eval_map[response_id]
                evaluation_text = eval_doc.get('evaluation_text', '')
                
                # Use new extraction method that handles both formats
                scores = self.extract_scores_from_evaluation(evaluation_text, eval_doc)
                
                if scores:  # Only include if we extracted scores
                    row = {
                        'model': model_name,
                        'response_id': response_id,
                        'prompt_name': response.get('prompt_name'),
                        'sequence_name': response.get('sequence_name'),
                        'created_at': response.get('created_at'),
                        'evaluating_model': eval_doc.get('evaluating_llm_model'),
                        **scores
                    }
                    performance_data.append(row)
            
            return pd.DataFrame(performance_data)
            
        except Exception as e:
            st.error(f"Error getting performance data: {e}")
            return pd.DataFrame()
