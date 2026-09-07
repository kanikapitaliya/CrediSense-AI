import streamlit as st
import pandas as pd
from nl2sql.query_engine import process_natural_language_query, PRESET_PATTERNS

def render_talk_to_data_view():
    st.subheader("💬 Talk-to-Data (NL-to-SQL Intelligent Data Query System)")
    st.markdown("Ask natural-language questions about credit applicants, default rates, and historical bureau patterns. Queries are converted to verified **read-only SQL** and executed against the SQLite database.")
    
    st.markdown("#### 💡 Quick Query Samples (Click to Run):")
    sample_cols = st.columns(3)
    
    preset_questions = [
        "What is the default rate by education level?",
        "Show average credit amount and annuity by contract type",
        "What are default rates for applicants with bureau overdue history?",
        "Compare default statistics across income types",
        "Previous application approval vs refusal stats by education",
        "List top 10 applicants with highest requested credit amount"
    ]
    
    selected_query = None
    for i, q in enumerate(preset_questions):
        col_idx = i % 3
        with sample_cols[col_idx]:
            if st.button(f"🔍 {q}", key=f"q_btn_{i}", use_container_width=True):
                selected_query = q
                
    st.write("")
    user_q = st.text_input("Or enter your natural language query:", value=selected_query or preset_questions[0], placeholder="e.g. What is the default rate by education level?")
    
    if st.button("⚡ Run NL-to-SQL Query", type="primary", use_container_width=True) or selected_query:
        question_to_run = selected_query or user_q
        with st.spinner(f"Translating & executing query: '{question_to_run}'..."):
            res = process_natural_language_query(question_to_run)
            
        st.divider()
        if res.get("status") == "SUCCESS":
            st.success("✅ **SQL Query Validated (Read-Only SELECT Enforced)**")
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Execution Time", f"{res['execution_time_ms']} ms")
            with m2:
                st.metric("Records Returned", res['row_count'])
            with m3:
                st.metric("Query Mode", res['llm_mode'])
                
            st.markdown("#### 📜 Generated SQL Query")
            st.code(res['sql'], language='sql')
            
            st.markdown("#### 🤖 Grounded Answer Summary")
            st.markdown(res['grounded_answer'])
            
            st.markdown("#### 📋 Returned Dataset Table")
            if 'data_df' in res and isinstance(res['data_df'], pd.DataFrame):
                st.dataframe(res['data_df'], use_container_width=True, hide_index=True)
            elif res.get('data'):
                st.dataframe(pd.DataFrame(res['data']), use_container_width=True, hide_index=True)
        else:
            st.error(f"Query Failed: {res.get('error', 'Unknown Error')}")
