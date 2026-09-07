import os
import joblib
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from typing import Dict, List, Tuple
import shap

from inference.scoring import load_scoring_model, predict_applicant_risk
from data.feature_engineering import build_application_features

_EXPLAINER = None

FEATURE_TRANSLATIONS = {
    'EXT_SOURCE_MEAN': 'Composite External Credit Score',
    'EXT_SOURCE_3': 'External Bureau Score 3',
    'EXT_SOURCE_2': 'External Bureau Score 2',
    'EXT_SOURCE_1': 'External Bureau Score 1',
    'EXT_SOURCE_PROD': 'External Score Product Factor',
    'EXT_SOURCE_STD': 'External Score Variance',
    'PAYMENT_RATE': 'Annual Loan Payment-to-Credit Rate',
    'ANNUITY_TO_INCOME_RATIO': 'Annuity-to-Income Ratio',
    'CREDIT_TO_INCOME_RATIO': 'Credit-to-Income Ratio',
    'GOODS_TO_CREDIT_RATIO': 'Goods Price-to-Credit Ratio',
    'AGE_YEARS': 'Applicant Age (Years)',
    'EMPLOYMENT_YEARS': 'Employment Duration (Years)',
    'EMPLOYMENT_TO_AGE_RATIO': 'Career Stability Ratio',
    'INCOME_PER_PERSON': 'Per Capita Household Income',
    'BUREAU_MAX_DPD': 'Bureau Max Days Past Due',
    'BUREAU_LOAN_COUNT': 'Total Bureau Credit Accounts',
    'BUREAU_TOTAL_DEBT_SUM': 'Total Bureau Credit Debt',
    'INS_PAYMENT_DELAY_MEAN': 'Average Installment Payment Delay',
    'INS_PAYMENT_DEFICIT_MEAN': 'Average Installment Shortfall',
    'PREV_REFUSAL_RATIO': 'Historical Refusal Rate on Past Loans',
    'PREV_APPROVED_COUNT': 'Count of Approved Prior Loans',
    'AMT_ANNUITY': 'Requested Annuity Amount',
    'AMT_CREDIT': 'Requested Loan Credit Amount',
    'AMT_INCOME_TOTAL': 'Total Annual Income',
    'AMT_GOODS_PRICE': 'Goods Purchase Price',
    'DAYS_BIRTH': 'Applicant Age (Days)',
    'DAYS_EMPLOYED': 'Employment Duration (Days)',
    'ORGANIZATION_TYPE': 'Employer Organization Type',
    'OCCUPATION_TYPE': 'Applicant Occupation Category',
    'OWN_CAR_AGE': 'Vehicle Age (Years)',
    'DAYS_REGISTRATION': 'Days Since Address Registration',
    'DAYS_ID_PUBLISH': 'Days Since ID Document Issue',
    'DAYS_LAST_PHONE_CHANGE': 'Days Since Contact Info Change',
    'NAME_INCOME_TYPE': 'Income Source Category',
    'NAME_EDUCATION_TYPE': 'Education Level',
    'NAME_FAMILY_STATUS': 'Marital / Family Status',
    'NAME_HOUSING_TYPE': 'Housing Ownership Status',
    'NAME_CONTRACT_TYPE': 'Loan Contract Type',
    'CODE_GENDER': 'Applicant Gender',
    'FLAG_OWN_CAR': 'Car Ownership Flag',
    'FLAG_OWN_REALTY': 'Realty Ownership Flag',
    'CNT_CHILDREN': 'Number of Children',
    'CNT_FAM_MEMBERS': 'Family Members Count',
    'DOCUMENTS_PROVIDED_COUNT': 'Total Identity Documents Submitted'
}

def get_explainer():
    """
    Lazy load SHAP TreeExplainer for LightGBM model.
    """
    global _EXPLAINER
    if _EXPLAINER is None:
        model, metadata = load_scoring_model()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _EXPLAINER = shap.TreeExplainer(model)
    return _EXPLAINER

def extract_shap_vector_and_base(explainer, shap_values) -> Tuple[np.ndarray, float]:
    """
    Robustly extract 1D SHAP feature attribution vector for class 1 (default)
    and base expected value across various SHAP return format versions.
    """
    # 1. Base expected value
    exp_val = explainer.expected_value
    if hasattr(exp_val, '__len__') and not isinstance(exp_val, (str, bytes)):
        if len(exp_val) > 1:
            base_val = float(exp_val[1])
        elif len(exp_val) == 1:
            base_val = float(exp_val[0])
        else:
            base_val = 0.0
    else:
        base_val = float(exp_val)

    # 2. Extract values array
    if hasattr(shap_values, 'values'):
        vals = shap_values.values
    else:
        vals = shap_values

    if isinstance(vals, list):
        sv = vals[1] if len(vals) > 1 else vals[0]
        if len(sv.shape) > 1:
            sv = sv[0]
    elif isinstance(vals, np.ndarray):
        if len(vals.shape) == 3:
            sv = vals[0, :, 1] if vals.shape[2] > 1 else vals[0, :, 0]
        elif len(vals.shape) == 2:
            sv = vals[0]
        else:
            sv = vals
    else:
        sv = np.array(vals)

    return sv, base_val

