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
        <div class="arch-container">
            <div class="arch-node">
                <div class="arch-tag">1. Data Ingestion & Downcasting</div>
                <div class="arch-title">Home Credit Datasets</div>
                <div class="arch-desc">307,511 application rows • Memory reduction downcasting</div>
            </div>
            <div class="arch-arrow">▼</div>
            <div class="arch-node">
                <div class="arch-tag">2. Feature Pipeline</div>
                <div class="arch-title">Applicant Ratios & Historical Aggregations</div>
                <div class="arch-desc">160 features: Financial ratios, Bureau DPD, Installment shortfalls</div>
            </div>
            <div class="arch-arrow">▼</div>
            <div class="arch-node">
                <div class="arch-tag">3. ML & Scoring Engine</div>
                <div class="arch-title">LightGBM Classifier & Risk Banding</div>
                <div class="arch-desc">Out-of-fold evaluation (ROC-AUC 0.7507) • Class weight 11.38</div>
            </div>
            <div class="arch-arrow">▼</div>
            <div class="arch-split">
                <div class="arch-node arch-half">
                    <div class="arch-tag">4A. Explainability</div>
                    <div class="arch-title">SHAP Explainer</div>
                    <div class="arch-desc">Waterfall & Plain-language translation</div>
                </div>
                <div class="arch-node arch-half">
                    <div class="arch-tag">4B. Business Rules</div>
                    <div class="arch-title">Rules Engine</div>
                    <div class="arch-desc">Empirical policy rules evaluation</div>
                </div>
            </div>
            <div class="arch-arrow">▼</div>
            <div class="arch-node">
                <div class="arch-tag">5. Relational Query & Interface</div>
                <div class="arch-title">SQLite Database & Streamlit Intelligence UI</div>
                <div class="arch-desc">Read-only SQL safety validator + Natural language querying</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.subheader("🎯 Analytical Risk Band Definitions")
        st.markdown(f"""
        - 🟢 **Low Risk Band** (`prob < {LOW_RISK_MAX_PROB}`): Applicants with prime external scores and strong financial stability. Eligible for automated fast-track approval.
        
        - 🟠 **Medium Risk Band** (`{LOW_RISK_MAX_PROB} <= prob < {MEDIUM_RISK_MAX_PROB}`): Standard applicants requiring standard underwriting verification of income and employment.
        
        - 🔴 **High Risk Band** (`prob >= {MEDIUM_RISK_MAX_PROB}`): Applicants with high probability of payment difficulties. Requires senior credit officer manual review or guarantor.
        """)
