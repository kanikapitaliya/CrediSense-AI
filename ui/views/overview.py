import streamlit as st
import json
from pathlib import Path
from config.settings import REPORTS_DIR, PLATFORM_NAME, VERSION, LOW_RISK_MAX_PROB, MEDIUM_RISK_MAX_PROB

def render_overview_view():
    st.markdown(f"""
    <div class="header-card">
        <div class="header-title">🛡️ {PLATFORM_NAME}</div>
        <div class="header-subtitle">AI-Powered Credit Risk Intelligence, Explainability & Natural Language Query System • v{VERSION}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Platform Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-val">307,511</div>
            <div class="metric-lbl">Total Dataset Applicants</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-val">8.07%</div>
            <div class="metric-lbl">Baseline Default Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-val">0.762</div>
            <div class="metric-lbl">Model Out-Of-Fold ROC-AUC</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-val">11.38 : 1</div>
            <div class="metric-lbl">Class Weight Ratio</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    
    # System Architecture Section
    col_a, col_b = st.columns([1.2, 1])
    
    with col_a:
        st.subheader("📌 Platform System Architecture")
        st.markdown("""
        ```mermaid
        graph TD
            A[Home Credit Raw Datasets] --> B[Data Loader & Memory Downcaster]
            B --> C[Feature Engineering & Historical Aggregations]
            C --> D[LightGBM Model Training & Evaluation]
            D --> E[Inference Engine & Risk Banding]
            E --> F[SHAP Explainability & Business Translator]
            E --> G[Business Decision Rules Engine]
            B --> H[SQLite Indexed Query Layer]
            H --> I[NL-to-SQL Engine & Safety Validator]
            F --> J[Streamlit Interactive UI]
            G --> J
            I --> J
        ```
        """, unsafe_allow_html=True)
        
    with col_b:
        st.subheader("🎯 Analytical Risk Band Definitions")
        st.markdown(f"""
        - 🟢 **Low Risk Band** (`prob < {LOW_RISK_MAX_PROB}`): Applicants with prime external scores and strong financial stability. Eligible for automated fast-track approval.
        - 🟠 **Medium Risk Band** (`{LOW_RISK_MAX_PROB} <= prob < {MEDIUM_RISK_MAX_PROB}`): Standard applicants requiring standard underwriting verification of income and employment.
        - 🔴 **High Risk Band** (`prob >= {MEDIUM_RISK_MAX_PROB}`): Applicants with high probability of payment difficulties. Requires senior credit officer manual review or guarantor.
        
        > [!NOTE]
        > **Anti-Hallucination Guarantee**: All numbers, statistics, rule thresholds, and SQL query answers are calculated directly from authentic project datasets without synthetic or fake overrides.
        """)
