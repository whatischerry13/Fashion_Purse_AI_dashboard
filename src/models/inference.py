import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import timedelta
from src.features.engineering import get_inference_features

# --- CONFIGURACION DE RUTAS ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data/processed/sales_history.csv" 
MACRO_PATH = BASE_DIR / "data/processed/macro_indicators.csv"
MODELS_PATH = BASE_DIR / "models/xgboost_quantile.joblib"
OUTPUT_PATH = BASE_DIR / "data/processed/forecast_horizon.csv"

def run_forecast(weeks_ahead=52, marketing_boost=1.0, competitor_impact=1.0):
    """
    Genera predicciones futuras aplicando factores del simulador.
    """
    print(f"[INFERENCE] Ejecutando forecast... Marketing: {marketing_boost}, Competencia: {competitor_impact}")
    
    # 1. CARGA DE ARTEFACTOS
    if not MODELS_PATH.exists():
        print("ERROR: No se encuentra el modelo entrenado.")
        return pd.DataFrame()
    
    try:
        artifact = joblib.load(MODELS_PATH)
        system_models = artifact['models']
        expected_features = artifact['features']
    except Exception as e:
        print(f"ERROR cargando modelo: {e}")
        return pd.DataFrame()
    
    # 2. CARGA DE DATOS
    if not DATA_PATH.exists() or not MACRO_PATH.exists():
        print("ERROR: Faltan datos historicos o macroeconomicos.")
        return pd.DataFrame()

    df_raw = pd.read_csv(DATA_PATH)
    df_raw['Fecha'] = pd.to_datetime(df_raw['Fecha'])
    
    df_macro = pd.read_csv(MACRO_PATH)
    df_macro['Fecha'] = pd.to_datetime(df_macro['Fecha'])
    
    df_raw['Cluster'] = df_raw['Marca'].apply(lambda x: 'High_End' if x in ['Hermès', 'Chanel', 'Dior'] else 'Standard')
    df_hist = df_raw.groupby(['Cluster', pd.Grouper(key='Fecha', freq='W-MON')])['Net_Revenue'].sum()
    
    all_results = []
    
    # 3. BUCLE DE PREDICCION
    for cluster in system_models.keys():
        try:
            history_series = df_hist.xs(cluster).sort_index()
        except KeyError:
            continue
            
        current_history = history_series.copy()
        last_date = history_series.index[-1]
        
        for i in range(1, weeks_ahead + 1):
            next_date = last_date + timedelta(weeks=i)
            
            # A. Features
            try:
                X_row = get_inference_features(current_history.iloc[-12:], next_date)
                X_row = X_row[expected_features]
            except:
                continue
            
            # B. Prediccion Base
            models = system_models[cluster]
            preds = [models[0.1].predict(X_row)[0], models[0.5].predict(X_row)[0], models[0.9].predict(X_row)[0]]
            p_low, p_mid, p_high = np.sort(preds)
            
            # C. Ajuste Macro
            start_week = next_date - timedelta(days=next_date.weekday())
            end_week = start_week + timedelta(days=6)
            mask = (df_macro['Fecha'] >= start_week) & (df_macro['Fecha'] <= end_week)
            
            econ_idx = df_macro.loc[mask, 'Economic_Index'].mean() if not df_macro[mask].empty else 1.0
            hype_idx = df_macro.loc[mask, 'Luxury_Hype'].mean() if not df_macro[mask].empty else 1.0
            
            # D. APLICAR FACTORES (SIMULADOR)
            resilience = 0.95 if (cluster == 'High_End' and econ_idx < 1.0) else 1.0
            
            f_macro = econ_idx * resilience * hype_idx
            f_mkt = marketing_boost if cluster == 'Standard' else (1 + (marketing_boost - 1) * 0.6)
            f_comp = competitor_impact
            
            total_multiplier = f_macro * f_mkt * f_comp
            
            p_mid *= total_multiplier
            p_low *= total_multiplier
            p_high *= total_multiplier
            
            p_low, p_mid, p_high = max(0, p_low), max(0, p_mid), max(0, p_high)
            
            # E. Riesgo (Downside Risk)
            # Riesgo = % de ingresos que NO aseguramos
            risk_score = (1 - (p_low / p_mid)) * 100 if p_mid > 0 else 0
            risk_score = min(100, max(0, risk_score))
            
            current_history = pd.concat([current_history, pd.Series([p_mid], index=[next_date])])
            
            all_results.append({
                'Fecha': next_date,
                'Cluster': cluster,
                'Prediccion_Realista': round(p_mid, 2),
                'Escenario_Pesimista': round(p_low, 2),
                'Escenario_Optimista': round(p_high, 2),
                'Riesgo_Score': round(risk_score, 1)
            })
            
    # 4. GUARDADO
    df_res = pd.DataFrame(all_results)
    df_res.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Forecast guardado en: {OUTPUT_PATH}")
    return df_res

if __name__ == "__main__":
    run_forecast()
