import os
import time
import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
from polygon import RESTClient
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

def fetch_msft_earnings_dates(n=5):
    """
    Use yfinance Ticker('MSFT').earnings_dates to get the last n actual earnings.
    Return columns: announce_date (datetime, ET timezone), eps_actual (float), eps_estimate (float).
    """
    msft = yf.Ticker("MSFT")
    df = msft.earnings_dates
    
    # Filter out future dates (where actual is NaN)
    df = df[df['Reported EPS'].notna()].copy()
    
    # Sort descending, take top n
    df = df.sort_index(ascending=False).head(n)
    
    # Reset index and rename columns
    df = df.reset_index()
    df = df.rename(columns={
        'Earnings Date': 'announce_date',
        'Reported EPS': 'eps_actual',
        'EPS Estimate': 'eps_estimate'
    })
    
    # Ensure ET timezone
    et = pytz.timezone('US/Eastern')
    df['announce_date'] = df['announce_date'].dt.tz_convert(et)
    
    return df[['announce_date', 'eps_actual', 'eps_estimate']]

def fetch_8k_filing(announce_date, cik='0000789019'):
    """
    For MSFT (CIK 0000789019), find the 8-K filed within ±2 days of announce_date.
    Returns {'filed_at': pd.Timestamp (UTC), 'text': str, 'accession': str}.
    """
    headers = {'User-Agent': 'Jonathan Setiawan jonathan@example.com'}
    cik_padded = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    recent_filings = data['filings']['recent']
    
    # Find 8-K matching date window
    target_date = announce_date.date()
    match_idx = None
    
    for i, (form, filed_date) in enumerate(zip(recent_filings['form'], recent_filings['filingDate'])):
        if form == '8-K':
            f_date = datetime.strptime(filed_date, '%Y-%m-%d').date()
            if abs((f_date - target_date).days) <= 2:
                match_idx = i
                break
    
    if match_idx is None:
        raise ValueError(f"No 8-K found for {announce_date}")
    
    accession = recent_filings['accessionNumber'][match_idx].replace('-', '')
    primary_doc = recent_filings['primaryDocument'][match_idx]
    
    # Fetch filing index to find Exhibit 99.1
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json"
    time.sleep(0.1)
    idx_resp = requests.get(index_url, headers=headers)
    idx_resp.raise_for_status()
    idx_data = idx_resp.json()
    
    exhibit_path = None
    for file in idx_data['directory']['item']:
        name_lower = file['name'].lower()
        if any(x in name_lower for x in ['99.1', '99_1', 'ex99']) and name_lower.endswith(('.htm', '.html', '.txt')):
            exhibit_path = file['name']
            break
            
    if not exhibit_path:
        exhibit_path = primary_doc # Fallback to primary 8-K if 99.1 not explicit
        
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{exhibit_path}"
    time.sleep(0.1)
    doc_resp = requests.get(doc_url, headers=headers)
    doc_resp.raise_for_status()
    
    soup = BeautifulSoup(doc_resp.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    # Use acceptanceDateTime for higher precision if available
    acceptance_dt = recent_filings.get('acceptanceDateTime', [None]*len(recent_filings['form']))[match_idx]
    if acceptance_dt:
        filed_at = pd.to_datetime(acceptance_dt).tz_convert('UTC')
    else:
        filed_at = pd.to_datetime(recent_filings['filingDate'][match_idx]).tz_localize('UTC')
    
    return {
        'filed_at': filed_at,
        'text': text,
        'accession': accession
    }

def fetch_minute_bars(ticker, start, end):
    """
    Use polygon-api-client Aggs.get_aggs for minute bars.
    """
    client = RESTClient(os.environ.get("POLYGON_API_KEY"))
    
    # Polygon expects timestamps in milliseconds or date strings
    # We'll use datetime objects directly if client supports it, or convert
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    
    aggs = client.get_aggs(
        ticker, 1, "minute", start_ms, end_ms,
        adjusted=True, limit=50000
    )
    
    df = pd.DataFrame(aggs)
    if df.empty:
        return df
        
    df['t'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df = df.rename(columns={
        'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close',
        'volume': 'volume', 'vwap': 'vwap', 'transactions': 'transactions'
    })
    
    # Convert to ET
    et = pytz.timezone('US/Eastern')
    df['t_et'] = df['t'].dt.tz_convert(et)
    
    return df[['t', 't_et', 'open', 'high', 'low', 'close', 'volume', 'transactions']]

def download_lm_dictionary(out_path='data/lm_dict.csv'):
    """
    Download Loughran-McDonald master dictionary, or extract it from pysentiment2 if available.
    """
    try:
        import pysentiment2 as ps
        import os
        lm = ps.LM()
        dict_file = getattr(lm, 'PATH', None)
        if dict_file and os.path.exists(dict_file):
            print(f"Extracting Loughran-McDonald dictionary from pysentiment2 static data: {dict_file}")
            df = pd.read_csv(dict_file)
            out_df = pd.DataFrame()
            out_df['Word'] = df['Word']
            out_df['Negative'] = df['Negative']
            out_df['Positive'] = df['Positive']
            out_df['Uncertainty'] = df['Uncertainty']
            out_df['Litigious'] = df['Litigious']
            # Map Modal values: 1 = Strong, 3 = Weak
            out_df['Strong_Modal'] = (df['Modal'] == 1).astype(int) * 2009
            out_df['Weak_Modal'] = (df['Modal'] == 3).astype(int) * 2009
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            out_df.to_csv(out_path, index=False)
            return out_df
    except Exception as e:
        print(f"pysentiment2 extraction failed ({e}), falling back to direct URL...")
        
    # Fallback raw GitHub URL
    url = "https://raw.githubusercontent.com/marcus-patterson/LoughranMcDonald_MasterDictionary/master/LoughranMcDonald_MasterDictionary_2018.csv"
    resp = requests.get(url)
    resp.raise_for_status()
    
    with open(out_path, 'wb') as f:
        f.write(resp.content)
        
    df = pd.read_csv(out_path)
    cols = ['Word', 'Negative', 'Positive', 'Uncertainty', 'Litigious', 'Strong_Modal', 'Weak_Modal']
    df = df[cols]
    
    return df

