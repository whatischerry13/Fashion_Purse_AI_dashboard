import pandas as pd
import numpy as np
from pathlib import Path

# Configuración
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "ine_renta_hogares.csv"
SOURCE_CSV = "53689.csv"

def load_official_baselines():
    """Carga los datos base del INE (2022/23) para tener un suelo realista."""
    baselines = {}
    # Fallbacks inteligentes basados en tu análisis de CSV
    defaults = {
        'Madrid': 62300, 'Barcelona': 56200, 'Sevilla': 41100, 'Málaga': 40800,
        'Baleares': 53000, 'Murcia': 41700, 'Coruña': 45000, 'Vizcaya': 53500,
        'Guipúzcoa': 56000, 'Valencia': 44000, 'Zaragoza': 46000, 'Ourense': 35000
    }
    
    try:
        if Path(SOURCE_CSV).exists():
            print(f"📂 Leyendo fuente oficial: {SOURCE_CSV}...")
            df = pd.read_csv(SOURCE_CSV, sep=';', encoding='utf-8')
            df = df[df['Indicadores de renta media'] == 'Renta bruta media por hogar']
            
            target_provs = {
                'Madrid': 'Madrid', 'Barcelona': 'Barcelona', 'Sevilla': 'Sevilla', 
                'Málaga': 'Málaga', 'Murcia': 'Murcia', 'Illes Balears': 'Baleares',
                'Coruña, A': 'Coruña', 'Bizkaia': 'Vizcaya', 'Gipuzkoa': 'Guipúzcoa',
                'Asturias': 'Asturias', 'Valencia/València': 'Valencia', 'Ourense': 'Ourense'
            }
            
            for ine_name, my_name in target_provs.items():
                prov_data = df[df['Provincias'].str.contains(ine_name, na=False)]
                if not prov_data.empty:
                    latest_val = prov_data.sort_values('Periodo', ascending=False).iloc[0]['Total']
                    baselines[my_name] = float(str(latest_val).replace('.', '').replace(',', '.'))
        else:
            print("⚠️ CSV no encontrado. Usando defaults calibrados.")
    except Exception:
        pass

    for k, v in defaults.items():
        if k not in baselines: baselines[k] = v
        
    return baselines

def calculate_real_capacity(gross, profile):
    """
    Calcula la capacidad real de gasto (Shadow Wealth + IRPF + Coste Vida).
    """
    # 1. Multiplicador de Riqueza Oculta (Basado en análisis de 'Fuentes de Ingreso')
    shadow_mult = 1.0
    if profile in ['Elite', 'Global_Jetset']: shadow_mult = 1.6 # Rentas capital
    elif profile == 'Old_Money_Conservative': shadow_mult = 1.3 # Pensiones altas + Ahorro acumulado
    elif profile == 'Agro_Wealth': shadow_mult = 1.4 # Economía efectivo
    
    real_gross = gross * shadow_mult
    
    # 2. IRPF Estimado (Tipo efectivo medio progresivo)
    # Simplificación: 20% para rentas bajas, hasta 45% para altas
    tax_rate = 0.20
    if real_gross > 60000: tax_rate = 0.30
    if real_gross > 150000: tax_rate = 0.45
    
    net_income = real_gross * (1 - tax_rate)
    return int(net_income)