def explain_applicant(applicant_input: Dict) -> Dict:
    """
    Compute SHAP values for a given applicant input and return plain-language explanations.
    """
    model, metadata = load_scoring_model()
    feature_cols = metadata['feature_cols']
    cat_cols = metadata['cat_cols']
    
    # Predict score
    risk_info = predict_applicant_risk(applicant_input)
    
    # Process features
    df_raw = pd.DataFrame([applicant_input])
    df_feat = build_application_features(df_raw)
    
    missing_cols = [col for col in feature_cols if col not in df_feat.columns]
    if missing_cols:
        missing_df = pd.DataFrame(np.nan, index=df_feat.index, columns=missing_cols)
        df_feat = pd.concat([df_feat, missing_df], axis=1)
            
    for col in cat_cols:
        if col in df_feat.columns:
            df_feat[col] = df_feat[col].astype('category')
            
    X_single = df_feat[feature_cols]
    
    # Calculate SHAP values safely
    explainer = get_explainer()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shap_values = explainer.shap_values(X_single)
    
    sv, expected_val = extract_shap_vector_and_base(explainer, shap_values)
    
    feature_shap = []
    for feat_name, val, s_val in zip(feature_cols, X_single.iloc[0].values, sv):
        display_name = FEATURE_TRANSLATIONS.get(feat_name, feat_name.replace('_', ' ').title())
        
        if pd.notnull(val) and isinstance(val, (int, float, np.number)):
            val_str = f"{float(val):.4f}"
            raw_val = float(val)
        elif pd.notnull(val):
            val_str = str(val)
            raw_val = None
        else:
            val_str = "Not Specified"
            raw_val = None
            
        feature_shap.append({
            "feature": feat_name,
            "display_name": display_name,
            "value": val_str,
            "raw_val": raw_val,
            "shap_value": round(float(s_val), 4),
            "abs_shap": abs(float(s_val))
        })
        
    # Sort by absolute impact
    feature_shap.sort(key=lambda x: x['abs_shap'], reverse=True)
    
    # Top risk factors (positive SHAP = increases default risk)
    risk_factors = [f for f in feature_shap if f['shap_value'] > 0][:5]
    
    # Top mitigating factors (negative SHAP = decreases default risk)
    mitigating_factors = [f for f in feature_shap if f['shap_value'] < 0][:5]
    
    # Generate business language bullet points
    plain_language_bullets = []
    
    for f in risk_factors[:3]:
        plain_language_bullets.append(
            f"❌ **{f['display_name']}** ({f['value']}) increases credit default risk (SHAP impact: +{f['shap_value']:.4f})."
        )
        
    for f in mitigating_factors[:3]:
        plain_language_bullets.append(
            f"✅ **{f['display_name']}** ({f['value']}) helps lower credit default risk (SHAP impact: {f['shap_value']:.4f})."
        )
        
    return {
        "applicant_id": risk_info.get("SK_ID_CURR"),
        "default_probability": risk_info["default_probability"],
        "risk_band": risk_info["risk_band"],
        "base_value": round(expected_val, 4),
        "waterfall": feature_shap[:12],
        "top_risk_factors": risk_factors,
        "top_mitigating_factors": mitigating_factors,
        "plain_language_explanation": plain_language_bullets
    }

if __name__ == '__main__':
    print("Testing SHAP explainer module...")
    sample_app = {
        'SK_ID_CURR': 100002,
        'AMT_INCOME_TOTAL': 202500.0,
        'AMT_CREDIT': 406597.5,
        'AMT_ANNUITY': 24700.5,
        'DAYS_BIRTH': -9461,
        'DAYS_EMPLOYED': -637,
        'EXT_SOURCE_1': 0.083037,
        'EXT_SOURCE_2': 0.262949,
        'EXT_SOURCE_3': 0.139376
    }
    try:
        explanation = explain_applicant(sample_app)
        print("Explainer output bullets:")
        for b in explanation['plain_language_explanation']:
            print(b.encode('ascii', errors='replace').decode('ascii'))
    except FileNotFoundError as e:
        print("Model not trained yet:", e)
