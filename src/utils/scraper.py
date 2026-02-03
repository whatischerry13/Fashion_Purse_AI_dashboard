import requests
from bs4 import BeautifulSoup
import random
import time
from typing import Optional

class PriceMonitor:
    """
    Monitor de Competencia (Market Intelligence).
    Busca precios en tiempo real en marketplaces de segunda mano.
    """
    
    def __init__(self):
        # User-Agents rotatorios para evitar bloqueos básicos
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/89.0'
        ]

    def get_competitor_price(self, brand: str, model: str) -> Optional[float]:
        """
        Scrapea Google Shopping / Marketplaces para encontrar el precio actual.
        """
        search_query = f"{brand} {model} bag price"
        print(f"   🕵️‍♀️ Espiando mercado para: {search_query}...")
        
        # NOTA: En producción real usaríamos una API de scraping (ZenRows/ScraperAPI)
        # Para esta demo Zero-Cost, hacemos un intento directo con 'fallback'.
        
        # URL Genérica de búsqueda (simulada sobre un agregador)
        # Usamos DuckDuckGo HTML que es más amigable al scraping que Google
        url = f"https://html.duckduckgo.com/html/?q={search_query.replace(' ', '+')}"
        
        headers = {'User-Agent': random.choice(self.user_agents)}
        
        try:
            # Retardo ético
            time.sleep(random.uniform(0.5, 1.5))
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscamos patrones de precio en los resultados (ej: $12,500)
                text_content = soup.get_text()
                import re
                # Regex para encontrar precios en USD/EUR
                prices = re.findall(r'[\$\€]\s?([0-9]{1,3}(?:,[0-9]{3})*)', text_content)
                
                valid_prices = []
                for p in prices:
                    try:
                        val = float(p.replace(',', ''))
                        if val > 500: # Filtramos accesorios baratos
                            valid_prices.append(val)
                    except:
                        continue
                
                if valid_prices:
                    # Media de los primeros 3 precios encontrados
                    avg_price = sum(valid_prices[:3]) / len(valid_prices[:3])
                    return round(avg_price, 2)
            
            return None

        except Exception as e:
            print(f"   ⚠️ Scraping fallido ({e}). Usando precio base.")
            return None

# Instancia global
market_spy = PriceMonitor()