"""
Criteria Analysis page for StoryBench dashboard
Box plots, heatmaps, and detailed analysis of evaluation criteria
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path to import data_service
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from data_service import DataService

def create_criteria_heatmap(performance_df):
    """Create a heatmap showing model performance across criteria."""
    criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                    'visual_imagination', 'conceptual_depth', 'adaptability']
    available_criteria = [col for col in criteria_cols if col in performance_df.columns]
    
    if not available_criteria:
        return None
    
    # Calculate average scores by model for each criterion
    heatmap_data = performance_df.groupby('model')[available_criteria].mean()
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[col.replace('_', ' ').title() for col in heatmap_data.columns],
        y=heatmap_data.index,
        colorscale='RdYlBu',
        colorbar=dict(title="Score (1-5)"),
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>%{x}: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Model Performance Heatmap Across Criteria",
        xaxis_title="Evaluation Criteria",
        yaxis_title="Models",
        height=max(400, len(heatmap_data) * 30)
    )
    
    return fig

def create_criteria_distribution_plots(performance_df):
    """Create box plots for each criterion showing score distributions."""
    criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                    'visual_imagination', 'conceptual_depth', 'adaptability']
    available_criteria = [col for col in criteria_cols if col in performance_df.columns]
    
    if not available_criteria:
        return []
    
    figures = []
    
    for criterion in available_criteria:
        fig = px.box(
            performance_df, 
            x='model', 
            y=criterion,
            title=f"Score Distribution: {criterion.replace('_', ' ').title()}",
            points="all"
        )
        fig.update_layout(
            xaxis_title="Model",
            yaxis_title="Score (1-5)",
            xaxis_tickangle=-45,
            height=400
        )
        figures.append((criterion, fig))
    
    return figures

def analyze_criteria_correlations(performance_df):
    """Analyze correlations between different criteria."""
    criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                    'visual_imagination', 'conceptual_depth', 'adaptability']
    available_criteria = [col for col in criteria_cols if col in performance_df.columns]
    
    if len(available_criteria) < 2:
        return None
    
    correlation_matrix = performance_df[available_criteria].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=[col.replace('_', ' ').title() for col in correlation_matrix.columns],
        y=[col.replace('_', ' ').title() for col in correlation_matrix.index],
        colorscale='RdBu',
        zmid=0,
        colorbar=dict(title="Correlation"),
        hoverongaps=False,
        hovertemplate='<b>%{y}</b> vs <b>%{x}</b><br>Correlation: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Criteria Correlation Matrix",
        height=500
    )
    
    return fig

def show():
    """Display the criteria analysis page."""
    st.header("📈 Criteria Analysis")
    
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
    
    # Criteria summary statistics
    st.subheader("📊 Criteria Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Criteria",
            len(available_criteria),
            f"{len(available_criteria)}/7 available"
        )
    
    with col2:
        avg_overall = performance_df[available_criteria].mean().mean()
        st.metric(
            "Average Score",
            f"{avg_overall:.2f}/5.0",
            delta=None
        )
    
    with col3:
        total_evaluations = len(performance_df) * len(available_criteria)
        st.metric(
            "Total Criterion Evaluations",
            f"{total_evaluations:,}",
            delta=None
        )
    
    # Performance heatmap
    st.subheader("🔥 Performance Heatmap")
    heatmap_fig = create_criteria_heatmap(performance_df)
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Individual criteria analysis
    st.subheader("📋 Individual Criteria Analysis")
    
    # Criteria selector
    selected_criteria = st.multiselect(
        "Select criteria to analyze:",
        available_criteria,
        default=available_criteria[:3],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_criteria:
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Box Plots", "Statistical Summary", "Model Rankings"])
        
        with tab1:
            st.write("**Score Distribution by Model**")
            for criterion in selected_criteria:
                fig = px.box(
                    performance_df, 
                    x='model', 
                    y=criterion,
                    title=f"{criterion.replace('_', ' ').title()} - Score Distribution",
                    points="all"
                )
                fig.update_layout(
                    xaxis_tickangle=-45,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.write("**Statistical Summary**")
            summary_stats = performance_df[selected_criteria].describe()
            st.dataframe(summary_stats.round(3), use_container_width=True)
            
            # Criteria insights
            st.write("**Key Insights:**")
            for criterion in selected_criteria:
                criterion_data = performance_df[criterion]
                mean_score = criterion_data.mean()
                std_score = criterion_data.std()
                
                st.write(f"• **{criterion.replace('_', ' ').title()}**: Avg {mean_score:.2f} ± {std_score:.2f}")
        
        with tab3:
            st.write("**Top Models by Criterion**")
            for criterion in selected_criteria:
                criterion_rankings = performance_df.groupby('model')[criterion].mean().sort_values(ascending=False)
                
                st.write(f"**{criterion.replace('_', ' ').title()}**")
                for i, (model, score) in enumerate(criterion_rankings.head().items(), 1):
                    st.write(f"{i}. {model}: {score:.2f}")
                st.write("")
    
    # Correlation analysis
    st.subheader("🔗 Criteria Correlations")
    correlation_fig = analyze_criteria_correlations(performance_df)
    if correlation_fig:
        st.plotly_chart(correlation_fig, use_container_width=True)
        
        # Correlation insights
        criteria_df = performance_df[available_criteria]
        correlation_matrix = criteria_df.corr()
        
        # Find highest correlations (excluding diagonal)
        correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                correlations.append({
                    'Criteria Pair': f"{correlation_matrix.columns[i]} - {correlation_matrix.columns[j]}",
                    'Correlation': correlation_matrix.iloc[i, j]
                })
        
        correlations_df = pd.DataFrame(correlations).sort_values('Correlation', ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Highest Correlations:**")
            for _, row in correlations_df.head().iterrows():
                pair = row['Criteria Pair'].replace('_', ' ').title()
                corr = row['Correlation']
                st.write(f"• {pair}: {corr:.3f}")
        
        with col2:
            st.write("**Lowest Correlations:**")
            for _, row in correlations_df.tail().iterrows():
                pair = row['Criteria Pair'].replace('_', ' ').title()
                corr = row['Correlation']
                st.write(f"• {pair}: {corr:.3f}")
