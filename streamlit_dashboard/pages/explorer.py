"""
Data Explorer page for StoryBench dashboard
Interactive filtering and drill-down analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path to import data_service
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from data_service import DataService

def create_scatter_plot(df, x_col, y_col, color_col=None, size_col=None):
    """Create interactive scatter plot."""
    fig = px.scatter(
        df, 
        x=x_col, 
        y=y_col,
        color=color_col,
        size=size_col,
        hover_data=['model', 'prompt_name', 'sequence_name'],
        title=f"{y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}"
    )
    
    fig.update_layout(height=500)
    return fig

def filter_data(performance_df, filters):
    """Apply filters to the performance dataframe."""
    filtered_df = performance_df.copy()
    
    # Model filter
    if filters['models']:
        filtered_df = filtered_df[filtered_df['model'].isin(filters['models'])]
    
    # Date filter
    if filters['date_range'] and len(filters['date_range']) == 2:
        start_date, end_date = filters['date_range']
        if 'created_at' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['created_at'] >= pd.Timestamp(start_date)) &
                (filtered_df['created_at'] <= pd.Timestamp(end_date))
            ]
    
    # Score range filters
    criteria_cols = ['creativity', 'coherence', 'character_depth', 'dialogue_quality', 
                    'visual_imagination', 'conceptual_depth', 'adaptability']
    
    for criterion in criteria_cols:
        if criterion in filtered_df.columns and criterion in filters['score_ranges']:
            min_score, max_score = filters['score_ranges'][criterion]
            filtered_df = filtered_df[
                (filtered_df[criterion] >= min_score) &
                (filtered_df[criterion] <= max_score)
            ]
    
    # Prompt sequence filter
    if filters['sequences']:
        filtered_df = filtered_df[filtered_df['sequence_name'].isin(filters['sequences'])]
    
    # Prompt name filter
    if filters['prompts']:
        filtered_df = filtered_df[filtered_df['prompt_name'].isin(filters['prompts'])]
    
    return filtered_df

def show():
    """Display the data explorer page."""
    st.header("🔍 Data Explorer")
    
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
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filters")
    
    # Initialize filters
    filters = {}
    
    # Model selection
    all_models = sorted(performance_df['model'].unique())
    filters['models'] = st.sidebar.multiselect(
        "Select Models:",
        all_models,
        default=all_models
    )
    
    # Date range filter
    if 'created_at' in performance_df.columns:
        min_date = performance_df['created_at'].min().date()
        max_date = performance_df['created_at'].max().date()
        
        filters['date_range'] = st.sidebar.date_input(
            "Date Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        filters['date_range'] = None
    
    # Score range filters
    st.sidebar.subheader("Score Ranges")
    filters['score_ranges'] = {}
    
    for criterion in available_criteria:
        criterion_title = criterion.replace('_', ' ').title()
        min_val = float(performance_df[criterion].min())
        max_val = float(performance_df[criterion].max())
        
        filters['score_ranges'][criterion] = st.sidebar.slider(
            f"{criterion_title}:",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            step=0.1
        )
    
    # Sequence and prompt filters
    if 'sequence_name' in performance_df.columns:
        all_sequences = sorted(performance_df['sequence_name'].unique())
        filters['sequences'] = st.sidebar.multiselect(
            "Select Sequences:",
            all_sequences,
            default=all_sequences
        )
    else:
        filters['sequences'] = []
    
    if 'prompt_name' in performance_df.columns:
        all_prompts = sorted(performance_df['prompt_name'].unique())
        filters['prompts'] = st.sidebar.multiselect(
            "Select Prompts:",
            all_prompts,
            default=all_prompts[:10] if len(all_prompts) > 10 else all_prompts
        )
    else:
        filters['prompts'] = []
    
    # Apply filters
    filtered_df = filter_data(performance_df, filters)
    
    # Display filtered data stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Filtered Responses", len(filtered_df), 
                 delta=len(filtered_df) - len(performance_df))
    
    with col2:
        unique_models = len(filtered_df['model'].unique()) if not filtered_df.empty else 0
        st.metric("Models", unique_models)
    
    with col3:
        if not filtered_df.empty:
            avg_score = filtered_df[available_criteria].mean().mean()
            st.metric("Avg Score", f"{avg_score:.2f}")
        else:
            st.metric("Avg Score", "N/A")
    
    with col4:
        if not filtered_df.empty and len(filtered_df) > 1:
            score_std = filtered_df[available_criteria].values.flatten().std()
            st.metric("Score Std Dev", f"{score_std:.3f}")
        else:
            st.metric("Score Std Dev", "N/A")
    
    if filtered_df.empty:
        st.warning("No data matches the current filters. Please adjust your selection.")
        return
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visualizations", "📋 Data Table", "📈 Correlations", "🔬 Detailed Analysis"])
    
    with tab1:
        st.subheader("Interactive Visualizations")
        
        # Visualization controls
        col1, col2 = st.columns(2)
        
        with col1:
            x_axis = st.selectbox(
                "X-Axis:",
                available_criteria,
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            y_axis = st.selectbox(
                "Y-Axis:",
                available_criteria,
                index=1 if len(available_criteria) > 1 else 0,
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        # Create scatter plot
        if x_axis != y_axis:
            scatter_fig = create_scatter_plot(filtered_df, x_axis, y_axis, color_col='model')
            st.plotly_chart(scatter_fig, use_container_width=True)
        
        # Distribution plots
        st.subheader("Score Distributions")
        
        selected_criterion = st.selectbox(
            "Select criterion for distribution:",
            available_criteria,
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        fig = px.histogram(
            filtered_df,
            x=selected_criterion,
            color='model',
            title=f"Distribution of {selected_criterion.replace('_', ' ').title()} Scores",
            marginal="box"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Filtered Data")
        
        # Column selection
        display_cols = st.multiselect(
            "Select columns to display:",
            filtered_df.columns.tolist(),
            default=['model', 'prompt_name', 'sequence_name'] + available_criteria
        )
        
        if display_cols:
            display_df = filtered_df[display_cols].copy()
            
            # Round numeric columns
            for col in available_criteria:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(2)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download filtered data as CSV",
                data=csv,
                file_name=f"storybench_filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with tab3:
        st.subheader("Correlation Analysis")
        
        if len(available_criteria) >= 2:
            # Correlation matrix
            corr_matrix = filtered_df[available_criteria].corr()
            
            fig = px.imshow(
                corr_matrix.values,
                x=[col.replace('_', ' ').title() for col in corr_matrix.columns],
                y=[col.replace('_', ' ').title() for col in corr_matrix.index],
                color_continuous_scale='RdBu',
                aspect="auto",
                title="Criteria Correlation Matrix"
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Correlation insights
            st.subheader("Correlation Insights")
            
            # Find strongest correlations
            correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    correlations.append({
                        'Criteria 1': corr_matrix.columns[i],
                        'Criteria 2': corr_matrix.columns[j],
                        'Correlation': corr_matrix.iloc[i, j]
                    })
            
            correlations_df = pd.DataFrame(correlations).sort_values('Correlation', key=abs, ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Strongest Positive Correlations:**")
                positive_corr = correlations_df[correlations_df['Correlation'] > 0].head()
                for _, row in positive_corr.iterrows():
                    criteria1 = row['Criteria 1'].replace('_', ' ').title()
                    criteria2 = row['Criteria 2'].replace('_', ' ').title()
                    corr = row['Correlation']
                    st.write(f"• {criteria1} ↔ {criteria2}: {corr:.3f}")
            
            with col2:
                st.write("**Strongest Negative Correlations:**")
                negative_corr = correlations_df[correlations_df['Correlation'] < 0].head()
                for _, row in negative_corr.iterrows():
                    criteria1 = row['Criteria 1'].replace('_', ' ').title()
                    criteria2 = row['Criteria 2'].replace('_', ' ').title()
                    corr = row['Correlation']
                    st.write(f"• {criteria1} ↔ {criteria2}: {corr:.3f}")
    
    with tab4:
        st.subheader("Detailed Analysis")
        
        # Model performance breakdown
        if not filtered_df.empty:
            st.write("**Model Performance Summary:**")
            
            model_stats = filtered_df.groupby('model')[available_criteria].agg(['mean', 'std', 'count'])
            model_stats.columns = [f"{col[1].title()} {col[0].replace('_', ' ').title()}" for col in model_stats.columns]
            
            st.dataframe(model_stats.round(3), use_container_width=True)
            
            # Outlier detection
            st.write("**Potential Outliers:**")
            
            outliers = []
            for criterion in available_criteria:
                q1 = filtered_df[criterion].quantile(0.25)
                q3 = filtered_df[criterion].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                criterion_outliers = filtered_df[
                    (filtered_df[criterion] < lower_bound) | 
                    (filtered_df[criterion] > upper_bound)
                ]
                
                if not criterion_outliers.empty:
                    outliers.extend([
                        {
                            'Model': row['model'],
                            'Criterion': criterion.replace('_', ' ').title(),
                            'Score': row[criterion],
                            'Type': 'High' if row[criterion] > upper_bound else 'Low'
                        }
                        for _, row in criterion_outliers.iterrows()
                    ])
            
            if outliers:
                outliers_df = pd.DataFrame(outliers)
                st.dataframe(outliers_df, use_container_width=True)
            else:
                st.info("No statistical outliers detected in the filtered data.")
