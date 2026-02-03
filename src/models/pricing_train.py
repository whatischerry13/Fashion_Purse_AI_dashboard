import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import sys
from pathlib import Path
import time

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
data_path = project_root / 'data'
models_path = project_root / 'models'
models_path.mkdir(exist_ok=True)

def train_pricing_model_advanced():
    print("🚀 [AI LAB] Iniciando Protocolo de Entrenamiento Avanzado (XGBoost Ensemble)...")
    start_time = time.time()
    
    # 1. CARGA DE DATOS
    try:
        csv_path = data_path / 'processed/pricing_training_data.csv'
        if not csv_path.exists():
            print(f"❌ Error: No encuentro {csv_path}")
            return
        df = pd.read_csv(csv_path)
        
        # Limpieza rápida: Eliminar nulos críticos
        # Aseguramos que 'Modelo' exista (si no existe, lo tratamos como 'Desconocido')
        if 'Modelo' not in df.columns:
            print("⚠️ Advertencia: Columna 'Modelo' no encontrada. Se usará 'Marca' como proxy.")
            df['Modelo'] = 'Desconocido'
        else:
            df['Modelo'] = df['Modelo'].fillna('Desconocido')

        df = df.dropna(subset=['Luxury_Hype', 'Material', 'Net_Revenue'])
        print(f"   📊 Dataset cargado: {len(df)} registros validados.")
        
    except Exception as e:
        print(f"❌ Error crítico de carga: {e}")
        return

    # 2. SELECCIÓN DE CARACTERÍSTICAS (Incluyendo MODELO)
    features = [
        'Marca', 'Modelo', 'Material', 'Color', 'Estado_General', 
        'Antiguedad', 'Has_Box', 'Has_Papers', 'Luxury_Hype'
    ]
    target = 'Net_Revenue'
    
    # Verificación de columnas existentes
    missing_cols = [col for col in features if col not in df.columns]
    if missing_cols:
        print(f"❌ Faltan columnas en el CSV: {missing_cols}")
        return

    X = df[features]
    y = df[target]
    
    # 3. SPLIT (80% Entreno / 20% Test Ciego)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. PIPELINE DE PREPROCESAMIENTO
    # 'Modelo' tiene alta cardinalidad (muchos valores únicos). handle_unknown='ignore' es vital.
    categorical_features = ['Marca', 'Modelo', 'Material', 'Color', 'Estado_General']
    numeric_features = ['Antiguedad', 'Luxury_Hype']
    binary_features = ['Has_Box', 'Has_Papers']
    
    preprocessor = ColumnTransformer(transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
        ('num', 'passthrough', numeric_features + binary_features)
    ])
    
    # 5. GRID DE HIPERPARÁMETROS (Fuerza Bruta Inteligente)
    param_grid = {
        'regressor__n_estimators': [300, 500, 700],      # Más árboles = más precisión
        'regressor__learning_rate': [0.01, 0.03, 0.05],  # Paso fino
        'regressor__max_depth': [4, 6, 8],               # Profundidad de decisión
        'regressor__subsample': [0.7, 0.8, 0.9],         # Prevención Overfitting
        'regressor__colsample_bytree': [0.6, 0.7, 0.8],  # Prevención Overfitting
        'regressor__reg_alpha': [0, 0.1, 0.5],           # Regularización L1
        'regressor__reg_lambda': [1, 1.5, 2]             # Regularización L2
    }
    
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', XGBRegressor(random_state=42, n_jobs=-1))
    ])
    
    print("\n   🧠 Ejecutando Búsqueda de Hiperparámetros (Randomized Search)...")
    print("      (Probando 50 configuraciones óptimas con Cross-Validation)")
    
    search = RandomizedSearchCV(
        pipeline, 
        param_distributions=param_grid, 
        n_iter=50, 
        scoring='neg_root_mean_squared_error', 
        cv=5, 
        verbose=1, 
        n_jobs=-1,
        random_state=42
    )
    
    search.fit(X_train, y_train)
    best_model = search.best_estimator_
    
    print(f"\n   💎 Mejor Configuración:\n      {search.best_params_}")
    
    # 6. VALIDACIÓN DE OVERFITTING
    print("\n   🕵️‍♂️ DIAGNÓSTICO DE OVERFITTING:")
    train_preds = best_model.predict(X_train)
    test_preds = best_model.predict(X_test)
    
    r2_train = r2_score(y_train, train_preds)
    r2_test = r2_score(y_test, test_preds)
    
    print(f"      • R2 Entrenamiento: {r2_train:.4f}")
    print(f"      • R2 Test (Real):   {r2_test:.4f}")
    
    diff = r2_train - r2_test
    if diff > 0.10:
        print(f"      ⚠️ ALERTA: Overfitting alto ({diff:.1%}). Modelo memoriza datos.")
    elif diff < 0.05:
        print(f"      ✅ ESTADO: Modelo robusto y generalizable.")
    else:
        print(f"      ℹ️ ESTADO: Balance aceptable.")

    # 7. MÉTRICAS FINALES (Test Set)
    mae = mean_absolute_error(y_test, test_preds)
    mse = mean_squared_error(y_test, test_preds)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs((y_test - test_preds) / y_test)) * 100
    
    print("\n   🏆 RESULTADOS FINALES (Test Set Ciego):")
    print(f"      • MAE (Error Medio):       {mae:.2f} €")
    print(f"      • RMSE (Penaliza graves):  {rmse:.2f} €")
    print(f"      • R2 Score (Precisión):    {r2_test:.4f}")
    print(f"      • MAPE (Error %):          {mape:.2f} %")
    
    # 8. GUARDADO
    output_path = models_path / 'pricing_xgboost.joblib'
    joblib.dump(best_model, output_path)
    
    minutes = (time.time() - start_time) / 60
    print(f"\n   💾 Modelo optimizado guardado en: {output_path}")
    print(f"   ⏱️ Tiempo total: {minutes:.1f} min")

if __name__ == "__main__":
    train_pricing_model_advanced()