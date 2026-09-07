import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from data.loader import (
    load_application_train, load_application_test,
    load_bureau, load_previous_application,
    load_installments, load_pos_cash, load_credit_card, reduce_mem_usage
)
from config.settings import DATA_DIR

def build_application_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate domain-specific features from application dataframe.
    """
    df = df.copy()
    
    # Financial Ratios
    df['PAYMENT_RATE'] = df['AMT_ANNUITY'] / (df['AMT_CREDIT'] + 1e-5)
    df['INCOME_PER_PERSON'] = df['AMT_INCOME_TOTAL'] / (df['CNT_FAM_MEMBERS'].fillna(1) + 1e-5)
    df['ANNUITY_TO_INCOME_RATIO'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
    df['CREDIT_TO_INCOME_RATIO'] = df['AMT_CREDIT'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
    df['GOODS_TO_CREDIT_RATIO'] = df['AMT_GOODS_PRICE'] / (df['AMT_CREDIT'] + 1e-5)
    
    # Time Features
    df['AGE_YEARS'] = (np.abs(df['DAYS_BIRTH']) / 365.25).astype(np.float32)
    
    # Handle anomaly value 365243 in DAYS_EMPLOYED
    days_emp = df['DAYS_EMPLOYED'].replace(365243, np.nan)
    df['EMPLOYMENT_YEARS'] = (np.abs(days_emp) / 365.25).astype(np.float32)
    df['EMPLOYMENT_TO_AGE_RATIO'] = df['EMPLOYMENT_YEARS'] / (df['AGE_YEARS'] + 1e-5)
    
    # External Risk Score Aggregations
    ext_cols = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
    df['EXT_SOURCE_MEAN'] = df[ext_cols].mean(axis=1)
    df['EXT_SOURCE_STD'] = df[ext_cols].std(axis=1).fillna(0)
    df['EXT_SOURCE_PROD'] = df['EXT_SOURCE_1'].fillna(1) * df['EXT_SOURCE_2'].fillna(1) * df['EXT_SOURCE_3'].fillna(1)
    
    # Document provided count
    doc_cols = [c for c in df.columns if c.startswith('FLAG_DOCUMENT_')]
    df['DOCUMENTS_PROVIDED_COUNT'] = df[doc_cols].sum(axis=1) if doc_cols else 0
    
    return df

def build_bureau_features(nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Aggregate historical bureau credit bureau records to SK_ID_CURR level.
    """
    print("Extracting bureau features...")
    df_bureau = load_bureau(nrows=nrows)
    
    # One-hot encode categorical CREDIT_ACTIVE
    df_bureau['IS_ACTIVE'] = (df_bureau['CREDIT_ACTIVE'] == 'Active').astype(np.int8)
    df_bureau['IS_CLOSED'] = (df_bureau['CREDIT_ACTIVE'] == 'Closed').astype(np.int8)
    
    agg_funcs = {
        'SK_ID_BUREAU': ['count'],
        'IS_ACTIVE': ['sum'],
        'IS_CLOSED': ['sum'],
        'AMT_CREDIT_SUM': ['sum', 'max'],
        'AMT_CREDIT_SUM_DEBT': ['sum', 'max'],
        'CREDIT_DAY_OVERDUE': ['max', 'mean']
    }
    
    bureau_agg = df_bureau.groupby('SK_ID_CURR').agg(agg_funcs)
    bureau_agg.columns = ['_'.join(c).upper() for c in bureau_agg.columns]
    
    bureau_agg = bureau_agg.rename(columns={
        'SK_ID_BUREAU_COUNT': 'BUREAU_LOAN_COUNT',
        'IS_ACTIVE_SUM': 'BUREAU_ACTIVE_LOAN_COUNT',
        'IS_CLOSED_SUM': 'BUREAU_CLOSED_LOAN_COUNT',
        'AMT_CREDIT_SUM_SUM': 'BUREAU_TOTAL_CREDIT_SUM',
        'AMT_CREDIT_SUM_MAX': 'BUREAU_MAX_CREDIT_SUM',
        'AMT_CREDIT_SUM_DEBT_SUM': 'BUREAU_TOTAL_DEBT_SUM',
        'AMT_CREDIT_SUM_DEBT_MAX': 'BUREAU_MAX_DEBT_SUM',
        'CREDIT_DAY_OVERDUE_MAX': 'BUREAU_MAX_DPD',
        'CREDIT_DAY_OVERDUE_MEAN': 'BUREAU_MEAN_DPD'
    }).reset_index()
    
    return reduce_mem_usage(bureau_agg)

