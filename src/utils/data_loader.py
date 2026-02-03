import pandas as pd
import numpy as np
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
# CAMBIO CLAVE: Importamos FILES y settings directamente
from .config import settings, FILES

class DataLoader:
    def __init__(self):
        # --- RUTAS (Ahora usamos FILES que es mucho más seguro) ---
        self.catalog_path = FILES["catalog"]
        self.clients_base_path = FILES["clients_base"]
        self.inventory_state_path = FILES["inventory"]
        self.clients_state_path = FILES["clients_state"]
        self.metrics_path = FILES["daily_metrics"]
        
        self.TIER_1_BRANDS = settings["tier_1_brands"]
        self.daily_metrics_buffer = []

        # Cargar datos maestros
        self.catalog_templates = self._load_robust_csv(self.catalog_path)
        self.clients = self._load_robust_csv(self.clients_state_path if self.clients_state_path.exists() else self.clients_base_path)
        self._ensure_stratified_wallets()

        if self.inventory_state_path.exists():
            self.live_inventory = pd.read_csv(self.inventory_state_path)
        else:
            self.live_inventory = pd.DataFrame()

    def _load_robust_csv(self, path):
        if not path.exists(): return pd.DataFrame()
        try:
            return pd.read_csv(path, sep=None, engine='python')
        except:
            return pd.read_csv(path, sep=';')

    def _clean_price(self, value):
        if isinstance(value, (int, float)): return float(value)
        clean = re.sub(r'[^\d.,]', '', str(value))
        if ',' in clean and '.' in clean: clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean: clean = clean.replace(',', '.')
        try: return float(clean)
        except: return 0.0

    def _ensure_stratified_wallets(self):
        """Asigna presupuestos realistas: Aspiracionales, Recurrentes y VIPs."""
        if self.clients.empty: return
        
        def assign_budget():
            rand = random.random()
            if rand < 0.65: return random.randint(3500, 9000)   # Aspiracional (Standard)
            if rand < 0.92: return random.randint(15000, 40000) # Lujo Recurrente
            return random.randint(60000, 200000)                # VIP (High End)

        if 'Current_Budget' not in self.clients.columns:
            self.clients['Fashion_Wallet'] = [assign_budget() for _ in range(len(self.clients))]
            self.clients['Current_Budget'] = self.clients['Fashion_Wallet']
            self.clients['Purchases_Count'] = 0

    def _restock_inventory(self, date, volume=15):
        if self.catalog_templates.empty: return
        new_items = self.catalog_templates.sample(n=volume, replace=True).copy()
        new_items['ID_Serial_Unico'] = [f"SN-{random.randint(1000000, 9999999)}" for _ in range(len(new_items))]
        new_items['Date_Added'] = date
        new_items['Days_On_Market'] = 0
        new_items['Status'] = 'Available'
        new_items['Current_Price'] = new_items['Precio_Venta_EUR'].apply(self._clean_price)
        new_items['COGS'] = new_items['Current_Price'] * 0.55
        self.live_inventory = pd.concat([self.live_inventory, new_items], ignore_index=True)

    def _calculate_affinity(self, client, product, econ_idx):
        """Calcula probabilidad de compra democrática."""
        price = product['Current_Price']
        budget = client['Current_Budget']
        is_tier_1 = product['Marca'] in self.TIER_1_BRANDS
        
        # Filtro de crisis
        psych_factor = 1.15 if (econ_idx < 0.9 and is_tier_1) else (0.65 if econ_idx < 0.9 else 1.05)
        
        if price > budget: return 0
        
        score = 45 
        if str(product['Marca']) in str(client.get('Brand_Affinity', '')):
            score += 40
        
        return score * psych_factor

    def _save_state(self):
        """Guarda el progreso del simulador."""
        self.live_inventory.to_csv(self.inventory_state_path, index=False)
        self.clients.to_csv(self.clients_state_path, index=False)
        
        if self.daily_metrics_buffer:
            df_metrics = pd.DataFrame(self.daily_metrics_buffer)
            df_metrics.to_csv(self.metrics_path, index=False)

    def generate_sales_data(self, days=365, macro_df=None):
        traffic_mean = settings.get("traffic_mean", 90) # Uso seguro de dict
        print(f"💼 Ejecutando Simulador V25 (Tráfico ~{traffic_mean}/día)...")
        
        start_date = datetime.today() - timedelta(days=days)
        if self.live_inventory.empty: self._restock_inventory(start_date, volume=350)

        sales_log = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            row_macro = macro_df.iloc[i] if macro_df is not None else {'Economic_Index':1, 'Luxury_Hype':1}
            e_idx, h_idx = row_macro['Economic_Index'], row_macro['Luxury_Hype']

            # Reposición diaria
            self._restock_inventory(current_date, volume=random.randint(8, 18))
            self.live_inventory.loc[self.live_inventory['Status'] == 'Available', 'Days_On_Market'] += 1
            
            # --- TRÁFICO CONTROLADO ---
            traffic = int(np.random.normal(traffic_mean, 4) * h_idx)
            traffic = max(int(traffic_mean * 0.8), min(int(traffic_mean * 1.2), traffic))
            
            active_clients = self.clients[self.clients['Current_Budget'] > 800]
            if not active_clients.empty:
                visitors = active_clients.sample(n=min(traffic, len(active_clients)), replace=True)
                stock = self.live_inventory[self.live_inventory['Status'] == 'Available']
                
                daily_revenue = 0
                for _, client in visitors.iterrows():
                    if stock.empty: break
                    prod = stock.sample(n=1).iloc[0]
                    
                    if self._calculate_affinity(client, prod, e_idx) > 52:
                        is_return = random.random() < 0.06
                        rev = prod['Current_Price']
                        
                        sale_entry = {
                            'Fecha': current_date, 
                            'Marca': prod['Marca'], 
                            'Net_Revenue': -rev if is_return else rev,
                            'Status': 'Returned' if is_return else 'Completed',
                            'Cluster': 'High_End' if prod['Marca'] in self.TIER_1_BRANDS else 'Standard'
                        }
                        sales_log.append(sale_entry)
                        daily_revenue += sale_entry['Net_Revenue']
                        
                        # Actualizar
                        self.live_inventory.loc[prod.name, 'Status'] = 'Sold'
                        self.clients.loc[client.name, 'Current_Budget'] -= rev
                        stock = self.live_inventory[self.live_inventory['Status'] == 'Available']

            self.daily_metrics_buffer.append({
                'Fecha': current_date, 'Revenue': daily_revenue, 'Traffic': traffic
            })

        self._save_state()
        return pd.DataFrame(sales_log)