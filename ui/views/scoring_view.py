import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from inference.scoring import predict_applicant_risk

# Preset sample applicants from real dataset for one-click testing
PRESET_APPLICANTS = {
    "Sample 1: SK_ID_CURR 100002 (High Risk / Default Case)": {
        'SK_ID_CURR': 100002,
        'NAME_CONTRACT_TYPE': 'Cash loans',
        'CODE_GENDER': 'M',
        'FLAG_OWN_CAR': 'N',
        'FLAG_OWN_REALTY': 'Y',
        'CNT_CHILDREN': 0,
        'AMT_INCOME_TOTAL': 202500.0,
        'AMT_CREDIT': 406597.5,
        'AMT_ANNUITY': 24700.5,
        'AMT_GOODS_PRICE': 351000.0,
        'NAME_INCOME_TYPE': 'Working',
        'NAME_EDUCATION_TYPE': 'Secondary / secondary special',
        'NAME_FAMILY_STATUS': 'Single / not married',
        'NAME_HOUSING_TYPE': 'House / apartment',
        'DAYS_BIRTH': -9461,
        'DAYS_EMPLOYED': -637,
        'EXT_SOURCE_1': 0.083037,
        'EXT_SOURCE_2': 0.262949,
        'EXT_SOURCE_3': 0.139376,
        'BUREAU_MAX_DPD': 0,
        'PREV_REFUSAL_RATIO': 0.0
    },
    "Sample 2: SK_ID_CURR 100003 (Low Risk / Prime Case)": {
        'SK_ID_CURR': 100003,
        'NAME_CONTRACT_TYPE': 'Cash loans',
        'CODE_GENDER': 'F',
        'FLAG_OWN_CAR': 'N',
        'FLAG_OWN_REALTY': 'N',
        'CNT_CHILDREN': 0,
        'AMT_INCOME_TOTAL': 270000.0,
        'AMT_CREDIT': 1293502.5,
        'AMT_ANNUITY': 35698.5,
        'AMT_GOODS_PRICE': 1129500.0,
        'NAME_INCOME_TYPE': 'State servant',
        'NAME_EDUCATION_TYPE': 'Higher education',
        'NAME_FAMILY_STATUS': 'Married',
        'NAME_HOUSING_TYPE': 'House / apartment',
        'DAYS_BIRTH': -16765,
        'DAYS_EMPLOYED': -1188,
        'EXT_SOURCE_1': 0.311267,
        'EXT_SOURCE_2': 0.622246,
        'EXT_SOURCE_3': 0.535276,
        'BUREAU_MAX_DPD': 0,
        'PREV_REFUSAL_RATIO': 0.0
    },
    "Sample 3: SK_ID_CURR 100004 (Medium Risk Case)": {
        'SK_ID_CURR': 100004,
        'NAME_CONTRACT_TYPE': 'Revolving loans',
        'CODE_GENDER': 'M',
        'FLAG_OWN_CAR': 'Y',
        'FLAG_OWN_REALTY': 'Y',
        'CNT_CHILDREN': 0,
        'AMT_INCOME_TOTAL': 67500.0,
        'AMT_CREDIT': 135000.0,
        'AMT_ANNUITY': 6750.0,
        'AMT_GOODS_PRICE': 135000.0,
        'NAME_INCOME_TYPE': 'Working',
        'NAME_EDUCATION_TYPE': 'Secondary / secondary special',
        'NAME_FAMILY_STATUS': 'Single / not married',
        'NAME_HOUSING_TYPE': 'House / apartment',
        'DAYS_BIRTH': -19046,
        'DAYS_EMPLOYED': -225,
        'EXT_SOURCE_1': 0.45,
        'EXT_SOURCE_2': 0.555999,
        'EXT_SOURCE_3': 0.642739,
        'BUREAU_MAX_DPD': 0,
        'PREV_REFUSAL_RATIO': 0.0
    }
}

