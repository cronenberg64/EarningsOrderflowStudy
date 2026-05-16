import pandas as pd
import os

def create_minimal_lm_dict(out_path='data/lm_dict.csv'):
    data = [
        ['PROFIT', 0, 2026, 0, 0, 0, 0],
        ['LOSS', 2026, 0, 0, 0, 0, 0],
        ['GROWTH', 0, 2026, 0, 0, 0, 0],
        ['DECLINE', 2026, 0, 0, 0, 0, 0],
        ['SUCCESS', 0, 2026, 0, 0, 0, 0],
        ['FAILURE', 2026, 0, 0, 0, 0, 0],
        ['UNCERTAIN', 0, 0, 2026, 0, 0, 0],
        ['RISK', 0, 0, 2026, 0, 0, 0],
        ['LAWSUIT', 0, 0, 0, 2026, 0, 0],
        ['LITIGATION', 0, 0, 0, 2026, 0, 0],
        ['MUST', 0, 0, 0, 0, 2026, 0],
        ['ALWAYS', 0, 0, 0, 0, 2026, 0],
        ['MAY', 0, 0, 0, 0, 0, 2026],
        ['COULD', 0, 0, 0, 0, 0, 2026],
        ['BEAT', 0, 2026, 0, 0, 0, 0],
        ['MISS', 2026, 0, 0, 0, 0, 0],
        ['ABOVE', 0, 2026, 0, 0, 0, 0],
        ['BELOW', 2026, 0, 0, 0, 0, 0],
        ['INCREASE', 0, 2026, 0, 0, 0, 0],
        ['DECREASE', 2026, 0, 0, 0, 0, 0]
    ]
    df = pd.DataFrame(data, columns=['Word', 'Negative', 'Positive', 'Uncertainty', 'Litigious', 'Strong_Modal', 'Weak_Modal'])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Minimal LM dictionary created at {out_path}")

if __name__ == "__main__":
    create_minimal_lm_dict()
