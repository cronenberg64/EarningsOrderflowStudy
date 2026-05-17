import os
import sys
import pandas as pd
import numpy as np

# Ensure parent directory is in path
sys.path.append('.')

from src.sentiment import score_lm
from src.event_study import build_event_panel, cross_event_average, cumulative_return_per_event
from src.viz import plot_all_signatures, plot_cross_event_scatter, plot_all_events_overlay

def main():
    print("Re-running EarningsOrderflowStudy analysis pipeline...")
    
    # 1. Load data
    events_df = pd.read_parquet('data/events.parquet')
    
    # Check if we have the real LM dictionary or fallback
    lm_dict = pd.read_csv('data/lm_dict.csv')
    print(f"Loaded LM dictionary with {len(lm_dict)} words.")
    
    # 2. Score Sentiment
    sentiment_results = []
    for idx, row in events_df.iterrows():
        date_str = row['announce_date'].strftime('%Y-%m-%d')
        pr_path = f'data/press_releases/event_{date_str}.txt'
        with open(pr_path, 'r') as f:
            text = f.read()
        
        scores = score_lm(text, lm_dict)
        scores['announce_date'] = row['announce_date']
        sentiment_results.append(scores)
        
    sent_df = pd.DataFrame(sentiment_results)
    
    # Drop any pre-existing sentiment columns if present
    cols_to_drop = [c for c in sent_df.columns if c in events_df.columns and c != 'announce_date']
    if cols_to_drop:
        events_df = events_df.drop(columns=cols_to_drop)
        
    events_df = events_df.merge(sent_df, on='announce_date')
    events_df.to_parquet('data/events_augmented.parquet')
    print("Sentiment scoring completed and saved to data/events_augmented.parquet.")
    print("Augmented events overview:")
    print(events_df[['announce_date', 'net_sentiment', 'eps_actual', 'eps_estimate']])
    
    # 3. Build Panel and Compute Averages
    panel = build_event_panel(events_df, bars_dir='data/bars/')
    avg_df = cross_event_average(panel, ['log_return', 'volume', 'cvd', 'rv5', 'spread', 'cum_return'])
    per_event_cum = cumulative_return_per_event(panel)
    print("Event panel and averages constructed.")
    
    # Ensure outputs directory exists
    os.makedirs('outputs', exist_ok=True)
    
    # 4. Generate Visualizations
    print("Generating updated event signatures plot...")
    plot_all_signatures(avg_df, 'outputs/event_signature.png')
    
    print("Generating updated cross-event scatter plots...")
    plot_cross_event_scatter(events_df, panel, 'outputs/cross_event_scatter.png')
    
    print("Generating updated per-event overlay plots...")
    plot_all_events_overlay(per_event_cum, 'outputs/all_events_overlay.png')
    
    print("Analysis pipeline recompute complete!")

if __name__ == "__main__":
    main()
