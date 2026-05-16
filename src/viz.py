import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats

# Global style settings for premium dark theme
plt.style.use('dark_background')
plt.rcParams.update({
    'axes.facecolor': '#0d1117',
    'figure.facecolor': '#0d1117',
    'grid.color': '#30363d',
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'axes.edgecolor': '#30363d',
    'xtick.color': '#8b949e',
    'ytick.color': '#8b949e'
})

def plot_event_signature(avg_df, col_base, ylabel, title, out_path):
    """Plot a single variable's averaged response with SE band."""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    mean = avg_df[f'{col_base}_mean']
    sem = avg_df[f'{col_base}_sem']
    tau = avg_df.index
    
    ax.plot(tau, mean, color='tab:cyan', lw=2)
    ax.fill_between(tau, mean - sem, mean + sem, color='tab:cyan', alpha=0.2)
    
    ax.axvline(0, color='white', linestyle='--', alpha=0.5)
    ax.set_xlabel('Minutes from Event (τ)')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def plot_all_signatures(avg_df, out_path):
    """4-panel hero plot for the README."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('EarningsOrderflowStudy — Averaged MSFT Earnings Response (N=5)', fontsize=16, color='white')
    
    # 1. Cumulative Return
    axes[0,0].plot(avg_df.index, avg_df['cum_return_mean'], color='tab:cyan', lw=2)
    axes[0,0].fill_between(avg_df.index, avg_df['cum_return_mean'] - avg_df['cum_return_sem'], 
                           avg_df['cum_return_mean'] + avg_df['cum_return_sem'], color='tab:cyan', alpha=0.2)
    axes[0,0].set_title('Cumulative Log Return')
    axes[0,0].set_ylabel('Return')
    
    # 2. Volume (Log Scale)
    axes[0,1].plot(avg_df.index, avg_df['volume_mean'], color='tab:orange', lw=2)
    axes[0,1].set_yscale('log')
    axes[0,1].set_title('Averaged Volume (Log Scale)')
    axes[0,1].set_ylabel('Shares')
    
    # 3. CVD
    axes[1,0].plot(avg_df.index, avg_df['cvd_mean'], color='tab:green', lw=2)
    axes[1,0].fill_between(avg_df.index, avg_df['cvd_mean'] - avg_df['cvd_sem'], 
                           avg_df['cvd_mean'] + avg_df['cvd_sem'], color='tab:green', alpha=0.2)
    axes[1,0].set_title('Cumulative Signed Volume (CVD Proxy)')
    axes[1,0].set_ylabel('Signed Shares')
    
    # 4. Realized Vol
    axes[1,1].plot(avg_df.index, avg_df['rv5_mean'], color='tab:red', lw=2)
    axes[1,1].fill_between(avg_df.index, avg_df['rv5_mean'] - avg_df['rv5_sem'], 
                           avg_df['rv5_mean'] + avg_df['rv5_sem'], color='tab:red', alpha=0.2)
    axes[1,1].set_title('Realized Volatility (Rolling 5-min)')
    axes[1,1].set_ylabel('Std Dev')
    
    for ax in axes.flat:
        ax.axvline(0, color='white', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.1)
        ax.set_xlabel('τ (min)')
        
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(out_path, dpi=150)
    plt.close()

def plot_cross_event_scatter(events_df, panel, out_path):
    """Scatter plots linking sentiment/surprise to response magnitude."""
    # Get response at tau=30 (settled jump)
    resp_30 = panel.xs(30, level='tau')['cum_return']
    
    df = events_df.copy()
    df['date_str'] = df['announce_date'].dt.strftime('%Y-%m-%d')
    df = df.set_index('date_str')
    df['response'] = resp_30
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Sentiment vs Response
    x1 = df['net_sentiment']
    y = df['response']
    ax1.scatter(x1, y, color='tab:cyan', s=100, edgecolors='white', alpha=0.8)
    for i, txt in enumerate(df.index):
        ax1.annotate(txt, (x1.iloc[i], y.iloc[i]), xytext=(5,5), textcoords='offset points', fontsize=9)
    
    slope1, intercept1, r1, p1, se1 = stats.linregress(x1, y)
    ax1.plot(x1, intercept1 + slope1*x1, color='tab:red', linestyle='--', alpha=0.5)
    ax1.set_title(f'Sentiment vs Response (R²={r1**2:.2f})')
    ax1.set_xlabel('L-McD Net Sentiment')
    ax1.set_ylabel('Cumulative Return at τ=30')
    
    # EPS Surprise vs Response
    df['surprise'] = (df['eps_actual'] - df['eps_estimate']) / df['eps_estimate'].abs()
    x2 = df['surprise']
    ax2.scatter(x2, y, color='tab:orange', s=100, edgecolors='white', alpha=0.8)
    for i, txt in enumerate(df.index):
        ax2.annotate(txt, (x2.iloc[i], y.iloc[i]), xytext=(5,5), textcoords='offset points', fontsize=9)
        
    slope2, intercept2, r2, p2, se2 = stats.linregress(x2, y)
    ax2.plot(x2, intercept2 + slope2*x2, color='tab:red', linestyle='--', alpha=0.5)
    ax2.set_title(f'EPS Surprise vs Response (R²={r2**2:.2f})')
    ax2.set_xlabel('Standardized EPS Surprise')
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def plot_all_events_overlay(per_event_cum, out_path):
    """Show individual variation across events."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    per_event_cum.plot(ax=ax, cmap='viridis', lw=1.5, alpha=0.8)
    ax.axvline(0, color='white', linestyle='--', alpha=0.5)
    ax.set_title('Per-Event Cumulative Return Overlays', fontsize=14)
    ax.set_xlabel('Minutes from Event (τ)')
    ax.set_ylabel('Cum Log Return')
    ax.legend(title='Event Date', bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    ax.grid(True, alpha=0.1)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
