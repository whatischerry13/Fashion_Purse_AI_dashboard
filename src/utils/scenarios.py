import pandas as pd
import numpy as np
from datetime import datetime

def generate_macro_context(days=730, trend_bias=1.0, hype_bias=1.0):
    """
    trend_bias: < 1.0 para forzar crisis, > 1.0 para forzar boom.
    hype_bias: multiplicador de volatilidad/viralidad.
    """
    dates = pd.date_range(end=datetime.today(), periods=days)
    
    # Ciclo Económico con Sesgo del Usuario
    x = np.arange(days)
    cycle = (1.0 + 0.15 * np.sin(2 * np.pi * x / (365*3))) * trend_bias
    noise = np.random.normal(0, 0.02, days)
    economic_index = cycle + noise
    
    # Hype con Sesgo del Usuario
    hype_series = []
    h_val = 1.0
    for _ in range(days):
        h_val += np.random.normal(0, 0.05 * hype_bias)
        h_val += (1.0 - h_val) * 0.03 # Reversión a la media
        hype_series.append(max(0.6, min(1.8, h_val)))
        
    df = pd.DataFrame({
        'Fecha': dates,
        'Economic_Index': economic_index,
        'Luxury_Hype': hype_series
    })
    return df