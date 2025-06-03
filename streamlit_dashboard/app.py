#!/usr/bin/env python3
"""
StoryBench v1.5 Streamlit Dashboard
Multi-page dashboard for evaluation results analysis
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent src directory to path for imports
parent_src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(parent_src_path))

# Configure page
st.set_page_config(
    page_title="StoryBench Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stMetric > label {
        font-size: 0.9rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("📚 StoryBench v1.5")
st.sidebar.markdown("---")

# Navigation
pages = {
    "📊 Overview": "overview",
    "🏆 Model Rankings": "rankings", 
    "📈 Criteria Analysis": "criteria",
    "🏢 Provider Comparison": "providers",
    "⚡ Real-Time Progress": "progress",
    "🔍 Data Explorer": "explorer"
}

selected_page = st.sidebar.selectbox("Navigate to:", list(pages.keys()))
page_key = pages[selected_page]

# Main header
st.markdown('<h1 class="main-header">StoryBench Dashboard</h1>', unsafe_allow_html=True)

# Load appropriate page
if page_key == "overview":
    from pages import overview
    overview.show()
elif page_key == "rankings":
    from pages import rankings
    rankings.show()
elif page_key == "criteria":
    st.header("📈 Criteria Analysis")
    st.info("Coming soon! This page will show box plots and heatmaps for evaluation criteria.")
elif page_key == "providers":
    st.header("🏢 Provider Comparison") 
    st.info("Coming soon! This page will compare performance by provider (Anthropic, OpenAI, etc.)")
elif page_key == "progress":
    from pages import progress
    progress.show()
elif page_key == "explorer":
    st.header("🔍 Data Explorer")
    st.info("Coming soon! This page will provide interactive filtering and drill-down analysis.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**StoryBench v1.5**")
st.sidebar.markdown("Built with Streamlit")
