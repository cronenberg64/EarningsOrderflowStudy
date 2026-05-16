import os
import sys
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.append('.')

from src.sentiment import score_lm
from src.event_study import build_event_panel, cross_event_average, cumulative_return_per_event
from src.viz import plot_all_signatures, plot_cross_event_scatter, plot_all_events_overlay

def main():
    os.makedirs('outputs', exist_ok=True)
    
    # 1. Load data
    print("Loading data...")
    events_df = pd.read_parquet('data/events.parquet')
    lm_dict = pd.read_csv('data/lm_dict.csv')
    
    # 2. Score Sentiment
    print("Scoring sentiment...")
    sentiment_results = []
    for idx, row in events_df.iterrows():
        date_str = row['announce_date'].strftime('%Y-%m-%d')
        pr_path = f'data/press_releases/event_{date_str}.txt'
        if os.path.exists(pr_path):
            with open(pr_path, 'r') as f:
                text = f.read()
            scores = score_lm(text, lm_dict)
            scores['announce_date'] = row['announce_date']
            sentiment_results.append(scores)
            
    sent_df = pd.DataFrame(sentiment_results)
    events_df = events_df.merge(sent_df, on='announce_date')
    
    # 3. Build Panel
    print("Building event panel...")
    panel = build_event_panel(events_df, bars_dir='data/bars/')
    
    # 4. Compute Averages
    print("Computing averages...")
    avg_df = cross_event_average(panel, ['log_return', 'volume', 'cvd', 'rv5', 'spread', 'cum_return'])
    per_event_cum = cumulative_return_per_event(panel)
    
    # 5. Generate Plots
    print("Generating plots...")
    plot_all_signatures(avg_df, 'outputs/event_signature.png')
    plot_cross_event_scatter(events_df, panel, 'outputs/cross_event_scatter.png')
    plot_all_events_overlay(per_event_cum, 'outputs/all_events_overlay.png')
    
    print("Analysis complete. Plots saved to outputs/")

if __name__ == "__main__":
    main()
