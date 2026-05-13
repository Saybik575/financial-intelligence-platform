from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


load_dotenv()

db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_port = os.getenv("DB_PORT")

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=db_user,
    password=db_password,
    host=db_host,
    port=int(db_port) if db_port else None,
    database=db_name,
)

engine = create_engine(db_url)
ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT / "data" / "clean"


def load_dim_company() -> None:
    df = pd.read_csv(CLEAN_DIR / "dim_company.csv")
    target_cols = [
        "symbol",
        "company_name",
        "sector_id",
        "sub_sector",
        "company_logo",
        "website",
        "nse_url",
        "bse_url",
        "face_value",
        "book_value",
        "about_company",
    ]
    df = df[target_cols].where(pd.notna(df[target_cols]), None)
    # Ensure one row per symbol before upserting into the PK-constrained table.
    df = df.drop_duplicates(subset=["symbol"], keep="last")
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO dim_company (
            symbol, company_name, sector_id, sub_sector, company_logo,
            website, nse_url, bse_url, face_value, book_value, about_company
        )
        VALUES (
            :symbol, :company_name, :sector_id, :sub_sector, :company_logo,
            :website, :nse_url, :bse_url, :face_value, :book_value, :about_company
        )
        ON CONFLICT (symbol) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            sector_id = EXCLUDED.sector_id,
            sub_sector = EXCLUDED.sub_sector,
            company_logo = EXCLUDED.company_logo,
            website = EXCLUDED.website,
            nse_url = EXCLUDED.nse_url,
            bse_url = EXCLUDED.bse_url,
            face_value = EXCLUDED.face_value,
            book_value = EXCLUDED.book_value,
            about_company = EXCLUDED.about_company
        """
    )

    with engine.begin() as conn:
        before_count = conn.execute(text("SELECT COUNT(*) FROM dim_company")).scalar_one()
        print(f"Rows in dim_company before load: {before_count}")
        conn.execute(upsert_sql, records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM dim_company")).scalar_one()
        print(f"Rows in dim_company after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")


def load_dim_health_label() -> None:
    df = pd.read_csv(CLEAN_DIR / "dim_health_label.csv")
    target_cols = ["label_id", "label_name", "min_score", "max_score", "color_hex"]
    df = df[target_cols].where(pd.notna(df[target_cols]), None)
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO dim_health_label (
            label_id, label_name, min_score, max_score, color_hex
        )
        VALUES (
            :label_id, :label_name, :min_score, :max_score, :color_hex
        )
        ON CONFLICT (label_id) DO UPDATE SET
            label_name = EXCLUDED.label_name,
            min_score = EXCLUDED.min_score,
            max_score = EXCLUDED.max_score,
            color_hex = EXCLUDED.color_hex
        """
    )

    with engine.begin() as conn:
        before_count = conn.execute(text("SELECT COUNT(*) FROM dim_health_label")).scalar_one()
        print(f"Rows in dim_health_label before load: {before_count}")
        conn.execute(upsert_sql, records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM dim_health_label")).scalar_one()
        print(f"Rows in dim_health_label after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")


def load_dim_sector() -> None:
    df = pd.read_csv(CLEAN_DIR / "dim_sector.csv")
    target_cols = ["sector_id", "sector_name", "sector_code", "description"]
    df = df[target_cols].where(pd.notna(df[target_cols]), None)
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO dim_sector (
            sector_id, sector_name, sector_code, description
        )
        VALUES (
            :sector_id, :sector_name, :sector_code, :description
        )
        ON CONFLICT (sector_id) DO UPDATE SET
            sector_name = EXCLUDED.sector_name,
            sector_code = EXCLUDED.sector_code,
            description = EXCLUDED.description
        """
    )

    with engine.begin() as conn:
        before_count = conn.execute(text("SELECT COUNT(*) FROM dim_sector")).scalar_one()
        print(f"Rows in dim_sector before load: {before_count}")
        conn.execute(upsert_sql, records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM dim_sector")).scalar_one()
        print(f"Rows in dim_sector after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")


def load_dim_year() -> None:
    df = pd.read_csv(CLEAN_DIR / "dim_year.csv")
    target_cols = ["year_id", "year_label", "fiscal_year", "quarter", "is_ttm", "is_half_year", "sort_order"]
    df = df[target_cols].astype(object).where(pd.notna(df[target_cols]), None)
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO dim_year (
            year_id, year_label, fiscal_year, quarter, is_ttm, is_half_year, sort_order
        )
        VALUES (
            :year_id, :year_label, :fiscal_year, :quarter, :is_ttm, :is_half_year, :sort_order
        )
        ON CONFLICT (year_id) DO UPDATE SET
            year_label = EXCLUDED.year_label,
            fiscal_year = EXCLUDED.fiscal_year,
            quarter = EXCLUDED.quarter,
            is_ttm = EXCLUDED.is_ttm,
            is_half_year = EXCLUDED.is_half_year,
            sort_order = EXCLUDED.sort_order
        """
    )

    with engine.begin() as conn:
        before_count = conn.execute(text("SELECT COUNT(*) FROM dim_year")).scalar_one()
        print(f"Rows in dim_year before load: {before_count}")
        conn.execute(upsert_sql, records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM dim_year")).scalar_one()
        print(f"Rows in dim_year after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")


def load_fact_analysis() -> None:
    df = pd.read_csv(CLEAN_DIR / "fact_analysis.csv")
    target_cols = [
        "symbol",
        "period_label",
        "compounded_sales_growth_pct",
        "compounded_profit_growth_pct",
        "stock_price_cagr_pct",
        "roe_pct",
    ]
    df = df[target_cols].astype(object).where(pd.notna(df[target_cols]), None)

    upsert_sql = text(
        """
        INSERT INTO fact_analysis (
            symbol, period_label, compounded_sales_growth_pct, compounded_profit_growth_pct, stock_price_cagr_pct, roe_pct
        )
        VALUES (
            :symbol, :period_label, :compounded_sales_growth_pct, :compounded_profit_growth_pct, :stock_price_cagr_pct, :roe_pct
        )
        ON CONFLICT (symbol, period_label) DO UPDATE SET
            compounded_sales_growth_pct = EXCLUDED.compounded_sales_growth_pct,
            compounded_profit_growth_pct = EXCLUDED.compounded_profit_growth_pct,
            stock_price_cagr_pct = EXCLUDED.stock_price_cagr_pct,
            roe_pct = EXCLUDED.roe_pct
        """
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_analysis_symbol_period
                ON fact_analysis (symbol, period_label)
                """
            )
        )
        before_count = conn.execute(text("SELECT COUNT(*) FROM fact_analysis")).scalar_one()
        print(f"Rows in fact_analysis before load: {before_count}")

        valid_symbols = {row[0] for row in conn.execute(text("SELECT symbol FROM dim_company"))}
        valid_df = df[df["symbol"].isin(valid_symbols)].copy()
        skipped_symbols = sorted(set(df["symbol"]) - valid_symbols)
        records = valid_df.to_dict(orient="records")

        if skipped_symbols:
            print(f"Skipped symbols (not found in dim_company): {', '.join(skipped_symbols)}")
        if records:
            conn.execute(upsert_sql, records)

        after_count = conn.execute(text("SELECT COUNT(*) FROM fact_analysis")).scalar_one()
        print(f"Rows in fact_analysis after load:  {after_count}")
        print(f"CSV rows processed: {len(df)}")
        print(f"Rows loaded/upserted: {len(records)}")


def load_fact_balance_sheet() -> None:
    df = pd.read_csv(CLEAN_DIR / "fact_balance_sheet.csv")
    target_cols = [
        "symbol",
        "year_id",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
        "debt_to_equity",
        "equity_ratio",
        "shares_outstanding",
        "book_value_per_share",
    ]
    df = df[target_cols].astype(object).where(pd.notna(df[target_cols]), None)
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO fact_balance_sheet (
            symbol, year_id, equity_capital, reserves, borrowings, other_liabilities,
            total_liabilities, fixed_assets, cwip, investments, other_asset, total_assets,
            debt_to_equity, equity_ratio, shares_outstanding, book_value_per_share
        )
        VALUES (
            :symbol, :year_id, :equity_capital, :reserves, :borrowings, :other_liabilities,
            :total_liabilities, :fixed_assets, :cwip, :investments, :other_asset, :total_assets,
            :debt_to_equity, :equity_ratio, :shares_outstanding, :book_value_per_share
        )
        ON CONFLICT (symbol, year_id) DO UPDATE SET
            equity_capital = EXCLUDED.equity_capital,
            reserves = EXCLUDED.reserves,
            borrowings = EXCLUDED.borrowings,
            other_liabilities = EXCLUDED.other_liabilities,
            total_liabilities = EXCLUDED.total_liabilities,
            fixed_assets = EXCLUDED.fixed_assets,
            cwip = EXCLUDED.cwip,
            investments = EXCLUDED.investments,
            other_asset = EXCLUDED.other_asset,
            total_assets = EXCLUDED.total_assets,
            debt_to_equity = EXCLUDED.debt_to_equity,
            equity_ratio = EXCLUDED.equity_ratio,
            shares_outstanding = EXCLUDED.shares_outstanding,
            book_value_per_share = EXCLUDED.book_value_per_share
        """
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_balance_sheet_symbol_year
                ON fact_balance_sheet (symbol, year_id)
                """
            )
        )
        before_count = conn.execute(text("SELECT COUNT(*) FROM fact_balance_sheet")).scalar_one()
        print(f"Rows in fact_balance_sheet before load: {before_count}")
        valid_symbols = {row[0] for row in conn.execute(text("SELECT symbol FROM dim_company"))}
        valid_records = [record for record in records if record["symbol"] in valid_symbols]
        skipped_symbols = sorted({record["symbol"] for record in records} - valid_symbols)
        if skipped_symbols:
            print(f"Skipped symbols (not found in dim_company): {', '.join(skipped_symbols)}")
        if valid_records:
            conn.execute(upsert_sql, valid_records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM fact_balance_sheet")).scalar_one()
        print(f"Rows in fact_balance_sheet after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")
        print(f"Rows loaded/upserted: {len(valid_records)}")


def load_fact_cash_flow() -> None:
    df = pd.read_csv(CLEAN_DIR / "fact_cash_flow.csv")
    target_cols = [
        "symbol",
        "year_id",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
        "free_cash_flow",
        "cash_conversion_ratio",
    ]
    df = df[target_cols].astype(object).where(pd.notna(df[target_cols]), None)
    # The cleaned CSV still contains repeated symbol/year rows for some companies.
    # Keep the last occurrence so the upsert sees one row per natural key.
    df = df.drop_duplicates(subset=["symbol", "year_id"], keep="last")
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO fact_cash_flow (
            symbol, year_id, operating_activity, investing_activity, financing_activity,
            net_cash_flow, free_cash_flow, cash_conversion_ratio
        )
        VALUES (
            :symbol, :year_id, :operating_activity, :investing_activity, :financing_activity,
            :net_cash_flow, :free_cash_flow, :cash_conversion_ratio
        )
        ON CONFLICT (symbol, year_id) DO UPDATE SET
            operating_activity = EXCLUDED.operating_activity,
            investing_activity = EXCLUDED.investing_activity,
            financing_activity = EXCLUDED.financing_activity,
            net_cash_flow = EXCLUDED.net_cash_flow,
            free_cash_flow = EXCLUDED.free_cash_flow,
            cash_conversion_ratio = EXCLUDED.cash_conversion_ratio
        """
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_cash_flow_symbol_year
                ON fact_cash_flow (symbol, year_id)
                """
            )
        )
        before_count = conn.execute(text("SELECT COUNT(*) FROM fact_cash_flow")).scalar_one()
        print(f"Rows in fact_cash_flow before load: {before_count}")
        valid_symbols = {row[0] for row in conn.execute(text("SELECT symbol FROM dim_company"))}
        valid_records = [record for record in records if record["symbol"] in valid_symbols]
        skipped_symbols = sorted({record["symbol"] for record in records} - valid_symbols)
        if skipped_symbols:
            print(f"Skipped symbols (not found in dim_company): {', '.join(skipped_symbols)}")
        if valid_records:
            conn.execute(upsert_sql, valid_records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM fact_cash_flow")).scalar_one()
        print(f"Rows in fact_cash_flow after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")
        print(f"Rows loaded/upserted: {len(valid_records)}")


def load_fact_ml_scores() -> None:
    df = pd.read_csv(CLEAN_DIR / "fact_ml_scores.csv")
    target_cols = [
        "symbol",
        "computed_at",
        "overall_score",
        "profitability_score",
        "growth_score",
        "leverage_score",
        "cashflow_score",
        "dividend_score",
        "trend_score",
        "health_label",
    ]
    if "computed_at" in df.columns:
        df["computed_at"] = pd.to_datetime(df["computed_at"], errors="coerce")
    # drop duplicate rows in the CSV to avoid inserting duplicates
    df = df.drop_duplicates(subset=["symbol", "computed_at"]).copy()
    df = df[target_cols].astype(object).where(pd.notna(df[target_cols]), None)
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO fact_ml_scores (
            symbol, computed_at, overall_score, profitability_score, growth_score,
            leverage_score, cashflow_score, dividend_score, trend_score, health_label
        )
        VALUES (
            :symbol, :computed_at, :overall_score, :profitability_score, :growth_score,
            :leverage_score, :cashflow_score, :dividend_score, :trend_score, :health_label
        )
        ON CONFLICT (symbol, computed_at) DO UPDATE SET
            overall_score = EXCLUDED.overall_score,
            profitability_score = EXCLUDED.profitability_score,
            growth_score = EXCLUDED.growth_score,
            leverage_score = EXCLUDED.leverage_score,
            cashflow_score = EXCLUDED.cashflow_score,
            dividend_score = EXCLUDED.dividend_score,
            trend_score = EXCLUDED.trend_score,
            health_label = EXCLUDED.health_label
        """
    )

    with engine.begin() as conn:
        # Remove existing duplicate rows in the target table so the unique index can be created.
        # This keeps the row with the smallest ctid for each (symbol, computed_at).
        conn.execute(
            text(
                """
                DELETE FROM fact_ml_scores a
                USING fact_ml_scores b
                WHERE a.symbol = b.symbol
                  AND a.computed_at = b.computed_at
                  AND a.ctid > b.ctid
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_ml_scores_symbol_computed_at
                ON fact_ml_scores (symbol, computed_at)
                """
            )
        )
        before_count = conn.execute(text("SELECT COUNT(*) FROM fact_ml_scores")).scalar_one()
        print(f"Rows in fact_ml_scores before load: {before_count}")
        if records:
            conn.execute(upsert_sql, records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM fact_ml_scores")).scalar_one()
        print(f"Rows in fact_ml_scores after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")


def load_fact_profit_loss() -> None:
    df = pd.read_csv(CLEAN_DIR / "fact_profit_loss.csv")
    target_cols = [
        "symbol",
        "year_id",
        "sales",
        "expenses",
        "operating_profit",
        "opm_pct",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_pct",
        "net_profit",
        "eps",
        "dividend_payout_pct",
        "net_profit_margin_pct",
        "expense_ratio_pct",
        "interest_coverage",
        "asset_turnover",
        "return_on_assets",
    ]
    df = df[target_cols].astype(object).where(pd.notna(df[target_cols]), None)
    records = df.to_dict(orient="records")

    upsert_sql = text(
        """
        INSERT INTO fact_profit_loss (
            symbol, year_id, sales, expenses, operating_profit, opm_pct, other_income, interest,
            depreciation, profit_before_tax, tax_pct, net_profit, eps, dividend_payout_pct,
            net_profit_margin_pct, expense_ratio_pct, interest_coverage, asset_turnover, return_on_assets
        )
        VALUES (
            :symbol, :year_id, :sales, :expenses, :operating_profit, :opm_pct, :other_income, :interest,
            :depreciation, :profit_before_tax, :tax_pct, :net_profit, :eps, :dividend_payout_pct,
            :net_profit_margin_pct, :expense_ratio_pct, :interest_coverage, :asset_turnover, :return_on_assets
        )
        ON CONFLICT (symbol, year_id) DO UPDATE SET
            sales = EXCLUDED.sales,
            expenses = EXCLUDED.expenses,
            operating_profit = EXCLUDED.operating_profit,
            opm_pct = EXCLUDED.opm_pct,
            other_income = EXCLUDED.other_income,
            interest = EXCLUDED.interest,
            depreciation = EXCLUDED.depreciation,
            profit_before_tax = EXCLUDED.profit_before_tax,
            tax_pct = EXCLUDED.tax_pct,
            net_profit = EXCLUDED.net_profit,
            eps = EXCLUDED.eps,
            dividend_payout_pct = EXCLUDED.dividend_payout_pct,
            net_profit_margin_pct = EXCLUDED.net_profit_margin_pct,
            expense_ratio_pct = EXCLUDED.expense_ratio_pct,
            interest_coverage = EXCLUDED.interest_coverage,
            asset_turnover = EXCLUDED.asset_turnover,
            return_on_assets = EXCLUDED.return_on_assets
        """
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_profit_loss_symbol_year
                ON fact_profit_loss (symbol, year_id)
                """
            )
        )
        before_count = conn.execute(text("SELECT COUNT(*) FROM fact_profit_loss")).scalar_one()
        print(f"Rows in fact_profit_loss before load: {before_count}")
        valid_symbols = {row[0] for row in conn.execute(text("SELECT symbol FROM dim_company"))}
        valid_records = [record for record in records if record["symbol"] in valid_symbols]
        skipped_symbols = sorted({record["symbol"] for record in records} - valid_symbols)
        if skipped_symbols:
            print(f"Skipped symbols (not found in dim_company): {', '.join(skipped_symbols)}")
        if valid_records:
            conn.execute(upsert_sql, valid_records)
        after_count = conn.execute(text("SELECT COUNT(*) FROM fact_profit_loss")).scalar_one()
        print(f"Rows in fact_profit_loss after load:  {after_count}")
        print(f"CSV rows processed: {len(records)}")
        print(f"Rows loaded/upserted: {len(valid_records)}")


def load_fact_pros_cons() -> None:
    df = pd.read_csv(CLEAN_DIR / "fact_pros_cons.csv")
    target_cols = ["symbol", "is_pro", "category", "text", "source", "confidence", "generated_at"]
    if "generated_at" in df.columns:
        df["generated_at"] = pd.to_datetime(df["generated_at"], errors="coerce")
    df = df[target_cols].astype(object).where(pd.notna(df[target_cols]), None)

    upsert_sql = text(
        """
        INSERT INTO fact_pros_cons (
            symbol, is_pro, category, text, source, confidence, generated_at
        )
        VALUES (
            :symbol, :is_pro, :category, :text, :source, :confidence, :generated_at
        )
        ON CONFLICT (symbol, is_pro, category, text, generated_at) DO UPDATE SET
            source = EXCLUDED.source,
            confidence = EXCLUDED.confidence
        """
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_pros_cons_unique_row
                ON fact_pros_cons (symbol, is_pro, category, text, generated_at)
                """
            )
        )
        before_count = conn.execute(text("SELECT COUNT(*) FROM fact_pros_cons")).scalar_one()
        print(f"Rows in fact_pros_cons before load: {before_count}")

        valid_symbols = {row[0] for row in conn.execute(text("SELECT symbol FROM dim_company"))}
        valid_df = df[df["symbol"].isin(valid_symbols)].copy()
        skipped_symbols = sorted(set(df["symbol"]) - valid_symbols)
        records = valid_df.to_dict(orient="records")

        if skipped_symbols:
            print(f"Skipped symbols (not found in dim_company): {', '.join(skipped_symbols)}")
        if records:
            conn.execute(upsert_sql, records)

        after_count = conn.execute(text("SELECT COUNT(*) FROM fact_pros_cons")).scalar_one()
        print(f"Rows in fact_pros_cons after load:  {after_count}")
        print(f"CSV rows processed: {len(df)}")
        print(f"Rows loaded/upserted: {len(records)}")


def main() -> None:
    load_dim_company()
    load_dim_health_label()
    load_dim_sector()
    load_dim_year()
    load_fact_analysis()
    load_fact_balance_sheet()
    load_fact_cash_flow()
    load_fact_ml_scores()
    load_fact_profit_loss()
    load_fact_pros_cons()


if __name__ == "__main__":
    main()

