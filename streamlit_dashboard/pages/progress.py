"""
Real-Time Progress page for StoryBench dashboard
Shows progress from automated evaluation runs
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def find_progress_files():
    """Find JSON progress files from automated evaluation runs."""
    progress_files = []
    
    # Look in the main storybench directory for progress files
    storybench_dir = Path(__file__).parent.parent.parent
    
    for file_path in storybench_dir.glob("*progress*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Verify it's a progress file by checking for expected keys
                if 'start_time' in data and 'models' in data:
                    progress_files.append({
                        'path': file_path,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'name': file_path.name
                    })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return sorted(progress_files, key=lambda x: x['modified'], reverse=True)

def load_progress_data(file_path):
    """Load and parse progress data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading progress file: {e}")
        return None

def create_progress_chart(progress_data):
    """Create a progress visualization chart."""
    models = progress_data.get('models', {})
    
    if not models:
        st.warning("No model progress data found.")
        return None
    
    # Prepare data for visualization
    chart_data = []
    for model_name, model_info in models.items():
        chart_data.append({
            'Model': model_name,
            'Completed': model_info.get('completed', 0),
            'Total': model_info.get('total', 0),
            'Progress': (model_info.get('completed', 0) / max(model_info.get('total', 1), 1)) * 100,
            'Status': model_info.get('status', 'unknown')
        })
    
    df = pd.DataFrame(chart_data)
    
    # Create horizontal bar chart
    fig = px.bar(
        df, 
        x='Progress', 
        y='Model',
        orientation='h',
        title="Evaluation Progress by Model",
        color='Status',
        color_discrete_map={
            'completed': '#28a745',
            'in_progress': '#ffc107', 
            'pending': '#6c757d',
            'error': '#dc3545'
        },
        range_x=[0, 100]
    )
    
    fig.update_layout(
        xaxis_title="Progress (%)",
        height=max(400, len(df) * 30)
    )
    
    return fig

def show():
    """Display the progress page."""
    st.header("⚡ Real-Time Progress")
    
    # Find available progress files
    progress_files = find_progress_files()
    
    if not progress_files:
        st.info("""
        No progress files found. Progress files are created when running automated evaluations.
        
        To start an automated evaluation run:
        ```bash
        cd /home/todd/storybench
        source venv-storybench/bin/activate
        python run_automated_evaluation.py --dry-run  # Test run
        python run_automated_evaluation.py           # Full run
        ```
        """)
        return
    
    # File selection
    st.subheader("Select Progress File")
    
    file_options = {f"{pf['name']} ({pf['modified'].strftime('%Y-%m-%d %H:%M')})" : pf['path'] 
                   for pf in progress_files}
    
    selected_file_key = st.selectbox(
        "Choose a progress file:",
        options=list(file_options.keys())
    )
    
    if not selected_file_key:
        return
    
    selected_file = file_options[selected_file_key]
    
    # Load and display progress data
    progress_data = load_progress_data(selected_file)
    
    if not progress_data:
        return
    
    # Display summary metrics
    st.subheader("Run Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        start_time = progress_data.get('start_time')
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            st.metric("Start Time", start_dt.strftime('%Y-%m-%d %H:%M'))
        else:
            st.metric("Start Time", "N/A")
    
    with col2:
        end_time = progress_data.get('end_time')
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            st.metric("End Time", end_dt.strftime('%Y-%m-%d %H:%M'))
        else:
            st.metric("End Time", "In Progress")
    
    with col3:
        total_cost = progress_data.get('total_cost', 0)
        st.metric("Total Cost", f"${total_cost:.4f}")
    
    with col4:
        models = progress_data.get('models', {})
        completed_models = sum(1 for m in models.values() if m.get('status') == 'completed')
        st.metric("Completed Models", f"{completed_models}/{len(models)}")
    
    # Progress visualization
    st.subheader("Progress Visualization")
    fig = create_progress_chart(progress_data)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed model information
    st.subheader("Model Details")
    
    models = progress_data.get('models', {})
    if models:
        for model_name, model_info in models.items():
            with st.expander(f"{model_name} - {model_info.get('status', 'unknown').title()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Completed:** {model_info.get('completed', 0)}/{model_info.get('total', 0)}")
                    st.write(f"**Cost:** ${model_info.get('cost', 0):.4f}")
                    
                with col2:
                    st.write(f"**Start Time:** {model_info.get('start_time', 'N/A')}")
                    st.write(f"**End Time:** {model_info.get('end_time', 'In Progress')}")
                
                # Show errors if any
                errors = model_info.get('errors', [])
                if errors:
                    st.write("**Errors:**")
                    for error in errors:
                        st.error(error)
    
    # Configuration details
    with st.expander("Run Configuration"):
        config = progress_data.get('config', {})
        if config:
            st.json(config)
        else:
            st.write("No configuration data available")
    
    # Raw data
    with st.expander("Raw Progress Data"):
        st.json(progress_data)
    
    # Auto-refresh option
    st.subheader("Auto-Refresh")
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds")
    
    if auto_refresh:
        st.rerun()
