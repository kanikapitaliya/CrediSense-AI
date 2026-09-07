import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from config.settings import DATASETS_DIR

def reduce_mem_usage(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """
    Iterate through all columns of a dataframe and modify the data type
    to reduce memory usage without losing precision.
    """
    start_mem = df.memory_usage().sum() / 1024**2
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != object and col_type.name != 'category' and 'datetime' not in col_type.name:
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            else:
                if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
                    
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print(f"Memory usage reduced from {start_mem:.2f} MB to {end_mem:.2f} MB ({100 * (start_mem - end_mem) / start_mem:.1f}% reduction)")
    return df

def validate_dataframe(df: pd.DataFrame, table_name: str, key_col: Optional[str] = None) -> Dict:
    """
    Validate DataFrame structure, null counts, key presence, and memory footprint.
    """
    results = {
        "table_name": table_name,
        "valid": True,
        "row_count": len(df),
        "col_count": len(df.columns),
        "missing_cells_pct": round(float(df.isnull().mean().mean() * 100), 2),
        "errors": []
    }
    
    if key_col:
        if key_col not in df.columns:
            results["valid"] = False
            results["errors"].append(f"Missing required primary key column '{key_col}'")
        elif df[key_col].isnull().any():
            results["valid"] = False
            results["errors"].append(f"Primary key '{key_col}' contains null values")
            
    return results

def load_table(filename: str, nrows: Optional[int] = None, optimize_mem: bool = True) -> pd.DataFrame:
    """
    Generic loader for dataset CSV files with memory optimization.
    """
    filepath = DATASETS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
        
    df = pd.read_csv(filepath, nrows=nrows)
    if optimize_mem:
        df = reduce_mem_usage(df)
    return df

def load_application_train(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('application_train.csv', nrows=nrows)

def load_application_test(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('application_test.csv', nrows=nrows)

def load_bureau(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('bureau.csv', nrows=nrows)

def load_bureau_balance(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('bureau_balance.csv', nrows=nrows)

def load_previous_application(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('previous_application.csv', nrows=nrows)

def load_pos_cash(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('POS_CASH_balance.csv', nrows=nrows)

def load_installments(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('installments_payments.csv', nrows=nrows)

def load_credit_card(nrows: Optional[int] = None) -> pd.DataFrame:
    return load_table('credit_card_balance.csv', nrows=nrows)

def load_column_descriptions() -> Dict[str, str]:
    """
    Load data dictionary mapping column names to human descriptions.
    """
    filepath = DATASETS_DIR / 'HomeCredit_columns_description.csv'
    if not filepath.exists():
        return {}
    try:
        df_desc = pd.read_csv(filepath, encoding='latin1')
        desc_dict = dict(zip(df_desc['Row'], df_desc['Description']))
        return desc_dict
    except Exception:
        return {}

if __name__ == "__main__":
    print("Testing data loader utilities...")
    df_app = load_application_train(nrows=1000)
    val = validate_dataframe(df_app, "application_train", key_col="SK_ID_CURR")
    print("Validation result:", val)
