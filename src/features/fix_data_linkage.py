import pandas as pd
import numpy as np
from pathlib import Path
import sys

def fix_sales_linkage():
    print("🔧 Iniciando reparación de vínculos de datos...")

    # --- CORRECCIÓN DE RUTAS (DOBLE VERIFICACIÓN) ---
    # Opción A: Calcular relativo al archivo
    current_file = Path(__file__).resolve()
    # Subimos: features -> src -> Fashion_Purse_AI
    project_root = current_file.parent.parent.parent
    
    # Opción B: Usar el directorio desde donde lanzas el comando (C:\Fashion_Purse_AI)
    cwd = Path.cwd()

    # Verificamos cuál es la correcta buscando la carpeta 'data'
    if (project_root / 'data').exists():
        print(f"   📂 Ruta detectada (Relativa): {project_root}")
    elif (cwd / 'data').exists():
        project_root = cwd
        print(f"   📂 Ruta detectada (Terminal): {project_root}")
    else:
        print(f"   ❌ ERROR: No encuentro la carpeta 'data' en {project_root} ni en {cwd}")
        return

    data_raw_path = project_root / 'data/raw'
    data_processed_path = project_root / 'data/processed'

    # --- CARGAR DATOS ---
    try:
        clients_file = data_raw_path / 'clients.csv'
        sales_file = data_processed_path / 'sales_history.csv'
        
        df_clients = pd.read_csv(clients_file)
        df_sales = pd.read_csv(sales_file)
        print(f"   ✅ Clientes cargados: {len(df_clients)}")
        print(f"   ✅ Ventas cargadas: {len(df_sales)}")
    except Exception as e:
        print(f"   ❌ Error leyendo archivos: {e}")
        return

    # --- LÓGICA DE NEGOCIO ---
    
    # 1. Generar IDs de cliente si no existen
    if 'Client_ID' not in df_clients.columns:
        print("   ⚠️ Creando columna Client_ID en clientes...")
        df_clients['Client_ID'] = [f"CL_{i:04d}" for i in range(len(df_clients))]
        df_clients.to_csv(clients_file, index=False)
        print("   💾 clients.csv actualizado.")

    # 2. Vincular Ventas a Clientes (Ponderado por Tier)
    print("   🔗 Asignando dueños a las ventas...")
    
    if 'Tier' in df_clients.columns:
        # Los VIC compran 10 veces más que los Standard
        weights = df_clients['Tier'].map({
            'VIC': 10, 'VIC (Top 1%)': 10,
            'Gold': 5, 'Gold (Recurrente)': 5,
            'Standard': 1, 'Standard (Ocasional)': 1
        }).fillna(1)
    else:
        weights = np.ones(len(df_clients))
    
    probs = weights / weights.sum()

    # Asignación aleatoria ponderada
    df_sales['Client_ID'] = np.random.choice(
        df_clients['Client_ID'], 
        size=len(df_sales), 
        p=probs
    )
    
    # 3. Guardar
    output_file = data_processed_path / 'sales_history.csv'
    df_sales.to_csv(output_file, index=False)
    
    print(f"   ✅ ¡ÉXITO! Base de datos reparada.")
    print(f"   👉 Archivo guardado: {output_file}")

if __name__ == "__main__":
    fix_sales_linkage()