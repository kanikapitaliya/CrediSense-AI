import streamlit as st

def apply_custom_styles():
    """
    Apply modern, high-contrast, premium CSS styles to Streamlit app.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-radius: 12px;
        padding: 24px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        border: 1px solid #334155;
    }
    .header-title {
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-subtitle {
        font-size: 14px;
        color: #94A3B8;
        margin-top: 6px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 26px;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-lbl {
        font-size: 12px;
        font-weight: 500;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    /* Badges */
    .badge-low {
        background-color: rgba(46, 204, 113, 0.15);
        color: #2ECC71;
        border: 1px solid #2ECC71;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }
    .badge-med {
        background-color: rgba(243, 156, 18, 0.15);
        color: #F39C12;
        border: 1px solid #F39C12;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }
    .badge-high {
        background-color: rgba(231, 76, 60, 0.15);
        color: #E74C3C;
        border: 1px solid #E74C3C;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }
    
    /* Insight Card */
    .insight-card {
        background-color: #1E293B;
        border-left: 4px solid #38BDF8;
        padding: 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 16px;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    .insight-title {
        font-size: 16px;
        font-weight: 600;
        color: #38BDF8;
    }
    .insight-body {
        font-size: 14px;
        color: #CBD5E1;
        margin-top: 6px;
    }
    .insight-takeaway {
        font-size: 13px;
        font-weight: 500;
        color: #F59E0B;
        margin-top: 8px;
    }
    
    /* SQL Code Container */
    .sql-box {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        color: #38BDF8;
        font-size: 13px;
    }
    
    /* Architecture Flow Cards */
    .arch-container {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .arch-node {
        background: #1E293B;
        border: 1px solid #334155;
        border-left: 4px solid #818CF8;
        border-radius: 8px;
        padding: 10px 14px;
    }
    .arch-tag {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        color: #818CF8;
        letter-spacing: 0.5px;
    }
    .arch-title {
        font-size: 13px;
        font-weight: 600;
        color: #F8FAFC;
        margin-top: 2px;
    }
    .arch-desc {
        font-size: 11px;
        color: #94A3B8;
    }
    .arch-arrow {
        text-align: center;
        color: #64748B;
        font-size: 10px;
        line-height: 1;
    }
    .arch-split {
        display: flex;
        gap: 8px;
    }
    .arch-half {
        flex: 1;
    }
    </style>
    """, unsafe_allow_html=True)
