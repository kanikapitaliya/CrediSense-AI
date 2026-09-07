import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Union, List, Optional, Tuple
from config.settings import SAVED_MODELS_DIR, LOW_RISK_MAX_PROB, MEDIUM_RISK_MAX_PROB
from data.feature_engineering import build_application_features

_MODEL = None
_METADATA = None

def load_scoring_model():
    """
    Lazy loader for trained LightGBM model and feature metadata.
    """
    global _MODEL, _METADATA
    if _MODEL is None or _METADATA is None:
        model_path = SAVED_MODELS_DIR / "lgbm_credit_model.joblib"
        meta_path = SAVED_MODELS_DIR / "model_metadata.joblib"
        
        if not model_path.exists() or not meta_path.exists():
            raise FileNotFoundError("Model artifacts not found. Please run model training first.")
            
        _MODEL = joblib.load(model_path)
        _METADATA = joblib.load(meta_path)
        
    return _MODEL, _METADATA

def get_risk_band(prob: float) -> Tuple[str, str, str]:
    """
    Map probability to risk band name, color code, and recommendation tag.
    """
    if prob < LOW_RISK_MAX_PROB:
        return "Low Risk", "#2ECC71", "Fast-Track Approval Eligible"
    elif prob < MEDIUM_RISK_MAX_PROB:
        return "Medium Risk", "#F39C12", "Standard Underwriting Review"
    else:
        return "High Risk", "#E74C3C", "Enhanced Risk Mitigation / Senior Officer Approval Required"

def predict_applicant_risk(applicant_input: Union[Dict, pd.DataFrame]) -> Dict:
    """
    Predict default probability and risk band for an individual applicant or batch.
    """
    model, metadata = load_scoring_model()
    feature_cols = metadata['feature_cols']
    cat_cols = metadata['cat_cols']
    
    if isinstance(applicant_input, dict):
        df_raw = pd.DataFrame([applicant_input])
    else:
        df_raw = applicant_input.copy()
        
    # Generate domain features
    df_feat = build_application_features(df_raw)
    
    # Ensure all model feature columns exist (fill missing features with NaN)
    missing_cols = [col for col in feature_cols if col not in df_feat.columns]
    if missing_cols:
        missing_df = pd.DataFrame(np.nan, index=df_feat.index, columns=missing_cols)
        df_feat = pd.concat([df_feat, missing_df], axis=1)
            
    # Format categorical columns
    for col in cat_cols:
        if col in df_feat.columns:
            df_feat[col] = df_feat[col].astype('category')
            
    X_input = df_feat[feature_cols]
    
    # Run prediction
    probs = model.predict_proba(X_input)[:, 1]
    
    results = []
    for i, prob in enumerate(probs):
        band, color, rec = get_risk_band(float(prob))
        sk_id = df_raw.iloc[i].get('SK_ID_CURR', i + 100000)
        
        res = {
            "SK_ID_CURR": int(sk_id) if pd.notnull(sk_id) else None,
            "default_probability": round(float(prob), 4),
            "default_probability_pct": f"{prob*100:.2f}%",
            "risk_score_1000": int(prob * 1000),
            "risk_band": band,
            "badge_color": color,
            "recommendation": rec
        }
        results.append(res)
        
    if isinstance(applicant_input, dict):
        return results[0]
    return results

if __name__ == '__main__':
    print("Testing scoring pipeline...")
    sample_applicant = {
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
        'EXT_SOURCE_3': 0.139376
    }
    try:
        score = predict_applicant_risk(sample_applicant)
        print("Score output:", score)
    except FileNotFoundError as e:
        print("Model not trained yet:", e)
