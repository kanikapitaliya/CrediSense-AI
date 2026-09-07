import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from config.settings import REPORTS_DIR

DISCLAIMER_TEXT = (
    "DISCLAIMER: The rules provided by CrediSense AI are decision-support guidelines derived "
    "analytically from model feature importances and historical empirical default rates. "
    "They do NOT constitute official banking policy or legal credit granting decisions."
)

RULES_DEFINITION = [
    {
        "rule_id": "RULE-01",
        "rule_name": "High External Risk & Credit Overdue Escalation",
        "condition_description": "Composite External Score < 0.35 OR Bureau Max DPD > 30 Days",
        "action": "AUTOMATED DECLINE / HIGH RISK ESCALATION",
        "rationale": "Empirical EDA shows composite external score <0.30 carries a 23.14% default rate, and overdue bureau history elevates default risk to 17.91%."
    },
    {
        "rule_id": "RULE-02",
        "rule_name": "Critical Debt Burden Cap Check",
        "condition_description": "Annuity-to-Income Ratio > 25%",
        "action": "MANDATORY DTI UNDERWRITING REVIEW",
        "rationale": "High annuity burden above 25% significantly limits monthly disposable cash flow, escalating probability of missed payment."
    },
    {
        "rule_id": "RULE-03",
        "rule_name": "Young Applicant & Prior Refusal Policy",
        "condition_description": "Applicant Age < 28 AND Prior Home Credit Refusal History",
        "action": "GUARANTOR / COLLATERAL REQUIREMENT",
        "rationale": "Younger applicants with prior loan refusal exhibit ~11.5% default probability requiring secondary payment assurance."
    },
    {
        "rule_id": "RULE-04",
        "rule_name": "Prime Applicant Fast-Track Stream",
        "condition_description": "Composite External Score >= 0.60 AND Annuity-to-Income < 15% AND Zero Bureau DPD",
        "action": "FAST-TRACK APPROVAL ELIGIBLE",
        "rationale": "Prime applicants matching these criteria demonstrate default probability < 2.5%, suitable for instant processing."
    },
    {
        "rule_id": "RULE-05",
        "rule_name": "Credit-to-Income Exposure Cap",
        "condition_description": "Requested Credit Amount > 4.5x Annual Income",
        "action": "CREDIT LIMIT SCALING RECOMMENDED",
        "rationale": "Excessive credit leverage relative to annual income increases default risk during macro-economic shocks."
    }
]

def evaluate_applicant_rules(applicant_data: Dict, model_score: Dict) -> Dict:
    """
    Evaluate business decision rules against applicant metrics and return rule triggers.
    """
    # Extract metrics
    income = float(applicant_data.get('AMT_INCOME_TOTAL', 0) or 0)
    credit = float(applicant_data.get('AMT_CREDIT', 0) or 0)
    annuity = float(applicant_data.get('AMT_ANNUITY', 0) or 0)
    
    ext1 = float(applicant_data.get('EXT_SOURCE_1', np.nan) or np.nan)
    ext2 = float(applicant_data.get('EXT_SOURCE_2', np.nan) or np.nan)
    ext3 = float(applicant_data.get('EXT_SOURCE_3', np.nan) or np.nan)
    ext_mean = np.nanmean([ext1, ext2, ext3]) if not all(np.isnan([ext1, ext2, ext3])) else 0.5
    
    days_birth = float(applicant_data.get('DAYS_BIRTH', -12000) or -12000)
    age_years = abs(days_birth) / 365.25
    
    dti = annuity / (income + 1e-5)
    credit_to_income = credit / (income + 1e-5)
    
    max_dpd = float(applicant_data.get('BUREAU_MAX_DPD', 0) or 0)
    prev_refusal = float(applicant_data.get('PREV_REFUSAL_RATIO', 0) or 0)
    
    triggered_rules = []
    
    # Rule 1
    if ext_mean < 0.35 or max_dpd > 30:
        triggered_rules.append(RULES_DEFINITION[0])
        
    # Rule 2
    if dti > 0.25:
        triggered_rules.append(RULES_DEFINITION[1])
        
    # Rule 3
    if age_years < 28 and prev_refusal > 0:
        triggered_rules.append(RULES_DEFINITION[2])
        
    # Rule 4
    if ext_mean >= 0.60 and dti < 0.15 and max_dpd == 0:
        triggered_rules.append(RULES_DEFINITION[3])
        
    # Rule 5
    if credit_to_income > 4.5:
        triggered_rules.append(RULES_DEFINITION[4])
        
    # Final rule recommendation decision
    if any(r['rule_id'] == 'RULE-01' for r in triggered_rules):
        final_decision = "DECLINE / MANUAL ESCALATION"
    elif any(r['rule_id'] == 'RULE-04' for r in triggered_rules):
        final_decision = "FAST-TRACK APPROVE"
    elif len(triggered_rules) > 0:
        final_decision = "CONDITIONAL REVIEW REQUIRED"
    else:
        final_decision = "STANDARD UNDERWRITING APPROVAL"
        
    return {
        "disclaimer": DISCLAIMER_TEXT,
        "final_rule_decision": final_decision,
        "triggered_rules_count": len(triggered_rules),
        "triggered_rules": triggered_rules,
        "all_rules": RULES_DEFINITION
    }

def get_all_rules_matrix() -> List[Dict]:
    return RULES_DEFINITION

if __name__ == '__main__':
    print("Testing rules engine...")
    sample_app = {
        'AMT_INCOME_TOTAL': 150000,
        'AMT_CREDIT': 800000,
        'AMT_ANNUITY': 45000,
        'EXT_SOURCE_2': 0.22,
        'DAYS_BIRTH': -9000
    }
    sample_score = {"default_probability": 0.24, "risk_band": "High Risk"}
    res = evaluate_applicant_rules(sample_app, sample_score)
    print("Rules decision:", res['final_rule_decision'])
    print("Triggered rules:", [r['rule_id'] for r in res['triggered_rules']])
