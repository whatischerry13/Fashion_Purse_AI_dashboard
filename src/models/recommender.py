import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
import os

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
data_processed = project_root / 'data/processed'
data_raw = project_root / 'data/raw'

def generate_recommendations():
    print("🧠 Iniciando Motor de Recomendación Cross-Sell (Content-Based V3.0)...")
    
    # 1. CARGA DE DATOS ROBUSTA
    try:
        if not (data_processed / 'sales_history.csv').exists():
            print("❌ Error: No se encuentra sales_history.csv")
            return
        if not (data_raw / 'accessories_catalog.csv').exists():
            print("❌ Error: No se encuentra accessories_catalog.csv (Ejecuta create_catalog.py primero)")
            return

        df_sales = pd.read_csv(data_processed / 'sales_history.csv')
        df_catalog = pd.read_csv(data_raw / 'accessories_catalog.csv')
        
        # Intentar cargar clusters, si falla, crear dummy
        try:
            df_clusters = pd.read_csv(data_processed / 'clients_clusters.csv')
            # Limpieza básica de nombres de columnas por si acaso
            if 'Segmento_IA' in df_clusters.columns:
                df_clusters.rename(columns={'Segmento_IA': 'Segmento'}, inplace=True)
            elif 'Segmento_Clean' in df_clusters.columns:
                df_clusters.rename(columns={'Segmento_Clean': 'Segmento'}, inplace=True)
            else:
                df_clusters['Segmento'] = 'Standard'
        except:
            print("⚠️ Clusters no encontrados. Usando perfil 'Standard' por defecto.")
            df_clusters = pd.DataFrame(columns=['Client_ID', 'Segmento'])
            
    except Exception as e:
        print(f"❌ Error crítico cargando datos: {e}")
        return

    # Normalización de fechas
    df_sales['Fecha'] = pd.to_datetime(df_sales['Fecha'], errors='coerce')
    today = datetime.now()
    
    # 2. PERFILADO DE CLIENTE (CONTEXTO)
    # Filtramos devoluciones para no recomendar basado en algo que no gustó
    valid_sales = df_sales[df_sales['Status'] != 'Returned'].dropna(subset=['Fecha']).copy()
    
    # Ordenamos por fecha descendente para coger la última compra real
    valid_sales = valid_sales.sort_values('Fecha', ascending=False)
    client_profiles = valid_sales.drop_duplicates(subset='Client_ID', keep='first')
    
    # Unir con Clusters (Left Join)
    if not df_clusters.empty and 'Client_ID' in df_clusters.columns:
        client_profiles = pd.merge(client_profiles, df_clusters[['Client_ID', 'Segmento']], on='Client_ID', how='left')
        client_profiles['Segmento'] = client_profiles['Segmento'].fillna('Standard')
    else:
        client_profiles['Segmento'] = 'Standard'
    
    recommendations_list = []
    
    print(f"   ⚙️ Calculando afinidad para {len(client_profiles)} clientes activos...")

    # 3. MOTOR DE SCORING (CORE)
    for _, client in client_profiles.iterrows():
        c_id = client['Client_ID']
        last_brand = client['Marca'] if pd.notna(client['Marca']) else 'Universal'
        days_since = (today - client['Fecha']).days
        cluster = str(client['Segmento'])
        
        # Iteramos sobre todo el catálogo para puntuar cada ítem
        for _, item in df_catalog.iterrows():
            score = 0
            reasons = []
            
            # --- A. MATCH DE MARCA (La regla de oro del Lujo) ---
            # Si compraste Hermès, quieres accesorios Hermès.
            if item['Brand_Target'] == last_brand:
                score += 200
                reasons.append(f"Colección {last_brand}")
            elif item['Brand_Target'] == 'Universal':
                score += 40 # Siempre suma, es seguro
            else:
                score -= 1000 # PENALIZACIÓN: No recomendar accesorios Gucci a un cliente Chanel
            
            # --- B. MATCH TEMPORAL (Lifecycle) ---
            # Servicios de Mantenimiento (Spa)
            if item['Category'] == 'Service' or item['Subcategory'] == 'Spa':
                if days_since > 300: 
                    score += 150 # Urgencia alta
                    reasons.append("Mantenimiento Anual")
                elif days_since < 60:
                    score -= 100 # Demasiado pronto
            
            # Productos de Cuidado (Add-on inmediato)
            if item['Category'] == 'Care' and days_since < 45:
                score += 80 
                reasons.append("Cuidado Básico")

            # --- C. INTELIGENCIA DE CLUSTER (Personalización) ---
            
            # 💎 VIC / ELITE
            if "VIC" in cluster or "Elite" in cluster:
                # Aman la joyería y lo exclusivo. Ignoran el precio.
                if item['Category'] == 'Jewelry': score += 100
                if item['Sociological_Fit'] in ['Collector', 'Trendsetter', 'VIP']: score += 80
                if item['Price'] > 400: score += 50
            
            # 🛡️ RIESGO (Retornadores)
            elif "Riesgo" in cluster or "Retornadores" in cluster:
                # Evitar productos físicos caros. Empujar Servicios (No devolubles).
                if item['Category'] == 'Service': score += 200
                if item['Category'] in ['Jewelry', 'Leather Goods']: score -= 300
            
            # 🛍️ SMART SHOPPER / STANDARD
            elif "Smart" in cluster or "Standard" in cluster:
                # Buscan funcionalidad y precio medio.
                if item['Category'] in ['Care', 'Storage', 'Adornment']: score += 70
                if item['Price'] < 300: score += 50
                if item['Sociological_Fit'] in ['Pragmatic', 'Classic']: score += 40

            # 💤 INACTIVOS
            elif "Inactivos" in cluster or "Durmientes" in cluster:
                # Necesitan un "gancho" barato o emocional para volver.
                if item['Category'] == 'Adornment': score += 60 # Algo bonito (Twilly, Charm)
                if item['Price'] < 200: score += 50 # Barrera de entrada baja

            # Filtrado Final
            if score > 0:
                recommendations_list.append({
                    'Client_ID': c_id,
                    'Product_ID': item['ID'],
                    'Product_Name': item['Name'],
                    'Category': item['Category'],
                    'Subcategory': item['Subcategory'],
                    'Price': item['Price'],
                    'Margin': item['Margin'],
                    'Score': score,
                    'Reason': " + ".join(reasons[:2]), # Solo las 2 razones principales
                    'Context_Item': last_brand,
                    'Context_Date': client['Fecha'].strftime('%Y-%m-%d')
                })
    
    # 4. RANKING Y EXPORTACIÓN
    df_recs = pd.DataFrame(recommendations_list)
    
    if not df_recs.empty:
        # Ordenar por Cliente y Score descendente
        df_recs = df_recs.sort_values(['Client_ID', 'Score'], ascending=[True, False])
        
        # Diversificación: Intentar no mostrar 3 productos iguales si es posible
        # (Lógica simplificada: tomamos el Top 3 directo para este MVP)
        df_final = df_recs.groupby('Client_ID').head(3)
        
        output_path = data_processed / 'recommendations_matrix.csv'
        df_final.to_csv(output_path, index=False)
        
        print(f"✅ ¡Éxito! Matriz de Recomendación generada.")
        print(f"   📊 Recomendaciones totales: {len(df_final)}")
        print(f"   👤 Clientes cubiertos: {df_final['Client_ID'].nunique()}")
        print(f"   💾 Guardado en: {output_path}")
        
        # Muestra de control
        sample = df_final.iloc[0]
        print(f"   🔎 Ejemplo: Al cliente {sample['Client_ID']} (Contexto: {sample['Context_Item']}) -> {sample['Product_Name']} (Score: {sample['Score']})")
        
    else:
        print("⚠️ Advertencia: No se generaron recomendaciones. Revisa si hay coincidencia de marcas entre Ventas y Catálogo.")

if __name__ == "__main__":
    generate_recommendations()