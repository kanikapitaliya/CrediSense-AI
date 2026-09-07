import streamlit as st
import json
import plotly.express as px
import pandas as pd
from pathlib import Path
from config.settings import REPORTS_DIR

def render_eda_view():
    st.subheader("📊 Exploratory Data Analysis & Data-Derived Insights")
    st.markdown("All business insights below are empirically calculated directly from the **307,511 applicant rows** and historical credit tables.")
    
    report_file = REPORTS_DIR / 'eda_business_insights.json'
    if not report_file.exists():
        st.warning("EDA insights report not found. Running EDA analysis...")
        from data.eda import run_eda_analysis
        summary = run_eda_analysis()
    else:
        with open(report_file, 'r') as f:
            summary = json.load(f)
            
    insights = summary.get("insights", [])
    
    for i, ins in enumerate(insights, 1):
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">Insight {i}: {ins['title']}</div>
            <div class="insight-body">{ins['description']}</div>
            <div class="insight-takeaway">💡 Strategic Action: {ins['takeaway']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        metrics = ins.get("metrics", [])
        if metrics:
            df_m = pd.DataFrame(metrics)
            
            # Chart rendering based on columns
            col1, col2 = st.columns([1.5, 1])
            with col1:
                # Find category column
                cat_col = [c for c in df_m.columns if c not in ['count', 'mean', 'default_pct', 'HAS_OVERDUE']][0] if len(df_m.columns) > 3 else df_m.columns[0]
                fig = px.bar(
                    df_m, x=cat_col, y='default_pct',
                    text='default_pct',
                    color='default_pct',
                    color_continuous_scale='Reds',
                    labels={'default_pct': 'Default Rate (%)', cat_col: 'Category'},
                    title=f"Default Rate by {cat_col}"
                )
                fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.write("**Data Breakdown Table**")
                display_cols = [c for c in df_m.columns if c not in ['mean']]
                st.dataframe(df_m[display_cols], use_container_width=True, hide_index=True)
                
        st.divider()
