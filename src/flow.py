import pandas as pd
import numpy as np

def tick_rule_sign(returns: pd.Series) -> pd.Series:
    """
    Apply Lee-Ready tick rule: +1 if return > 0, -1 if return < 0, 
    else use prior sign.
    """
    signs = np.sign(returns)
    # Replace 0 with NaN and forward fill to carry prior sign
    signs = signs.replace(0, np.nan).ffill().fillna(0)
    return signs

def signed_volume(bars: pd.DataFrame) -> pd.Series:
    """
    Compute tick-rule signed volume from minute bars.
    """
    # Compute returns (log returns preferred for symmetry)
    returns = np.log(bars['close'] / bars['close'].shift(1)).fillna(0)
    signs = tick_rule_sign(returns)
    return signs * bars['volume']

def cvd(bars: pd.DataFrame, reset_at: pd.Timestamp = None) -> pd.Series:
    """
    Compute cumulative signed volume. 
    If reset_at is provided, start accumulation from that timestamp.
    """
    sv = signed_volume(bars)
    if reset_at:
        # Reset values before reset_at to 0 so the cumsum starts fresh
        sv_copy = sv.copy()
        mask = bars['t'] < reset_at
        sv_copy.loc[mask] = 0
        return sv_copy.cumsum()
    return sv.cumsum()

def realized_vol_rolling(returns: pd.Series, window: int = 5) -> pd.Series:
    """
    Compute rolling realized volatility: sqrt(sum(r^2)).
    Keep in per-minute units as requested.
    """
    return np.sqrt((returns**2).rolling(window=window).sum())

def spread_proxy(bars: pd.DataFrame) -> pd.Series:
    """
    Corwin-Schultz-style bid-ask spread proxy from high/low.
    Formula: 2 * (H - L) / (H + L)
    """
    return 2 * (bars['high'] - bars['low']) / (bars['high'] + bars['low'])
