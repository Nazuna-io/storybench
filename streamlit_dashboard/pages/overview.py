"""
Overview page for StoryBench dashboard
Shows key metrics and top performing models
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import data_service
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from data_service import DataService

def show():
    """Display the overview page."""
    st.header("📊 Overview")
    
    # Initialize data service
    data_service = DataService()
    
    # Get basic stats
    stats = data_service.get_database_stats()
    
    if not stats:
        st.error("Unable to load data. Please check your database connection.")
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Responses",
            value=f"{stats.get('total_responses', 0):,}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Models Evaluated", 
            value=stats.get('unique_models', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            label="LLM Evaluations",
            value=f"{stats.get('total_evaluations', 0):,}",
            delta=None
        )
    
    with col4:
        latest_eval = stats.get('latest_evaluation')
        if latest_eval:
            days_ago = (datetime.now() - latest_eval).days
            st.metric(
                label="Last Evaluation",
                value=f"{days_ago} days ago",
                delta=None
            )
        else:
            st.metric(label="Last Evaluation", value="N/A", delta=None)
    
    # Model response counts chart
    st.subheader("Model Response Counts")
    
    model_counts = stats.get('model_counts', {})
    if model_counts:
        # Create DataFrame for plotting
        model_df = pd.DataFrame([
            {'Model': model, 'Responses': count}
            for model, count in model_counts.items()
        ]).sort_values('Responses', ascending=True)
        
        # Create horizontal bar chart
        fig = px.bar(
            model_df, 
            x='Responses', 
            y='Model',
            orientation='h',
            title="Response Count by Model",
            color='Responses',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Top performers section
    st.subheader("Top Performing Models")
    
    # Get performance data
    performance_df = data_service.get_model_performance_data()
    
    if not performance_df.empty:
        # Calculate average scores by model
        criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                        'visual_imagination', 'conceptual_depth', 'adaptability']
        
        available_criteria = [col for col in criteria_cols if col in performance_df.columns]
        
        if available_criteria:
            # Calculate average scores
            model_avg_scores = performance_df.groupby('model')[available_criteria].mean()
            model_avg_scores['overall_score'] = model_avg_scores[available_criteria].mean(axis=1)
            model_avg_scores = model_avg_scores.sort_values('overall_score', ascending=False)
            
            # Display top 5 models
            st.write("**Top 5 Models by Overall Score:**")
            
            top_5 = model_avg_scores.head().reset_index()
            for idx, row in top_5.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{idx + 1}. {row['model']}**")
                    with col2:
                        st.metric(
                            label="Avg Score",
                            value=f"{row['overall_score']:.2f}/5.0"
                        )
        
        # Evaluation progress info
        st.subheader("Evaluation Coverage")
        
        total_possible = stats.get('total_responses', 0) * len(available_criteria)
        total_actual = len(performance_df) * len(available_criteria)
        coverage_pct = (total_actual / total_possible * 100) if total_possible > 0 else 0
        
        st.metric(
            label="Evaluation Coverage",
            value=f"{coverage_pct:.1f}%",
            delta=f"{total_actual:,} of {total_possible:,} possible evaluations"
        )
        
    else:
        st.info("No evaluation data available yet. Run evaluations to see performance metrics.")
