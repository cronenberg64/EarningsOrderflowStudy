import pandas as pd
import string
import re

def score_lm(text: str, lm_dict: pd.DataFrame) -> dict:
    """
    Tokenize press release text and score against Loughran-McDonald categories.
    """
    # Tokenize: lowercase, strip punctuation, split, drop short tokens
    text = text.lower()
    # Remove punctuation using regex for efficiency
    text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
    tokens = [t for t in text.split() if len(t) >= 2]
    
    n_total = len(tokens)
    if n_total == 0:
        return {'n_total': 0, 'net_sentiment': 0}

    results = {'n_total': n_total}
    categories = ['Negative', 'Positive', 'Uncertainty', 'Litigious', 'Strong_Modal', 'Weak_Modal']
    
    # Pre-process dictionary for faster lookup (word -> set of categories)
    # The LM dict has words in uppercase usually
    lm_dict['Word'] = lm_dict['Word'].str.lower()
    
    for cat in categories:
        # Get set of words for this category where value is non-zero
        cat_words = set(lm_dict[lm_dict[cat] > 0]['Word'])
        count = sum(1 for t in tokens if t in cat_words)
        results[f'n_{cat.lower()[:3]}'] = count
        results[f'{cat.lower()[:3]}_pct'] = count / n_total

    # Calculate net sentiment (pos - neg)
    results['net_sentiment'] = results.get('pos_pct', 0) - results.get('neg_pct', 0)
    
    return results
