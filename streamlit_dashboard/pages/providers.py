"""
Provider Comparison page for StoryBench dashboard
Compare performance by company (Anthropic, OpenAI, Google, etc.)
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

def extract_provider_from_model(model_name):
    """Extract provider name from model name."""
    model_lower = model_name.lower()
    
    if 'claude' in model_lower:
        return 'Anthropic'
    elif any(x in model_lower for x in ['gpt', 'o4-', 'o1-']):
        return 'OpenAI'
    elif 'gemini' in model_lower:
        return 'Google'
    elif any(x in model_lower for x in ['deepseek', 'qwen', 'llama']):
        return 'DeepInfra'
    else:
        return 'Unknown'

def create_provider_comparison_chart(performance_df):
    """Create comparison chart by provider."""
    criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                    'visual_imagination', 'conceptual_depth', 'adaptability']
    available_criteria = [col for col in criteria_cols if col in performance_df.columns]
    
    if not available_criteria:
        return None, None
    
    # Add provider column
    performance_df['provider'] = performance_df['model'].apply(extract_provider_from_model)
    
    # Calculate average scores by provider
    provider_scores = performance_df.groupby('provider')[available_criteria].mean()
    provider_scores['overall_score'] = provider_scores[available_criteria].mean(axis=1)
    provider_scores = provider_scores.sort_values('overall_score', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        x=provider_scores.index,
        y=provider_scores['overall_score'],
        title="Overall Performance by Provider",
        labels={'x': 'Provider', 'y': 'Average Score (1-5)'},
        color=provider_scores['overall_score'],
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(height=400)
    return fig, provider_scores
    st.subheader("🏆 Overall Performance Comparison")
    
    comparison_fig, provider_scores = create_provider_comparison_chart(performance_df)
    if comparison_fig:
        st.plotly_chart(comparison_fig, use_container_width=True)
    
    # Provider rankings table
    st.subheader("📋 Provider Rankings")
    
    rankings_data = []
    for rank, (provider, scores) in enumerate(provider_scores.iterrows(), 1):
        rankings_data.append({
            'Rank': rank,
            'Provider': provider,
            'Overall Score': f"{scores['overall_score']:.2f}",
            'Models': provider_stats.loc[provider, 'models'],
            'Responses': provider_stats.loc[provider, 'responses']
        })
    
    rankings_df = pd.DataFrame(rankings_data)
    st.dataframe(rankings_df, use_container_width=True)
    
    # Detailed analysis
    st.subheader("🔍 Detailed Analysis")
    
    # Provider selection for comparison
    available_providers = list(provider_scores.index)
    selected_providers = st.multiselect(
        "Select providers to compare:",
        available_providers,
        default=available_providers[:3] if len(available_providers) >= 3 else available_providers
    )
    
    if selected_providers:
        # Radar chart comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Provider Performance Radar**")
            radar_fig = create_provider_criteria_radar(provider_scores, selected_providers)
            if radar_fig:
                st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            st.write("**Criteria Breakdown**")
            for criterion in available_criteria:
                criterion_title = criterion.replace('_', ' ').title()
                st.write(f"**{criterion_title}:**")
                
                criterion_rankings = provider_scores[criterion].sort_values(ascending=False)
                for i, (provider, score) in enumerate(criterion_rankings.items(), 1):
                    if provider in selected_providers:
                        st.write(f"{i}. {provider}: {score:.2f}")
                st.write("")
    
    # Statistical comparison
    st.subheader("📈 Statistical Comparison")
    
    # Create comparison table
    comparison_stats = []
    for provider in available_providers:
        provider_data = performance_df[performance_df['provider'] == provider]
        
        if not provider_data.empty:
            stats = {
                'Provider': provider,
                'Models': len(provider_data['model'].unique()),
                'Total Responses': len(provider_data),
                'Avg Overall Score': provider_data[available_criteria].mean().mean(),
                'Score Std Dev': provider_data[available_criteria].values.flatten().std()
            }
            
            # Best and worst criteria
            criteria_means = provider_data[available_criteria].mean()
            stats['Best Criterion'] = criteria_means.idxmax().replace('_', ' ').title()
            stats['Best Score'] = criteria_means.max()
            stats['Worst Criterion'] = criteria_means.idxmin().replace('_', ' ').title()
            stats['Worst Score'] = criteria_means.min()
            
            comparison_stats.append(stats)
    
    if comparison_stats:
        comparison_df = pd.DataFrame(comparison_stats)
        comparison_df = comparison_df.round(3)
        st.dataframe(comparison_df, use_container_width=True)
    
    # Market insights
    st.subheader("💡 Market Insights")
    
    if len(available_providers) > 1:
        insights = []
        
        # Market share by responses
        market_share = performance_df['provider'].value_counts(normalize=True) * 100
        dominant_provider = market_share.index[0]
        insights.append(f"**Market Presence**: {dominant_provider} leads with {market_share.iloc[0]:.1f}% of evaluated responses")
        
        # Performance leader
        performance_leader = provider_scores.index[0]
        top_score = provider_scores.iloc[0]['overall_score']
        insights.append(f"**Performance Leader**: {performance_leader} with {top_score:.2f}/5.0 average score")
        
        # Diversity
        model_diversity = provider_stats['models'].to_dict()
        most_diverse = max(model_diversity.items(), key=lambda x: x[1])
        insights.append(f"**Model Diversity**: {most_diverse[0]} offers {most_diverse[1]} different models")
        
        for insight in insights:
            st.write(f"• {insight}")
