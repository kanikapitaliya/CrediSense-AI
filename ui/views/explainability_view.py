import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from explainability.shap_explainer import explain_applicant, FEATURE_TRANSLATIONS

def render_explainability_view():
    st.subheader("💡 Explainable AI (SHAP Waterfall & Plain-Language Translation)")
    st.markdown("Surfaces feature impact breakdown for individual applicants translated into non-technical business language.")
    
    if 'last_applicant_input' not in st.session_state:
        st.info("ℹ️ Please score an applicant in the **Applicant Scoring** tab first to view individual SHAP explanations.")
        return
        
    app_input = st.session_state['last_applicant_input']
    
    with st.spinner("Computing SHAP values & translating feature contributions..."):
        try:
            explanation = explain_applicant(app_input)
        except Exception as e:
            st.error(f"SHAP Explanation Error: {str(e)}")
            return
            
    st.markdown(f"### Applicant ID: `{explanation['applicant_id']}` | Risk Band: **{explanation['risk_band']}** ({explanation['default_probability']*100:.2f}% Prob)")
    
    # 1. Plain Language Summary Bullets
    st.markdown("#### 📢 Executive Risk Factor Breakdown")
    for bullet in explanation['plain_language_explanation']:
        st.markdown(bullet)
        
    st.write("")
    
    # 2. SHAP Waterfall Visualization
    st.markdown("#### 📊 Feature Contribution Waterfall Chart (SHAP Values)")
    waterfall_data = explanation['waterfall']
    df_wf = pd.DataFrame(waterfall_data)
    
    fig = px.bar(
        df_wf,
        y='display_name',
        x='shap_value',
        orientation='h',
        color='shap_value',
        color_continuous_scale=['#2ECC71', '#334155', '#E74C3C'],
        labels={'shap_value': 'SHAP Impact on Default Log-Odds', 'display_name': 'Feature Name'},
        title="Top 12 Features Increasing (+) or Decreasing (-) Default Risk"
    )
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Full Feature SHAP Table
    with st.expander("🔍 View Raw Feature Values & SHAP Coefficients"):
        st.dataframe(df_wf[['feature', 'display_name', 'value', 'shap_value']], use_container_width=True, hide_index=True)
