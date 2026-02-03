import pandas as pd
import numpy as np
from pathlib import Path
import os
import random
import sys

print("🏁 Iniciando Generador de Catálogo Masivo (Luxury Scale V4.0)...")

def get_project_root():
    current_path = Path(__file__).resolve()
    for parent in [current_path.parent] + list(current_path.parents):
        if (parent / 'data').exists():
            return parent
    return Path.cwd()

def create_massive_catalog():
    print("📦 Configurando motor de generación...")
    project_root = get_project_root()
    data_raw_path = project_root / 'data/raw'
    os.makedirs(data_raw_path, exist_ok=True)

    catalog_rows = []
    
    # =========================================================================
    # 1. COLECCIÓN CURADA: VINTAGE & ICONIC (Peticiones Específicas)
    # =========================================================================
    print("   ...Inyectando piezas de coleccionista y Vintage")
    
    vintage_gems = [
        # Chanel Vintage
        ("Pendientes Chanel Vintage Coco Mark Redondos", "Jewelry", "Earrings", "Chanel", 449, 250, "Classic", "Vintage, Gold, Round, 90s"),
        ("Pendientes Chanel Vintage Perla Imitación", "Jewelry", "Earrings", "Chanel", 499, 280, "Classic", "Vintage, Pearl, Elegant"),
        ("Pendientes Chanel Vintage Bicolor (Colección 98A)", "Jewelry", "Earrings", "Chanel", 590, 320, "Collector", "Vintage, 98A, Rare, Two-tone"),
        ("Broche Chanel Gripoix Vintage", "Jewelry", "Brooch", "Chanel", 1200, 600, "Collector", "Vintage, Poured Glass, Rare"),
        
        # Hermès Iconic
        ("Brazalete Hermès Kelly Dog (Black/Gold)", "Jewelry", "Bracelet", "Hermès", 550, 280, "Trendsetter", "Leather, Gold, Rock"),
        ("Collar Hermès Farandole 120cm", "Jewelry", "Necklace", "Hermès", 1400, 800, "Classic", "Silver, Chaine d'Ancre, Long"),
        
        # Dior & Others
        ("Gargantilla Dior J'Adior (Antique Gold)", "Jewelry", "Necklace", "Dior", 420, 180, "Trendsetter", "Choker, Logo, Gold"),
        ("Cinturón Chanel Chain & Leather (Vintage)", "Adornment", "Belt", "Chanel", 850, 400, "Style", "Vintage, Chain, Waist")
    ]
    
    for name, cat, sub, brand, p, c, soc, tags in vintage_gems:
        catalog_rows.append({
            'Category': cat, 'Subcategory': sub, 'Name': name, 'Brand_Target': brand,
            'Price': p, 'Cost': c, 'Margin': p - c, 'Sociological_Fit': soc, 
            'Tags': tags, 'Description': "Pieza seleccionada de alta demanda."
        })

    # =========================================================================
    # 2. GENERADOR PROCEDURAL: SLG (Small Leather Goods) - VOLUMEN
    # =========================================================================
    print("   ...Generando matriz de Pequeña Marroquinería (SLG)")
    
    # Definimos los modelos icónicos por marca
    slg_models = {
        'Louis Vuitton': [('Zippy Coin Purse', 450), ('Key Pouch', 320), ('Victorine Wallet', 550), ('Toiletry 26', 680)],
        'Chanel': [('Classic Card Holder', 550), ('Flap Coin Purse', 620), ('O-Case Mini', 490)],
        'Hermès': [('Calvi Card Holder', 390), ('Bastia Coin Purse', 250), ('Bearn Mini', 1400)],
        'Gucci': [('GG Marmont Card Case', 290), ('Dionysus Coin Purse', 350), ('Horsebit 1955 Wallet', 480)],
        'Saint Laurent': [('Cassandre Matelassé Holder', 320), ('Envelope Wallet', 450)],
        'Dior': [('Saddle Flap Card Holder', 420), ('Lady Dior Voyageur', 650)],
        'Prada': [('Saffiano Metal Holder', 380), ('Triangle Logo Wallet', 520)],
        'Bottega Veneta': [('Intrecciato Card Case', 350), ('Cassette Zippered', 490)],
        'Celine': [('Triomphe Card Holder', 360), ('Strap Wallet Medium', 620)],
        'Loewe': [('Puzzle Coin Cardholder', 380), ('Anagram Square Wallet', 490)],
        'Fendi': [('Peekaboo Micro Wallet', 520), ('Baguette Card Case', 310)]
    }
    
    # Colores comunes y raros
    basic_colors = ['Black', 'Gold', 'Beige']
    fun_colors = ['Red', 'Pink', 'Green', 'Blue', 'Silver']
    
    for brand, models in slg_models.items():
        for model_name, base_price in models:
            # Generamos Black y Gold siempre (Básicos)
            for col in basic_colors:
                if brand == 'Hermès' and col == 'Gold': col = 'Etoupe' # Ajuste semántico
                catalog_rows.append({
                    'Category': 'Leather Goods', 'Subcategory': 'Wallet' if 'Wallet' in model_name else 'Card Holder',
                    'Name': f"{model_name} ({col})", 'Brand_Target': brand,
                    'Price': base_price, 'Cost': base_price * 0.45, 'Margin': base_price * 0.55,
                    'Sociological_Fit': 'Pragmatic' if col in ['Black', 'Etoupe'] else 'Style',
                    'Tags': f"SLG, {brand}, {col}, Daily", 'Description': f"Accesorio esencial de {brand} en color {col}."
                })
            
            # 50% de probabilidad de generar un color "Fun" para dar variedad sin saturar
            if random.random() > 0.5:
                fun_col = random.choice(fun_colors)
                catalog_rows.append({
                    'Category': 'Leather Goods', 'Subcategory': 'Card Holder',
                    'Name': f"{model_name} ({fun_col})", 'Brand_Target': brand,
                    'Price': base_price + 20, 'Cost': base_price * 0.45, 'Margin': (base_price+20) * 0.55,
                    'Sociological_Fit': 'Trendsetter',
                    'Tags': f"SLG, {brand}, {fun_col}, Pop", 'Description': f"Edición estacional en {fun_col}."
                })

    # =========================================================================
    # 3. GENERADOR PROCEDURAL: JOYERÍA DE MODA (Fashion Jewelry)
    # =========================================================================
    print("   ...Generando matriz de Joyería (Metales y Acabados)")
    
    jewelry_models = {
        'Hermès': [('Clic H Bracelet', 700, 'Bracelet'), ('Pop H Pendant', 460, 'Necklace'), ('Glenan Bracelet', 350, 'Bracelet')],
        'Chanel': [('CC Crystal Studs', 650, 'Earrings'), ('Pearl Drop Earrings', 820, 'Earrings'), ('Camellia Brooch', 550, 'Brooch')],
        'Dior': [('Tribales Earrings', 590, 'Earrings'), ('Dio(r)evolution Ring', 390, 'Ring'), ('Clair D Lune Necklace', 480, 'Necklace')],
        'Louis Vuitton': [('Essential V Necklace', 450, 'Necklace'), ('Blooming Bracelet', 490, 'Bracelet'), ('Nanogram Cuff', 620, 'Bracelet')],
        'Gucci': [('Double G Studs', 290, 'Earrings'), ('Interlocking G Ring', 320, 'Ring')],
        'Fendi': [('F is Fendi Earrings', 320, 'Earrings'), ('O\'Lock Choker', 550, 'Necklace')]
    }
    
    metals = ['Gold', 'Silver']
    
    for brand, items in jewelry_models.items():
        for model, price, subcat in items:
            for metal in metals:
                # Variación de precio ligera
                var_price = price + random.choice([0, 10, -10])
                catalog_rows.append({
                    'Category': 'Jewelry', 'Subcategory': subcat,
                    'Name': f"{model} ({metal})", 'Brand_Target': brand,
                    'Price': var_price, 'Cost': var_price * 0.4, 'Margin': var_price * 0.6,
                    'Sociological_Fit': 'Classic' if metal == 'Gold' else 'Modern',
                    'Tags': f"Jewelry, {subcat}, {metal}, {brand}", 'Description': f"Acabado en tono {metal}."
                })

    # =========================================================================
    # 4. TECH ACCESSORIES (El nuevo Entry Level)
    # =========================================================================
    print("   ...Añadiendo Accesorios Tech (High Margin)")
    
    tech_brands = ['Louis Vuitton', 'Gucci', 'Prada', 'Dior', 'Saint Laurent']
    for brand in tech_brands:
        catalog_rows.append({
            'Category': 'Tech', 'Subcategory': 'Case',
            'Name': f"iPhone 15 Pro Case ({brand})", 'Brand_Target': brand,
            'Price': 350 + random.randint(0, 100), 'Cost': 100, 'Margin': 250,
            'Sociological_Fit': 'Trendsetter', 'Tags': "Tech, Case, Logo", 'Description': "Funda de lujo para smartphone."
        })
        catalog_rows.append({
            'Category': 'Tech', 'Subcategory': 'Case',
            'Name': f"AirPods Pro Case ({brand})", 'Brand_Target': brand,
            'Price': 250 + random.randint(0, 50), 'Cost': 80, 'Margin': 170,
            'Sociological_Fit': 'Trendsetter', 'Tags': "Tech, AirPods, Gift", 'Description': "Estuche protector con logo."
        })

    # =========================================================================
    # 5. CARE & SERVICES (UNIVERSAL)
    # =========================================================================
    print("   ...Consolidando Servicios y Cuidado")
    
    care_services = [
        ("Saphir Médaille d'Or Renovateur", "Care", "Leather", 24, 12, "Nutrición esencial."),
        ("Collonil Carbon Pro Spray", "Care", "Protection", 19, 9, "Impermeabilizante."),
        ("Kit Limpieza Herrajes", "Care", "Hardware", 29, 10, "Pulido de metales."),
        ("Spa: Limpieza & Ozonización", "Service", "Spa", 120, 25, "Desinfección y limpieza."),
        ("Spa: Restauración Color", "Service", "Repair", 220, 40, "Retoque de esquinas."),
        ("Autenticación Entrupy", "Service", "Auth", 60, 15, "Certificado digital."),
        ("Organizador Fieltro (Universal)", "Storage", "Organizer", 35, 8, "Para tote bags.")
    ]
    
    # Multiplicar los "Care" products para que aparezcan recomendados a varias marcas
    # Simulamos que tenemos stock para distintas marcas
    for name, cat, sub, p, c, desc in care_services:
        catalog_rows.append({
            'Category': cat, 'Subcategory': sub, 'Name': name, 'Brand_Target': 'Universal',
            'Price': p, 'Cost': c, 'Margin': p - c, 'Sociological_Fit': 'Pragmatic', 
            'Tags': "Care, Maintenance", 'Description': desc
        })

    # =========================================================================
    # FINALIZACIÓN
    # =========================================================================
    df_catalog = pd.DataFrame(catalog_rows)
    
    # Generación de IDs
    df_catalog['ID'] = [f"{r['Category'][:3].upper()}-{r['Brand_Target'][:3].upper()}-{i+1:04d}" for i, r in df_catalog.iterrows()]
    cols = ['ID'] + [c for c in df_catalog.columns if c != 'ID']
    df_catalog = df_catalog[cols]
    
    output_file = data_raw_path / 'accessories_catalog.csv'
    df_catalog.to_csv(output_file, index=False)
    
    print(f"\n✅ ¡CATÁLOGO MASIVO GENERADO!")
    print(f"   📊 Referencias Totales: {len(df_catalog)}")
    print(f"   🏷️ Marcas Cubiertas: {len(df_catalog['Brand_Target'].unique())}")
    print(f"   📂 Guardado en: {output_file}")
    
    # Verificación rápida
    print("\n   Desglose por Categoría:")
    print(df_catalog['Category'].value_counts().to_string())

if __name__ == "__main__":
    create_massive_catalog()