def generate_census():
    print("💎 GENERANDO DATALAKE INE V7 (The Grand Atlas)...")
    
    BASELINES = load_official_baselines()
    
    # Proyección 2025: Inflación acumulada + Crecimiento Salarial
    MACRO_GROWTH = 1.08 
    
    # MATRIZ DE ZONAS ESTRATÉGICAS (Expandida con insights de tus datos)
    SEEDS = [
        # --- MADRID (65% Salarios -> Young High Earners & Elite) ---
        {"CP": "28109", "Prov": "Madrid", "Ciudad": "Alcobendas", "Zona": "La Moraleja", "Mult": 3.8, "Perfil": "Elite", "Volat": 0.6},
        {"CP": "28001", "Prov": "Madrid", "Ciudad": "Madrid", "Zona": "Salamanca", "Mult": 2.1, "Perfil": "Aristocracy", "Volat": 0.45},
        {"CP": "28010", "Prov": "Madrid", "Ciudad": "Madrid", "Zona": "Chamberí", "Mult": 1.4, "Perfil": "Young_High_Pro", "Volat": 0.3}, # Bonus anuales altos
        # Cinturón Sur (Entry Level Critical Mass)
        {"CP": "28925", "Prov": "Madrid", "Ciudad": "Alcorcón", "Zona": "Las Retamas", "Mult": 0.85, "Perfil": "Aspirational", "Volat": 0.2},
        {"CP": "28905", "Prov": "Madrid", "Ciudad": "Getafe", "Zona": "El Bercial", "Mult": 0.88, "Perfil": "Middle_Class", "Volat": 0.2},

        # --- NORTE (31% Pensiones -> Old Money Conservative) ---
        {"CP": "32003", "Prov": "Ourense", "Ciudad": "Ourense", "Zona": "Centro", "Mult": 1.5, "Perfil": "Old_Money_Conservative", "Volat": 0.2}, # Poca volatilidad (pensiones)
        {"CP": "48992", "Prov": "Vizcaya", "Ciudad": "Getxo", "Zona": "Neguri", "Mult": 2.3, "Perfil": "Industrial_Wealth", "Volat": 0.35},
        {"CP": "33004", "Prov": "Asturias", "Ciudad": "Oviedo", "Zona": "Uría", "Mult": 1.4, "Perfil": "Old_Money_Conservative", "Volat": 0.25},

        # --- COSTA / ISLAS (15% Otros Ingresos -> Riqueza Oculta) ---
        {"CP": "29660", "Prov": "Málaga", "Ciudad": "Marbella", "Zona": "Puerto Banús", "Mult": 3.5, "Perfil": "Global_Jetset", "Volat": 0.7}, 
        {"CP": "07013", "Prov": "Baleares", "Ciudad": "Palma", "Zona": "Son Vida", "Mult": 3.0, "Perfil": "Global_Jetset", "Volat": 0.65},
        {"CP": "03590", "Prov": "Alicante", "Ciudad": "Altea", "Zona": "Altea Hills", "Mult": 2.2, "Perfil": "Expat_Wealth", "Volat": 0.5},

        # --- CATALUÑA & LEVANTE ---
        {"CP": "08017", "Prov": "Barcelona", "Ciudad": "Barcelona", "Zona": "Sarrià", "Mult": 2.2, "Perfil": "Bourgeoisie", "Volat": 0.4},
        {"CP": "46004", "Prov": "Valencia", "Ciudad": "Valencia", "Zona": "Pla del Remei", "Mult": 1.9, "Perfil": "Urban_Sophisticated", "Volat": 0.3},
        
        # --- NICHO OCULTO (Agro & Inditex) ---
        {"CP": "30001", "Prov": "Murcia", "Ciudad": "Murcia", "Zona": "Catedral", "Mult": 1.6, "Perfil": "Agro_Wealth", "Volat": 0.4},
        {"CP": "15173", "Prov": "Coruña", "Ciudad": "Oleiros", "Zona": "Icaria (Inditex)", "Mult": 2.2, "Perfil": "Fashion_Exec", "Volat": 0.3},
    ]

    census_data = []
    print("   -> Expandiendo semillas con Lógica de Ingresos (Pensión vs Salario)...")

    for seed in SEEDS:
        prov_base = BASELINES.get(seed['Prov'], 45000)
        target_gross = prov_base * seed['Mult'] * MACRO_GROWTH
        
        # Generamos 200 hogares por zona
        mu = np.log(target_gross)
        sigma = seed['Volat']
        rentas_simuladas = np.random.lognormal(mu, sigma, 200)
        
        for gross in rentas_simuladas:
            if gross < 16000: gross = 16000
            
            # 1. Capacidad Real (Net Income ajustado)
            net_real = calculate_real_capacity(gross, seed['Perfil'])
            
            # 2. Fashion Wallet (Ajustado por Coste de Vivienda Local)
            # El coste de vivienda es brutal en 2025 en zonas calientes
            housing_penalty = 1.0
            if seed['Prov'] in ['Madrid', 'Barcelona', 'Baleares', 'Málaga']:
                housing_penalty = 1.25 # Vivienda +25% cara
            
            basic_costs = 22000 * housing_penalty
            discretionary = max(0, net_real - basic_costs)
            
            # Propensión al Lujo (Psicología)
            # Un 'Young High Pro' en Madrid gasta más en imagen que un 'Old Money' en Ourense
            propensity = 0.15 # Base
            if seed['Perfil'] in ['Young_High_Pro', 'Aspirational', 'Fashion_Exec']: propensity = 0.35
            if seed['Perfil'] in ['Global_Jetset']: propensity = 0.50 # Gasto desenfrenado
            
            fashion_wallet = int(discretionary * propensity)
            
            census_data.append({
                'CP': seed['CP'],
                'Provincia': seed['Prov'],
                'Ciudad': seed['Ciudad'],
                'Zona_Barrio': seed['Zona'],
                'Renta_Oficial': int(gross),
                'Capacidad_Real': net_real,
                'Fashion_Wallet': fashion_wallet,
                'Perfil_Sociologico': seed['Perfil']
            })

    df = pd.DataFrame(census_data)
    df['Percentil_Nacional'] = df['Renta_Oficial'].rank(pct=True)

    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ DATALAKE V7 COMPLETADO: {len(df)} Hogares.")
    print("   -> Integración de 'Fuentes de Ingreso': Pensiones (Norte) vs Salarios (Madrid).")
    print("   -> Ajuste de Vivienda 2025 aplicado a Fashion Wallet.")
    print(f"📂 Guardado en: {OUTPUT_FILE}")
    
    print("\n🔍 TOP 3 PERFILES CON MAYOR GASTO EN MODA (Fashion Wallet):")
    print(df.groupby('Perfil_Sociologico')['Fashion_Wallet'].mean().sort_values(ascending=False).head(3))

if __name__ == "__main__":
    generate_census()