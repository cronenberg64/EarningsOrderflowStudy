import pandas as pd
import numpy as np
import os
from src.flow import signed_volume, cvd, realized_vol_rolling, spread_proxy

def build_event_panel(events_df: pd.DataFrame, bars_dir: str = 'data/bars/') -> pd.DataFrame:
    """
    Build a long-form event panel with time-from-event (tau) and computed features.
    """
    panel_list = []
    
    for _, row in events_df.iterrows():
        date_str = row['announce_date'].strftime('%Y-%m-%d')
        file_path = os.path.join(bars_dir, f'event_{date_str}.parquet')
        
        if not os.path.exists(file_path):
            continue
            
        bars = pd.read_parquet(file_path)
        t_event = row['t_event']
        
        # 1. Compute tau: minutes from event (rounded to integer)
        # Convert both to UTC for subtraction
        bars['t'] = pd.to_datetime(bars['t']).dt.tz_convert('UTC')
        t_event = pd.to_datetime(t_event).tz_convert('UTC')
        
        bars['tau'] = ((bars['t'] - t_event).dt.total_seconds() / 60).round().astype(int)
        
        # 2. Filter to window [-30, 90]
        bars = bars[(bars['tau'] >= -30) & (bars['tau'] <= 90)].copy()
        
        # 3. Compute per-bar features
        bars['log_return'] = np.log(bars['close'] / bars['close'].shift(1)).fillna(0)
        bars['signed_vol'] = signed_volume(bars)
        bars['cvd'] = cvd(bars, reset_at=bars[bars['tau'] == -30]['t'].min())
        bars['rv5'] = realized_vol_rolling(bars['log_return'], window=5)
        bars['spread'] = spread_proxy(bars)
        
        # Cumulative return starting from tau=-30
        bars['cum_return'] = bars['log_return'].cumsum()
        
        # Add metadata
        bars['event_id'] = date_str
        
        panel_list.append(bars)
        
    if not panel_list:
        return pd.DataFrame()
        
    panel = pd.concat(panel_list)
    return panel.set_index(['event_id', 'tau'])

def cross_event_average(panel: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Compute mean and standard error across events for specified columns.
    """
    # Group by tau and aggregate
    stats = panel.groupby('tau')[columns].agg(['mean', 'sem'])
    
    # Flatten multi-index columns: 'col_mean', 'col_sem'
    stats.columns = [f"{col}_{stat}" for col, stat in stats.columns]
    
    return stats

def cumulative_return_per_event(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Reshape cumulative returns to wide format: rows = tau, columns = event_id.
    """
    return panel['cum_return'].unstack(level=0)
