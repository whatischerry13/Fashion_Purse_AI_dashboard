# src/features/engineering.py
import pandas as pd
import numpy as np

def enrich_features(df: pd.DataFrame, target_col: str = 'Net_Revenue') -> pd.DataFrame:
    """Centraliza la matemática para evitar discrepancias entre Train e Inferencia."""
    df = df.copy()
    
    # 1. Estacionalidad Cíclica
    if 'Fecha' in df.columns:
        week = pd.to_datetime(df['Fecha']).dt.isocalendar().week
    else:
        week = df.index.isocalendar().week if isinstance(df.index, pd.DatetimeIndex) else pd.Series([0])

    df['Week_Sin'] = np.sin(2 * np.pi * week / 52)
    df['Week_Cos'] = np.cos(2 * np.pi * week / 52)
    
    # 2. Lags y Ventanas (Fuente única de verdad)
    if target_col in df.columns:
        df['Lag_1'] = df[target_col].shift(1)
        df['Lag_4'] = df[target_col].shift(4)
        df['Rolling_Mean_4'] = df[target_col].shift(1).rolling(window=4).mean()
        # Rellenar NAs iniciales con la media para evitar que XGBoost falle
        df = df.fillna(method='bfill')
    
    return df

def get_inference_features(history: pd.Series, date: pd.Timestamp) -> pd.DataFrame:
    """Construye la fila de entrada para la predicción de una fecha específica."""
    future_row = pd.Series([np.nan], index=[date])
    extended = pd.concat([history, future_row])
    
    df_extended = pd.DataFrame({'Net_Revenue': extended, 'Fecha': extended.index})
    df_features = enrich_features(df_extended)
    
    # Retornamos solo la última fila (la que no tiene Target aún)
    return df_features.iloc[[-1]].drop(columns=['Net_Revenue', 'Fecha'])