def build_previous_app_features(nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Aggregate previous Home Credit applications to SK_ID_CURR level.
    """
    print("Extracting previous application features...")
    df_prev = load_previous_application(nrows=nrows)
    
    df_prev['IS_APPROVED'] = (df_prev['NAME_CONTRACT_STATUS'] == 'Approved').astype(np.int8)
    df_prev['IS_REFUSED'] = (df_prev['NAME_CONTRACT_STATUS'] == 'Refused').astype(np.int8)
    df_prev['IS_CANCELED'] = (df_prev['NAME_CONTRACT_STATUS'] == 'Canceled').astype(np.int8)
    
    agg_funcs = {
        'SK_ID_PREV': ['count'],
        'IS_APPROVED': ['sum'],
        'IS_REFUSED': ['sum'],
        'IS_CANCELED': ['sum'],
        'AMT_APPLICATION': ['mean', 'max'],
        'AMT_CREDIT': ['mean', 'max'],
        'AMT_DOWN_PAYMENT': ['mean']
    }
    
    prev_agg = df_prev.groupby('SK_ID_CURR').agg(agg_funcs)
    prev_agg.columns = ['_'.join(c).upper() for c in prev_agg.columns]
    
    prev_agg = prev_agg.rename(columns={
        'SK_ID_PREV_COUNT': 'PREV_APP_COUNT',
        'IS_APPROVED_SUM': 'PREV_APPROVED_COUNT',
        'IS_REFUSED_SUM': 'PREV_REFUSED_COUNT',
        'IS_CANCELED_SUM': 'PREV_CANCELED_COUNT',
        'AMT_APPLICATION_MEAN': 'PREV_AMT_APPLICATION_MEAN',
        'AMT_APPLICATION_MAX': 'PREV_AMT_APPLICATION_MAX',
        'AMT_CREDIT_MEAN': 'PREV_AMT_CREDIT_MEAN',
        'AMT_CREDIT_MAX': 'PREV_AMT_CREDIT_MAX',
        'AMT_DOWN_PAYMENT_MEAN': 'PREV_AMT_DOWN_PAYMENT_MEAN'
    }).reset_index()
    
    prev_agg['PREV_APPROVAL_RATIO'] = prev_agg['PREV_APPROVED_COUNT'] / (prev_agg['PREV_APP_COUNT'] + 1e-5)
    prev_agg['PREV_REFUSAL_RATIO'] = prev_agg['PREV_REFUSED_COUNT'] / (prev_agg['PREV_APP_COUNT'] + 1e-5)
    
    return reduce_mem_usage(prev_agg)

def build_installments_features(nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Aggregate installment payment behavior to SK_ID_CURR level.
    """
    print("Extracting installment payment features...")
    df_ins = load_installments(nrows=nrows)
    
    # Days past due for payment (DAYS_ENTRY_PAYMENT vs DAYS_INSTALMENT)
    df_ins['PAYMENT_DELAY'] = df_ins['DAYS_ENTRY_PAYMENT'] - df_ins['DAYS_INSTALMENT']
    df_ins['PAYMENT_DELAY'] = df_ins['PAYMENT_DELAY'].apply(lambda x: x if x > 0 else 0)
    
    # Shortfall in payment amount (AMT_INSTALMENT vs AMT_PAYMENT)
    df_ins['PAYMENT_DEFICIT'] = df_ins['AMT_INSTALMENT'] - df_ins['AMT_PAYMENT']
    df_ins['PAYMENT_DEFICIT'] = df_ins['PAYMENT_DEFICIT'].apply(lambda x: x if x > 0 else 0)
    
    ins_agg = df_ins.groupby('SK_ID_CURR').agg({
        'PAYMENT_DELAY': ['mean', 'max'],
        'PAYMENT_DEFICIT': ['mean', 'max'],
        'AMT_PAYMENT': ['sum', 'mean']
    })
    ins_agg.columns = ['_'.join(c).upper() for c in ins_agg.columns]
    
    ins_agg = ins_agg.rename(columns={
        'PAYMENT_DELAY_MEAN': 'INS_PAYMENT_DELAY_MEAN',
        'PAYMENT_DELAY_MAX': 'INS_PAYMENT_DELAY_MAX',
        'PAYMENT_DEFICIT_MEAN': 'INS_PAYMENT_DEFICIT_MEAN',
        'PAYMENT_DEFICIT_MAX': 'INS_PAYMENT_DEFICIT_MAX',
        'AMT_PAYMENT_SUM': 'INS_TOTAL_PAYMENT_SUM',
        'AMT_PAYMENT_MEAN': 'INS_PAYMENT_MEAN'
    }).reset_index()
    
    return reduce_mem_usage(ins_agg)

def build_full_dataset(is_train: bool = True, sample_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Build complete applicant dataset by merging application features with historical aggregates.
    """
    if is_train:
        print(f"Loading application train dataset (sample_rows={sample_rows})...")
        df_app = load_application_train(nrows=sample_rows)
    else:
        print(f"Loading application test dataset (sample_rows={sample_rows})...")
        df_app = load_application_test(nrows=sample_rows)
        
    df_app = build_application_features(df_app)
    
    # Pass sample_rows * 5 to auxiliary table loaders when sampling for fast execution
    aux_rows = sample_rows * 10 if sample_rows else None
    
    bureau_agg = build_bureau_features(nrows=aux_rows)
    prev_agg = build_previous_app_features(nrows=aux_rows)
    ins_agg = build_installments_features(nrows=aux_rows)
    
    print("Merging feature aggregates...")
    df_full = df_app.merge(bureau_agg, on='SK_ID_CURR', how='left')
    df_full = df_full.merge(prev_agg, on='SK_ID_CURR', how='left')
    df_full = df_full.merge(ins_agg, on='SK_ID_CURR', how='left')
    
    # Fill missing values for numerical aggregated counts with 0
    zero_fill_cols = [
        'BUREAU_LOAN_COUNT', 'BUREAU_ACTIVE_LOAN_COUNT', 'BUREAU_CLOSED_LOAN_COUNT',
        'BUREAU_TOTAL_CREDIT_SUM', 'BUREAU_TOTAL_DEBT_SUM', 'BUREAU_MAX_DPD',
        'PREV_APP_COUNT', 'PREV_APPROVED_COUNT', 'PREV_REFUSED_COUNT',
        'PREV_APPROVAL_RATIO', 'PREV_REFUSAL_RATIO',
        'INS_PAYMENT_DELAY_MEAN', 'INS_PAYMENT_DELAY_MAX', 'INS_PAYMENT_DEFICIT_MEAN'
    ]
    for col in zero_fill_cols:
        if col in df_full.columns:
            df_full[col] = df_full[col].fillna(0)
            
    df_full = reduce_mem_usage(df_full)
    print(f"Full dataset built successfully! Shape: {df_full.shape}")
    
    return df_full

if __name__ == '__main__':
    print("Testing feature engineering pipeline...")
    df_sample = build_full_dataset(is_train=True, sample_rows=1000)
    print(f"Sample features head:\n{df_sample[['SK_ID_CURR', 'PAYMENT_RATE', 'EXT_SOURCE_MEAN', 'BUREAU_LOAN_COUNT']].head()}")
