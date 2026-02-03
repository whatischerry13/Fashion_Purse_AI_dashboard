from pathlib import Path
import os

# 1. Definir la Raíz del Proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 2. Estructura de Datos
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw"
PROCESSED_DATA_PATH = DATA_DIR / "processed"

# 3. Modelos
MODELS_DIR = ROOT_DIR / "models"
MODEL_FILE = MODELS_DIR / "xgboost_quantile.joblib"

# 4. Archivos Específicos
FILES = {
    "catalog": RAW_DATA_PATH / "luxury_handbags.csv",
    "clients_base": RAW_DATA_PATH / "clients.csv",
    "inventory": PROCESSED_DATA_PATH / "inventory_state.csv",
    "clients_state": PROCESSED_DATA_PATH / "clients_state.csv",
    "sales_history": PROCESSED_DATA_PATH / "sales_history.csv",
    "macro_indicators": PROCESSED_DATA_PATH / "macro_indicators.csv",
    "forecast": PROCESSED_DATA_PATH / "forecast_horizon.csv",
    "daily_metrics": PROCESSED_DATA_PATH / "daily_metrics.csv"
}

# 5. Crear directorios
for path in [RAW_DATA_PATH, PROCESSED_DATA_PATH, MODELS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# 6. Configuración de Negocio (CAMBIO AQUÍ: minúscula 'settings')
settings = {
    "tier_1_brands": ['Hermès', 'Chanel', 'Dior'],
    "simulation_days": 730,
    "traffic_mean": 90,
    "traffic_std": 5,
    "RAW_DATA_PATH": RAW_DATA_PATH,       # Añadido para compatibilidad
    "PROCESSED_DATA_PATH": PROCESSED_DATA_PATH # Añadido para compatibilidad
}