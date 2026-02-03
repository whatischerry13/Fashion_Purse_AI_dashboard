import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# --- 1. CONFIGURACIÓN ROBUSTA DE RUTAS ---
current_dir = Path(__file__).resolve().parent 
project_root = current_dir.parent.parent     # Subimos niveles hasta la raiz
data_path = project_root / 'data'

def load_and_merge_data():
    print("🔄 [1/5] Verificando rutas de archivos...")
    
    files = {
        "sales": data_path / 'processed/sales_history.csv',
        "bags": data_path / 'raw/luxury_handbags.csv',
        "clients": data_path / 'processed/clients_clusters.csv',
        "macro": data_path / 'processed/macro_indicators.csv'
    }

    for name, path in files.items():
        if not path.exists():
            print(f"   ❌ ERROR FATAL: No encuentro el archivo: {path}")
            return None

    print("🔄 [2/5] Cargando Datasets...")
    df_sales = pd.read_csv(files["sales"])
    df_bags = pd.read_csv(files["bags"])
    df_clients = pd.read_csv(files["clients"])
    df_macro = pd.read_csv(files["macro"])
    
    # --- 3. LIMPIEZA Y FORMATO ---
    print("🔄 [3/5] Cruzando datos (Merge)...")
    
    df_sales['Fecha'] = pd.to_datetime(df_sales['Fecha'])
    df_macro['Fecha'] = pd.to_datetime(df_macro['Fecha'])
    
    # Merge 1: Ventas + Clientes
    df_master = pd.merge(df_sales, df_clients[['Client_ID', 'Tier', 'City']], 
                        on='Client_ID', how='left')
    
    # Merge 2: Ventas + Macro
    df_master = df_master.sort_values('Fecha')
    df_macro = df_macro.sort_values('Fecha')
    df_master = pd.merge_asof(df_master, df_macro, on='Fecha', direction='backward')
    
    # --- 4. INGENIERÍA DE CARACTERÍSTICAS (MATCH DE MODELO) ---
    print("🔄 [4/5] Extrayendo MODELO y características...")
    
    # --- CAMBIO CLAVE: AÑADIMOS 'Modelo' A LA LISTA ---
    feature_cols = ['Modelo', 'Material', 'Color', 'Estado_General', 'Año_Fabricacion', 'Has_Box', 'Has_Papers']
    
    # Inicializamos columnas
    for col in feature_cols:
        df_master[col] = np.nan
        df_master[col] = df_master[col].astype(object) # Evitar errores de tipo
        
    for idx, row in df_master.iterrows():
        try:
            price = row['Net_Revenue']
            brand = row['Marca']
            
            # Buscamos un bolso en el inventario que coincida en MARCA y PRECIO
            candidates = df_bags[
                (df_bags['Marca'] == brand) & 
                (df_bags['Precio_Venta_EUR'] >= price * 0.85) & 
                (df_bags['Precio_Venta_EUR'] <= price * 1.15)
            ]
            
            if not candidates.empty:
                # Si encontramos uno similar, copiamos sus datos (incluido el Modelo)
                match = candidates.sample(1).iloc[0]
            else:
                # Fallback: Si no coincide precio, cogemos cualquiera de la marca
                brand_backup = df_bags[df_bags['Marca'] == brand]
                if not brand_backup.empty:
                    match = brand_backup.sample(1).iloc[0]
                else:
                    continue
            
            # Copiamos los datos al registro de venta
            for col in feature_cols:
                val = match[col]
                df_master.at[idx, col] = val
                
        except Exception as e:
            continue

    # --- 5. LIMPIEZA FINAL ---
    # Filtramos ventas completadas y que tengan Modelo identificado
    df_training = df_master[
        (df_master['Status'] == 'Completed') & 
        (df_master['Modelo'].notna())
    ].copy()
    
    # Antigüedad
    df_training['Antiguedad'] = df_training['Fecha'].dt.year - df_training['Año_Fabricacion']
    df_training['Antiguedad'] = df_training['Antiguedad'].fillna(0).clip(lower=0)
    
    print(f"🔄 [5/5] Guardando Dataset Maestro ({len(df_training)} registros)...")
    
    output_path = data_path / 'processed/pricing_training_data.csv'
    df_training.to_csv(output_path, index=False)
    
    print(f"✅ ÉXITO TOTAL. Archivo generado en: {output_path}")
    print(f"   Muestra de modelos recuperados: {df_training['Modelo'].unique()[:5]}")
    return df_training

if __name__ == "__main__":
    load_and_merge_data()