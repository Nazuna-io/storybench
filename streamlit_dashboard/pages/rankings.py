"""
Model Rankings page for StoryBench dashboard
Interactive radar charts and detailed model comparison
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from math import pi
import sys
from pathlib import Path

# Add parent directory to path to import data_service
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from data_service import DataService

def create_radar_chart(model_scores, model_name):
    """Create a radar chart for a single model."""
    criteria = list(model_scores.index)
    values = list(model_scores.values)
    
    # Close the radar chart by repeating first value
    criteria_closed = criteria + [criteria[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=criteria_closed,
        fill='toself',
        name=model_name,
        line=dict(width=2),
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[1, 5],
                tickvals=[1, 2, 3, 4, 5]
            )
        ),
        showlegend=True,
        title=f"Performance Profile: {model_name}",
        height=400
    )
    
    return fig

def create_comparison_radar(model_scores_dict, selected_models):
    """Create comparison radar chart for multiple models."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, model in enumerate(selected_models):
        if model in model_scores_dict:
            scores = model_scores_dict[model]
            criteria = list(scores.index)
            values = list(scores.values)
            
            # Close the radar chart
            criteria_closed = criteria + [criteria[0]]
            values_closed = values + [values[0]]
            
            color = colors[i % len(colors)]
            
            fig.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=criteria_closed,
                fill='toself',
                name=model,
                line=dict(width=2, color=color),
                fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.1)')
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[1, 5],
                tickvals=[1, 2, 3, 4, 5]
            )
        ),
        showlegend=True,
        title="Model Comparison",
        height=500
    )
    
    return fig

def show():
    """Display the rankings page."""
    st.header("🏆 Model Rankings")
    
    # Initialize data service
    data_service = DataService()
    
    # Get performance data
    performance_df = data_service.get_model_performance_data()
    
    if performance_df.empty:
        st.warning("No performance data available. Please run evaluations first.")
        return
    
    # Get available criteria
    criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                    'visual_imagination', 'conceptual_depth', 'adaptability']
    available_criteria = [col for col in criteria_cols if col in performance_df.columns]
    
    if not available_criteria:
        st.error("No evaluation criteria found in the data.")
        return
    
    # Calculate average scores by model
    model_avg_scores = performance_df.groupby('model')[available_criteria].mean()
    model_avg_scores['overall_score'] = model_avg_scores[available_criteria].mean(axis=1)
    model_avg_scores = model_avg_scores.sort_values('overall_score', ascending=False)
    
    # Rankings table
    st.subheader("Overall Rankings")
    
    # Create rankings display
    rankings_data = []
    for rank, (model, scores) in enumerate(model_avg_scores.iterrows(), 1):
        rankings_data.append({
            'Rank': rank,
            'Model': model,
            'Overall Score': f"{scores['overall_score']:.2f}",
            'Response Count': len(performance_df[performance_df['model'] == model])
        })
    
    rankings_df = pd.DataFrame(rankings_data)
    st.dataframe(rankings_df, use_container_width=True)
    
    # Model selection for detailed analysis
    st.subheader("Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Individual Model Analysis**")
        selected_model = st.selectbox(
            "Select a model for detailed view:",
            options=model_avg_scores.index.tolist(),
            key="individual_model"
        )
        
        if selected_model:
            model_scores = model_avg_scores.loc[selected_model, available_criteria]
            fig = create_radar_chart(model_scores, selected_model)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Model Comparison**")
        selected_models = st.multiselect(
            "Select models to compare (max 4):",
            options=model_avg_scores.index.tolist(),
            default=model_avg_scores.index.tolist()[:3],
            max_selections=4,
            key="comparison_models"
        )
        
        if selected_models:
            model_scores_dict = {model: model_avg_scores.loc[model, available_criteria] 
                               for model in selected_models}
            fig = create_comparison_radar(model_scores_dict, selected_models)
            st.plotly_chart(fig, use_container_width=True)
    
    # Criteria breakdown
    st.subheader("Criteria Breakdown")
    
    # Create criteria comparison chart
    criteria_df = model_avg_scores[available_criteria].reset_index()
    criteria_melted = criteria_df.melt(
        id_vars=['model'], 
        value_vars=available_criteria,
        var_name='Criterion', 
        value_name='Score'
    )
    
    fig = px.box(
        criteria_melted, 
        x='Criterion', 
        y='Score',
        title="Score Distribution by Criterion",
        points="all"
    )
    fig.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistical summary
    st.subheader("Statistical Summary")
    
    summary_stats = model_avg_scores[available_criteria].describe()
    st.dataframe(summary_stats.round(3), use_container_width=True)
    
    # Performance insights
    st.subheader("Key Insights")
    
    # Find best and worst performing criteria overall
    overall_criterion_means = model_avg_scores[available_criteria].mean()
    best_criterion = overall_criterion_means.idxmax()
    worst_criterion = overall_criterion_means.idxmin()
    
    # Find most consistent and variable criteria
    criterion_stds = model_avg_scores[available_criteria].std()
    most_consistent = criterion_stds.idxmin()
    most_variable = criterion_stds.idxmax()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Highest Scoring Criterion",
            best_criterion.replace('_', ' ').title(),
            f"{overall_criterion_means[best_criterion]:.2f} avg"
        )
        st.metric(
            "Most Consistent Criterion",
            most_consistent.replace('_', ' ').title(),
            f"{criterion_stds[most_consistent]:.3f} std dev"
        )
    
    with col2:
        st.metric(
            "Lowest Scoring Criterion", 
            worst_criterion.replace('_', ' ').title(),
            f"{overall_criterion_means[worst_criterion]:.2f} avg"
        )
        st.metric(
            "Most Variable Criterion",
            most_variable.replace('_', ' ').title(),
            f"{criterion_stds[most_variable]:.3f} std dev"
        )