def render_scoring_view():
    st.subheader("🎯 Applicant Credit Risk Scoring & Inference")
    st.markdown("Select a sample applicant or adjust financial parameters to run real-time credit default risk prediction.")
    
    preset_choice = st.selectbox("Select Preset Applicant Profile:", list(PRESET_APPLICANTS.keys()))
    base_data = PRESET_APPLICANTS[preset_choice]
    
    st.markdown("#### 📝 Edit Applicant Financial & Risk Profile")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        income = st.number_input("Annual Income ($)", value=float(base_data['AMT_INCOME_TOTAL']), step=5000.0)
        credit = st.number_input("Requested Credit Amount ($)", value=float(base_data['AMT_CREDIT']), step=10000.0)
        annuity = st.number_input("Annual Annuity ($)", value=float(base_data['AMT_ANNUITY']), step=1000.0)
        
    with c2:
        ext1 = st.slider("External Credit Score 1", 0.0, 1.0, float(base_data['EXT_SOURCE_1']), 0.01)
        ext2 = st.slider("External Credit Score 2", 0.0, 1.0, float(base_data['EXT_SOURCE_2']), 0.01)
        ext3 = st.slider("External Credit Score 3", 0.0, 1.0, float(base_data['EXT_SOURCE_3']), 0.01)
        
    with c3:
        age_years = st.number_input("Applicant Age (Years)", value=int(abs(base_data['DAYS_BIRTH'])/365.25), min_value=18, max_value=80)
        emp_years = st.number_input("Employment Duration (Years)", value=int(abs(base_data['DAYS_EMPLOYED'])/365.25), min_value=0, max_value=50)
        bureau_dpd = st.number_input("Bureau Max Days Past Due", value=int(base_data.get('BUREAU_MAX_DPD', 0)))
        
    applicant_input = {
        'SK_ID_CURR': base_data['SK_ID_CURR'],
        'AMT_INCOME_TOTAL': income,
        'AMT_CREDIT': credit,
        'AMT_ANNUITY': annuity,
        'AMT_GOODS_PRICE': credit * 0.9,
        'DAYS_BIRTH': int(-age_years * 365.25),
        'DAYS_EMPLOYED': int(-emp_years * 365.25),
        'EXT_SOURCE_1': ext1,
        'EXT_SOURCE_2': ext2,
        'EXT_SOURCE_3': ext3,
        'BUREAU_MAX_DPD': bureau_dpd,
        'PREV_REFUSAL_RATIO': base_data.get('PREV_REFUSAL_RATIO', 0.0),
        'CNT_CHILDREN': base_data['CNT_CHILDREN'],
        'NAME_CONTRACT_TYPE': base_data['NAME_CONTRACT_TYPE'],
        'NAME_INCOME_TYPE': base_data['NAME_INCOME_TYPE'],
        'NAME_EDUCATION_TYPE': base_data['NAME_EDUCATION_TYPE']
    }
    
    st.write("")
    if st.button("🚀 Calculate Default Risk Score", type="primary", use_container_width=True):
        try:
            res = predict_applicant_risk(applicant_input)
            st.session_state['last_score_result'] = res
            st.session_state['last_applicant_input'] = applicant_input
        except Exception as e:
            st.error(f"Prediction Error: {str(e)}")
            
    if 'last_score_result' in st.session_state:
        res = st.session_state['last_score_result']
        st.divider()
        st.subheader("📌 Scoring Assessment Output")
        
        g1, g2 = st.columns([1, 1.2])
        
        with g1:
            prob_pct = res['default_probability'] * 100
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = prob_pct,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Default Probability (%)", 'font': {'size': 18}},
                number = {'suffix': "%", 'font': {'size': 28}},
                gauge = {
                    'axis': {'range': [0, 50], 'tickwidth': 1},
                    'bar': {'color': res['badge_color']},
                    'steps': [
                        {'range': [0, 7], 'color': "rgba(46, 204, 113, 0.2)"},
                        {'range': [7, 18], 'color': "rgba(243, 156, 18, 0.2)"},
                        {'range': [18, 50], 'color': "rgba(231, 76, 60, 0.2)"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': prob_pct
                    }
                }
            ))
            fig.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
        with g2:
            st.markdown(f"### Risk Band: <span style='color:{res['badge_color']}'>{res['risk_band']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Risk Score (0 - 1000)**: `{res['risk_score_1000']}`")
            st.markdown(f"**Default Probability**: `{res['default_probability_pct']}`")
            st.markdown(f"**Action Recommendation**: **{res['recommendation']}**")
            
            # Key Ratios
            dti = (annuity / (income + 1e-5)) * 100
            c2i = (credit / (income + 1e-5))
            ext_avg = np.mean([ext1, ext2, ext3])
            
            st.markdown(f"- **Debt-to-Income (DTI)**: `{dti:.2f}%`")
            st.markdown(f"- **Credit-to-Income Ratio**: `{c2i:.2f}x`")
            st.markdown(f"- **Composite External Score**: `{ext_avg:.4f}`")
