import sys
from pathlib import Path

# Configuración de Entorno
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    # CAMBIO AQUÍ: Importamos 'settings' en minúscula
    from src.utils.config import settings, FILES
    from src.utils.data_loader import DataLoader
    from src.utils.scenarios import generate_macro_context
except ImportError as e:
    print(f"❌ Error Crítico de Importación: {e}")
    sys.exit(1)

def main():
    print("="*60)
    print("👠 FASHION PURSE AI - ORQUESTADOR DE SIMULACIÓN V25")
    print("="*60)
    
    # CAMBIO AQUÍ: Usamos settings en minúscula
    days = settings["simulation_days"]
    
    # 1. MACROECONOMÍA
    print(f"\n🌍 1. Generando Contexto Macroeconómico ({days} días)...")
    macro_df = generate_macro_context(days=days, trend_bias=1.0, hype_bias=1.0)
    macro_df.to_csv(FILES["macro_indicators"], index=False)
    
    print(f"   -> Índice Económico Medio: {macro_df['Economic_Index'].mean():.2f}")

    # 2. MOTOR DE VENTAS
    print(f"\n💼 2. Iniciando Motor de Retail (Tráfico: {settings['traffic_mean']}/día)...")
    
    loader = DataLoader()
    df_sales = loader.generate_sales_data(days=days, macro_df=macro_df)
    
    # 3. RESULTADOS
    if not df_sales.empty:
        df_sales.to_csv(FILES["sales_history"], index=False)
        print("\n✅ PIPELINE FINALIZADA")
        print(f"   📊 Transacciones: {len(df_sales):,}")
        print(f"   💾 Guardado en: {FILES['sales_history']}")
        print("\n👉 Siguiente paso: python -m src.models.forecasting")
    else:
        print("\n⚠️ ALERTA: No se generaron ventas.")

if __name__ == "__main__":
    main()