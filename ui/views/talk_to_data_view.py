import streamlit as st
import pandas as pd
from nl2sql.query_engine import (
    process_natural_language_query,
    is_gemini_configured,
    PRESET_PATTERNS
)
from config.settings import GEMINI_MODEL

def render_talk_to_data_view():
    st.subheader("💬 Talk-to-Data (Gemini LLM NL-to-SQL Intelligence)")
    st.markdown(
        "Ask natural-language questions about credit applicants, default rates, and historical bureau patterns. "
        "Questions are converted to verified **read-only SQL** using Google Gemini LLM and executed against the SQLite database."
    )
    
    # Initialize conversation memory in session_state
    if 'talk_to_data_history' not in st.session_state:
        st.session_state['talk_to_data_history'] = []
        
    # Gemini status badge
    if is_gemini_configured():
        st.success(f"🟢 **Gemini AI Active**: Connected to `{GEMINI_MODEL}` for dynamic natural language translation.")
    else:
        st.info(
            "ℹ️ **Deterministic Mode**: `GEMINI_API_KEY` is not configured in `.env`. "
            "Using pre-validated SQL query patterns. Configure `GEMINI_API_KEY` in `.env` to enable dynamic LLM querying."
        )
        
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
    user_q = st.text_input(
        "Or enter your natural language query (or follow-up question):",
        value=selected_query or "",
        placeholder="e.g. Which education group has the highest default rate?"
    )
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        run_submitted = st.button("⚡ Run NL-to-SQL Query", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("🧹 Clear Memory", use_container_width=True):
            st.session_state['talk_to_data_history'] = []
            st.rerun()
            
    if run_submitted or selected_query:
        question_to_run = selected_query or user_q
        if not question_to_run.strip():
            st.warning("Please enter a question or select a sample query.")
            return
            
        history = st.session_state.get('talk_to_data_history', [])
        
        with st.spinner(f"Translating & executing query: '{question_to_run}'..."):
            res = process_natural_language_query(question_to_run, conversation_history=history)
            
        st.divider()
        if res.get("status") == "SUCCESS":
            # Save interaction to conversation memory (keep last 5 turns)
            st.session_state['talk_to_data_history'].append({
                "question": question_to_run,
                "sql": res.get("sql", ""),
                "grounded_answer": res.get("grounded_answer", ""),
                "is_llm": res.get("is_llm", False)
            })
            if len(st.session_state['talk_to_data_history']) > 5:
                st.session_state['talk_to_data_history'] = st.session_state['talk_to_data_history'][-5:]
                
            st.success("✅ **SQL Query Validated (Read-Only SELECT Enforced)**")
            
            if res.get("warning"):
                st.warning(f"⚠️ {res['warning']}")
            if res.get("info"):
                st.info(res["info"])
                
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Execution Time", f"{res['execution_time_ms']} ms")
            with m2:
                st.metric("Records Returned", res['row_count'])
            with m3:
                st.metric("Query Engine", res['llm_mode'])
                
            st.markdown("#### 📜 Generated SQL Query")
            st.code(res['sql'], language='sql')
            
            st.markdown("#### 🤖 Grounded Business Answer Summary")
            st.markdown(res['grounded_answer'])
            
            st.markdown("#### 📋 Returned Dataset Table")
            if 'data_df' in res and isinstance(res['data_df'], pd.DataFrame):
                st.dataframe(res['data_df'], use_container_width=True, hide_index=True)
            elif res.get('data'):
                st.dataframe(pd.DataFrame(res['data']), use_container_width=True, hide_index=True)
        else:
            st.error(f"Query Failed: {res.get('error', 'Unknown Error')}")
            
    # Conversation Memory Accordion
    if st.session_state.get('talk_to_data_history'):
        with st.expander(f"💬 Conversation Memory ({len(st.session_state['talk_to_data_history'])} recent turns preserved)"):
            for idx, turn in enumerate(st.session_state['talk_to_data_history'], 1):
                st.markdown(f"**Turn {idx} - User**: {turn['question']}")
                st.markdown(f"**SQL**: `{turn['sql']}`")
                st.markdown(f"**Summary**: {turn['grounded_answer']}")
                st.divider()
