-- DIMENSION TABLES (Must be created first)
CREATE TABLE IF NOT EXISTS dim_company (
    symbol TEXT PRIMARY KEY,
    company_name TEXT,
    sector_id INTEGER,
    sub_sector TEXT,
    company_logo TEXT,
    website TEXT,
    nse_url TEXT,
    bse_url TEXT,
    face_value NUMERIC,
    book_value NUMERIC,
    about_company TEXT
);

CREATE TABLE IF NOT EXISTS dim_health_label (
    label_id INTEGER PRIMARY KEY,
    label_name TEXT,
    min_score NUMERIC,
    max_score NUMERIC,
    color_hex TEXT
);

CREATE TABLE IF NOT EXISTS dim_sector (
    sector_id INTEGER PRIMARY KEY,
    sector_name TEXT,
    sector_code TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS dim_year (
    year_id INTEGER PRIMARY KEY,
    year_label TEXT,
    fiscal_year INTEGER,
    quarter TEXT,
    is_ttm BOOLEAN,
    is_half_year BOOLEAN,
    sort_order INTEGER
);

-- FACT TABLES (With Foreign Keys)
CREATE TABLE IF NOT EXISTS fact_analysis (
    symbol TEXT REFERENCES dim_company(symbol),
    period_label TEXT,
    compounded_sales_growth_pct DOUBLE PRECISION,
    compounded_profit_growth_pct DOUBLE PRECISION,
    stock_price_cagr_pct DOUBLE PRECISION,
    roe_pct DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS fact_balance_sheet (
    symbol TEXT REFERENCES dim_company(symbol),
    year_id INTEGER REFERENCES dim_year(year_id),
    equity_capital DOUBLE PRECISION,
    reserves DOUBLE PRECISION,
    borrowings DOUBLE PRECISION,
    other_liabilities DOUBLE PRECISION,
    total_liabilities DOUBLE PRECISION,
    fixed_assets DOUBLE PRECISION,
    cwip DOUBLE PRECISION,
    investments DOUBLE PRECISION,
    other_asset DOUBLE PRECISION,
    total_assets DOUBLE PRECISION,
    debt_to_equity DOUBLE PRECISION,
    equity_ratio DOUBLE PRECISION,
    shares_outstanding DOUBLE PRECISION,
    book_value_per_share DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS fact_cash_flow (
    symbol TEXT REFERENCES dim_company(symbol),
    year_id INTEGER REFERENCES dim_year(year_id),
    operating_activity DOUBLE PRECISION,
    investing_activity DOUBLE PRECISION,
    financing_activity DOUBLE PRECISION,
    net_cash_flow DOUBLE PRECISION,
    free_cash_flow DOUBLE PRECISION,
    cash_conversion_ratio DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS fact_ml_scores (
    symbol TEXT REFERENCES dim_company(symbol),
    computed_at TIMESTAMPTZ,
    overall_score DOUBLE PRECISION,
    profitability_score DOUBLE PRECISION,
    growth_score DOUBLE PRECISION,
    leverage_score DOUBLE PRECISION,
    cashflow_score DOUBLE PRECISION,
    dividend_score DOUBLE PRECISION,
    trend_score DOUBLE PRECISION,
    health_label TEXT
);

CREATE TABLE IF NOT EXISTS fact_profit_loss (
    symbol TEXT REFERENCES dim_company(symbol),
    year_id INTEGER REFERENCES dim_year(year_id),
    sales DOUBLE PRECISION,
    expenses DOUBLE PRECISION,
    operating_profit DOUBLE PRECISION,
    opm_pct DOUBLE PRECISION,
    other_income DOUBLE PRECISION,
    interest DOUBLE PRECISION,
    depreciation DOUBLE PRECISION,
    profit_before_tax DOUBLE PRECISION,
    tax_pct DOUBLE PRECISION,
    net_profit DOUBLE PRECISION,
    eps DOUBLE PRECISION,
    dividend_payout_pct DOUBLE PRECISION,
    net_profit_margin_pct DOUBLE PRECISION,
    expense_ratio_pct DOUBLE PRECISION,
    interest_coverage DOUBLE PRECISION,
    asset_turnover DOUBLE PRECISION,
    return_on_assets DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS fact_pros_cons (
    symbol TEXT REFERENCES dim_company(symbol),
    is_pro BOOLEAN,
    category TEXT,
    text TEXT,
    source TEXT,
    confidence DOUBLE PRECISION,
    generated_at TIMESTAMPTZ
);