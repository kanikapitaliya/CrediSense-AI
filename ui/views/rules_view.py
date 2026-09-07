import streamlit as st
import pandas as pd
from rules.rule_engine import evaluate_applicant_rules, get_all_rules_matrix, DISCLAIMER_TEXT

def render_rules_view():
    st.subheader("⚖️ Business Decision Rules Engine")
    st.markdown("Automated risk policy rules derived empirically from model decision splits and historical risk thresholds.")
    
    st.warning(f"⚠️ **Legal & Governance Notice**:\n\n{DISCLAIMER_TEXT}")
    st.write("")
    
    if 'last_applicant_input' in st.session_state and 'last_score_result' in st.session_state:
        app_input = st.session_state['last_applicant_input']
        score_res = st.session_state['last_score_result']
        
        rule_eval = evaluate_applicant_rules(app_input, score_res)
        
        st.markdown(f"### Current Applicant Assessment: `{app_input.get('SK_ID_CURR', 'Selected Applicant')}`")
        
        r1, r2 = st.columns([1, 1])
        with r1:
            outcome_str = "APPROVED / FAST-TRACK" if "APPROVE" in rule_eval["final_rule_decision"] else rule_eval["final_rule_decision"]
            st.markdown(f"**Policy Rule Final Outcome**: `{outcome_str}`")
            st.markdown(f"**Rules Triggered**: `{rule_eval['triggered_rules_count']} of {len(rule_eval['all_rules'])} Policy Rules`")
            
        with r2:
            st.markdown(f"**Calculated Default Risk**: `{score_res['default_probability_pct']}`")
            st.markdown(f"**Assigned Risk Band**: **{score_res['risk_band']}**")
            
        st.write("")
        st.markdown("#### 🚨 Triggered Decision Rules")
        if rule_eval['triggered_rules']:
            for rule in rule_eval['triggered_rules']:
                st.error(f"**[{rule['rule_id']}] {rule['rule_name']}**\n\n- **Condition**: `{rule['condition_description']}`\n- **Action Required**: `{rule['action']}`\n- **Empirical Rationale**: {rule['rationale']}")
        else:
            st.success("✅ No adverse policy rules triggered for this applicant. Standard underwriting applies.")
            
        st.divider()
        
    st.markdown("#### 📋 Complete Platform Business Decision Rulebook")
    all_rules = get_all_rules_matrix()
    df_rules = pd.DataFrame(all_rules)
    st.dataframe(df_rules[['rule_id', 'rule_name', 'condition_description', 'action', 'rationale']], use_container_width=True, hide_index=True)
