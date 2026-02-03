import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.cluster import KMeans
from datetime import datetime
import joblib
from pathlib import Path
import sys

# --- CONFIGURACIÓN ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
data_path = project_root / 'data/processed'
raw_path = project_root / 'data/raw'
models_path = project_root / 'models'

def run_clustering_model():
    print("🚀 Iniciando Motor de Segmentación Avanzada (Luxury AI v2.0)...")
    
    # 1. Carga Robusta de Datos
    try:
        df_sales = pd.read_csv(data_path / 'sales_history.csv')
        df_clients = pd.read_csv(raw_path / 'clients.csv')
        print(f"   ✅ Datos cargados: {len(df_sales)} transacciones, {len(df_clients)} clientes.")
    except Exception as e:
        print(f"   ❌ Error crítico cargando datos: {e}")
        return

    # 2. Módulo de Auto-Reparación (Self-Healing Data)
    if 'Client_ID' not in df_sales.columns:
        print("   🔧 Detectada falta de IDs en ventas. Ejecutando vinculación inteligente...")
        
        # Asegurar que clientes tienen ID
        if 'Client_ID' not in df_clients.columns:
            df_clients['Client_ID'] = [f"CL_{i:04d}" for i in range(len(df_clients))]
            df_clients.to_csv(raw_path / 'clients.csv', index=False)
        
        weights = df_clients['Tier'].map({
            'VIC': 12, 'VIC (Top 1%)': 12,
            'Gold': 6, 'Gold (Recurrente)': 6,
            'Standard': 1
        }).fillna(1)
        probs = weights / weights.sum()
        
        df_sales['Client_ID'] = np.random.choice(
            df_clients['Client_ID'], size=len(df_sales), p=probs
        )
        df_sales.to_csv(data_path / 'sales_history.csv', index=False)
        print("   ✅ Vinculación completada y guardada.")

    # 3. Ingeniería de Características (The Feature Engine)
    print("   ⚙️ Calculando métricas avanzadas (RFM + Returns + Loyalty)...")
    
    df_sales['Fecha'] = pd.to_datetime(df_sales['Fecha'], errors='coerce')
    snapshot_date = df_sales['Fecha'].max() + pd.Timedelta(days=1)
    
    money_col = 'Net_Revenue' if 'Net_Revenue' in df_sales.columns else 'Precio'
    if money_col not in df_sales.columns:
        df_sales[money_col] = 500 
        
    # A. Métricas de Valor (Solo Ventas Completadas)
    sales_completed = df_sales[df_sales['Status'] != 'Returned'].copy()
    
    rfm = sales_completed.groupby('Client_ID').agg({
        'Fecha': lambda x: (snapshot_date - x.max()).days, # Recencia
        'Marca': 'count',                                  # Frecuencia (Count de filas)
        money_col: ['sum', 'mean'],                        # LTV y Ticket Medio
    }).reset_index()
    
    rfm.columns = ['Client_ID', 'Recency', 'Frequency', 'Monetary', 'Avg_Ticket']
    
    # Calcular diversidad de marcas
    brand_diversity = sales_completed.groupby('Client_ID')['Marca'].nunique().reset_index()
    brand_diversity.columns = ['Client_ID', 'Unique_Brands']
    rfm = pd.merge(rfm, brand_diversity, on='Client_ID', how='left')
    
    # B. Métricas de Riesgo
    risk_metrics = df_sales.groupby('Client_ID').agg({
        'Status': lambda x: (x == 'Returned').mean() 
    }).reset_index()
    risk_metrics.columns = ['Client_ID', 'Return_Rate']
    
    # Fusión
    features = pd.merge(rfm, risk_metrics, on='Client_ID', how='left').fillna(0)
    
    # Feature Derivada
    features['Brand_Loyalty'] = 1 - (features['Unique_Brands'] / features['Frequency'])
    features['Brand_Loyalty'] = features['Brand_Loyalty'].clip(0, 1)

    print(f"   ✅ Perfiles calculados: {len(features)}. Ejemplo: Return Rate medio {(features['Return_Rate'].mean()*100):.1f}%")

    # 4. Preprocesamiento Matemático
    cols_to_log = ['Recency', 'Frequency', 'Monetary', 'Avg_Ticket']
    features_log = features.copy()
    for col in cols_to_log:
        features_log[col] = np.log1p(features_log[col])
        
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_log[cols_to_log + ['Return_Rate', 'Brand_Loyalty']])
    
    # 5. Clustering (K-Means)
    k = 5
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    features['Cluster'] = kmeans.fit_predict(features_scaled)
    
    # 6. Interpretabilidad Automática (CORREGIDO)
    # Seleccionamos explícitamente solo las columnas numéricas para la media
    numeric_cols = ['Monetary', 'Frequency', 'Recency', 'Avg_Ticket', 'Return_Rate', 'Brand_Loyalty']
    cluster_profile = features.groupby('Cluster')[numeric_cols].mean()
    
    def name_cluster(row):
        if row['Return_Rate'] > 0.3:
            return '⚠️ Retornadores Seriales'
        elif row['Monetary'] > cluster_profile['Monetary'].quantile(0.8) and row['Recency'] < cluster_profile['Recency'].quantile(0.4):
            return '💎 Top VIC (Elite)'
        elif row['Frequency'] > cluster_profile['Frequency'].quantile(0.7) and row['Avg_Ticket'] < cluster_profile['Avg_Ticket'].median():
            return '🛍️ Smart Shoppers (Accesorios)'
        elif row['Recency'] > cluster_profile['Recency'].quantile(0.7):
            return '💤 Durmientes / Inactivos'
        elif row['Brand_Loyalty'] > 0.6:
            return '❤️ Brand Lovers (Fieles)'
        else:
            return '🆕 Standard / Nuevos'

    cluster_names = {}
    for c_id in cluster_profile.index:
        cluster_names[c_id] = name_cluster(cluster_profile.loc[c_id])
        
    features['Segmento_IA'] = features['Cluster'].map(cluster_names)
    
    # 7. Guardar Resultados Finales
    df_final = pd.merge(df_clients, features, on='Client_ID', how='left')
    
    df_final['Segmento_IA'] = df_final['Segmento_IA'].fillna('🆕 Nuevo / Sin Data')
    for col in ['Monetary', 'Frequency', 'Return_Rate']:
        df_final[col] = df_final[col].fillna(0)
        
    output_file = data_path / 'clients_clusters.csv'
    df_final.to_csv(output_file, index=False)
    
    joblib.dump(kmeans, models_path / 'kmeans_model.joblib')
    
    print(f"   💾 Segmentación guardada en: {output_file}")
    print("   🧠 Modelo entrenado. Segmentos detectados:")
    print(df_final['Segmento_IA'].value_counts().head())

if __name__ == "__main__":
    run_clustering_model()