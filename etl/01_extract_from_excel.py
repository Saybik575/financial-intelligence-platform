import pandas as pd

files = {
    "companies": "data/raw/companies.xlsx",
    "balancesheet": "data/raw/balancesheet.xlsx",
    "cashflow": "data/raw/cashflow.xlsx",
    "profitandloss": "data/raw/profitandloss.xlsx",
    "analysis": "data/raw/analysis.xlsx",
    "documents": "data/raw/documents.xlsx",
    "prosandcons": "data/raw/prosandcons.xlsx"
}

data = {}

for name, path in files.items():
    df = pd.read_excel(path)
    data[name] = df
    
    print(f"\n{name.upper()}")
    print(df.shape)
    print(df.columns)