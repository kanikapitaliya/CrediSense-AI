import sys
from pathlib import Path

# Ensure project root is in sys.path when executed via `streamlit run ui/app.py`
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from ui.styles import apply_custom_styles
from ui.views.overview import render_overview_view
from ui.views.eda_view import render_eda_view
from ui.views.scoring_view import render_scoring_view
from ui.views.explainability_view import render_explainability_view
from ui.views.rules_view import render_rules_view
from ui.views.talk_to_data_view import render_talk_to_data_view

st.set_page_config(
    page_title="CrediSense AI - Credit Risk Intelligence Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    apply_custom_styles()
    
    # Sidebar Navigation
    st.sidebar.title("CrediSense AI")
    st.sidebar.caption("Credit Risk Intelligence Platform v1.0.0")
    st.sidebar.divider()
    
    navigation_option = st.sidebar.radio(
        "Platform Modules",
        [
            "🛡️ Executive Overview",
            "📊 EDA & Business Insights",
            "🎯 Applicant Scoring",
            "💡 Explainability & SHAP",
            "⚖️ Decision Rules Engine",
            "💬 Talk-to-Data (NL-to-SQL)"
        ]
    )
    
    st.sidebar.divider()
    st.sidebar.info("""
    **Dataset**: Home Credit Default Risk
    - **Applicants**: 307,511
    - **Default Rate**: 8.07%
    - **Database**: SQLite Indexed
    """)
    
    # Render Selected View
    if navigation_option == "🛡️ Executive Overview":
        render_overview_view()
    elif navigation_option == "📊 EDA & Business Insights":
        render_eda_view()
    elif navigation_option == "🎯 Applicant Scoring":
        render_scoring_view()
    elif navigation_option == "💡 Explainability & SHAP":
        render_explainability_view()
    elif navigation_option == "⚖️ Decision Rules Engine":
        render_rules_view()
    elif navigation_option == "💬 Talk-to-Data (NL-to-SQL)":
        render_talk_to_data_view()

if __name__ == '__main__':
    main()
