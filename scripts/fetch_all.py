import os
import time
import pandas as pd
from datetime import timedelta
from src.data import (
    fetch_msft_earnings_dates, 
    fetch_8k_filing, 
    fetch_minute_bars, 
    download_lm_dictionary
)

def main():
    if not os.environ.get("POLYGON_API_KEY"):
        print("WARNING: POLYGON_API_KEY env var not set. fetch_minute_bars will fail.")

    # 1. Fetch earnings dates
    print("Fetching MSFT earnings dates...")
    events_df = fetch_msft_earnings_dates(5)
    
    event_results = []
    
    # Ensure directories exist
    os.makedirs('data/bars', exist_ok=True)
    os.makedirs('data/press_releases', exist_ok=True)
    
    for idx, row in events_df.iterrows():
        announce_date = row['announce_date']
        print(f"\nProcessing event: {announce_date.date()}")
        
        # 2a. Fetch 8-K filing
        try:
            filing = fetch_8k_filing(announce_date)
            filed_at = filing['filed_at']
            text = filing['text']
            print(f"  8-K filed at: {filed_at}")
        except Exception as e:
            print(f"  Error fetching 8-K for {announce_date}: {e}")
            continue
            
        # 2b. Define window [filed_at - 30min, filed_at + 90min]
        window_start = filed_at - timedelta(minutes=30)
        window_end = filed_at + timedelta(minutes=90)
        
        # 2c. Fetch minute bars
        print(f"  Fetching minute bars for window: {window_start} to {window_end}")
        time.sleep(0.15) # Stay under Polygon limit
        try:
            bars = fetch_minute_bars('MSFT', window_start, window_end)
            print(f"  Retrieved {len(bars)} bars.")
        except Exception as e:
            print(f"  Error fetching Polygon bars: {e}")
            bars = pd.DataFrame()
        
        # 2d. Save bars
        date_str = announce_date.strftime('%Y-%m-%d')
        if not bars.empty:
            bars_path = f"data/bars/event_{date_str}.parquet"
            bars.to_parquet(bars_path)
        
        # 2e. Save press release text
        pr_path = f"data/press_releases/event_{date_str}.txt"
        with open(pr_path, 'w') as f:
            f.write(text)
            
        event_results.append({
            'announce_date': announce_date,
            't_event': filed_at,
            'eps_actual': row['eps_actual'],
            'eps_estimate': row['eps_estimate'],
            'bar_count': len(bars),
            'word_count': len(text.split())
        })
        
        time.sleep(0.1) # Stay under SEC limit
        
    # 3. Build data/events.parquet
    if event_results:
        res_df = pd.DataFrame(event_results)
        res_df.to_parquet('data/events.parquet')
        
        # 5. Print summary
        print("\n" + "="*30)
        print("DATA ACQUISITION SUMMARY")
        print("="*30)
        print(res_df[['announce_date', 't_event', 'bar_count', 'word_count']])
    else:
        print("No events processed successfully.")
    
    # 4. Download LM dictionary if missing
    if not os.path.exists('data/lm_dict.csv'):
        print("\nDownloading LM dictionary...")
        try:
            download_lm_dictionary('data/lm_dict.csv')
            print("LM dictionary downloaded.")
        except Exception as e:
            print(f"Failed to download LM dictionary: {e}")

if __name__ == "__main__":
    main()
