# src/models/forecasting.py
import pandas as pd
import xgboost as xgb
import joblib
from pathlib import Path
from src.features.engineering import enrich_features # <--- IMPORTANTE

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data/processed/sales_history.csv"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def train_quantile_models():
    print("🧠 [TRAINING V24] Entrenando con Ingeniería Centralizada...")
    
    df_raw = pd.read_csv(DATA_PATH)
    df_raw['Fecha'] = pd.to_datetime(df_raw['Fecha'])
    df_raw['Cluster'] = df_raw['Marca'].apply(lambda x: 'High_End' if x in ['Hermès', 'Chanel'] else 'Standard')
    
    # Agrupación semanal
    df_weekly = df_raw.groupby(['Cluster', pd.Grouper(key='Fecha', freq='W-MON')])['Net_Revenue'].sum().reset_index()
    
    # --- USAR INGENIERÍA CENTRALIZADA ---
    df_enriched = df_weekly.groupby('Cluster').apply(lambda x: enrich_features(x)).reset_index(drop=True)
    df_enriched = df_enriched.dropna()
    
    features = ['Week_Sin', 'Week_Cos', 'Lag_1', 'Lag_4', 'Rolling_Mean_4']
    models_store = {}
    
    for cluster in ['High_End', 'Standard']:
        data = df_enriched[df_enriched['Cluster'] == cluster]
        X, y = data[features], data['Net_Revenue']
        
        cluster_models = {}
        # Entrenar los 3 cuantiles
        for q, alpha in [('q10', 0.1), ('q50', 0.5), ('q90', 0.9)]:
            model = xgb.XGBRegressor(objective='reg:quantileerror', quantile_alpha=alpha,
                                     n_estimators=500, max_depth=4, learning_rate=0.05)
            model.fit(X, y)
            cluster_models[alpha] = model # Guardamos por valor numérico (0.1, 0.5, 0.9)
            
        models_store[cluster] = cluster_models
        
    joblib.dump({'models': models_store, 'features': features}, MODELS_DIR / "xgboost_quantile.joblib")
    print("✅ Modelos entrenados con éxito.")

if __name__ == "__main__":
    train_quantile_models()