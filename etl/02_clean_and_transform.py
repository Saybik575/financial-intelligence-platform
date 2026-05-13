from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
CLEAN_DIR = ROOT_DIR / "data" / "clean"

COMPANIES_FILE = RAW_DIR / "companies.xlsx"
BALANCE_FILE = RAW_DIR / "balancesheet.xlsx"
CASHFLOW_FILE = RAW_DIR / "cashflow.xlsx"
PROFIT_AND_LOSS_FILE = RAW_DIR / "profitandloss.xlsx"
ANALYSIS_FILE = RAW_DIR / "analysis.xlsx"
PROS_AND_CONS_FILE = RAW_DIR / "prosandcons.xlsx"


SECTOR_DESCRIPTION_MAP = {
	"IT": "Information Technology services and consulting companies",
	"Banking": "Commercial banks and financial institutions",
	"NBFC": "Non-banking financial companies",
	"Insurance": "Life and general insurance providers",
	"Energy": "Oil, gas, and renewable energy companies",
	"Power": "Electric power generation and distribution",
	"Healthcare": "Pharmaceutical and hospital companies",
	"Consumer Goods": "FMCG and retail businesses",
	"Auto": "Automobile manufacturers and suppliers",
	"Metals": "Steel and metal production companies",
	"Cement": "Cement manufacturing companies",
	"Paint": "Paint and chemical coating companies",
	"Industrial": "Engineering and capital goods companies",
	"Transport": "Logistics, aviation, and railway services",
	"Real Estate": "Property development companies",
	"Telecom": "Telecommunication service providers",
	"Finance": "Financial services and investment firms",
	"Holding Company": "Investment holding entities",
}


EXTRA_COMPANY_ROWS = [
	{
		"symbol": "ULTRACEMCO",
		"company_name": "UltraTech Cement Ltd",
		"sector_name": "Cement",
		"sub_sector": "Cement",
		"company_logo": pd.NA,
		"website": "https://www.ultratechcement.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=ULTRACEMCO",
		"bse_url": "https://www.bseindia.com/stock-share-price/ultratech-cement-ltd/ULTRACEMCO/532538/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "UltraTech Cement Ltd is India's largest manufacturer of grey cement, ready-mix concrete, and white cement.",
	},
	{
		"symbol": "UNIONBANK",
		"company_name": "Union Bank of India",
		"sector_name": "Banking",
		"sub_sector": "Public Bank",
		"company_logo": pd.NA,
		"website": "https://www.unionbankofindia.co.in/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=UNIONBANK",
		"bse_url": "https://www.bseindia.com/stock-share-price/union-bank-of-india/UNIONBANK/532477/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "Union Bank of India is a public sector bank offering retail and corporate banking services.",
	},
	{
		"symbol": "UNITDSPR",
		"company_name": "United Spirits Ltd",
		"sector_name": "Consumer Goods",
		"sub_sector": "Beverages",
		"company_logo": pd.NA,
		"website": "https://www.diageoindia.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=UNITDSPR",
		"bse_url": "https://www.bseindia.com/stock-share-price/united-spirits-ltd/UNITDSPR/532432/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "United Spirits Ltd is a leading alcoholic beverages company in India.",
	},
	{
		"symbol": "VBL",
		"company_name": "Varun Beverages Ltd",
		"sector_name": "Consumer Goods",
		"sub_sector": "Beverages",
		"company_logo": pd.NA,
		"website": "https://www.varunbeverages.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=VBL",
		"bse_url": "https://www.bseindia.com/stock-share-price/varun-beverages-ltd/VBL/540180/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "Varun Beverages Ltd is a bottling and distribution company for PepsiCo beverages.",
	},
	{
		"symbol": "VEDL",
		"company_name": "Vedanta Ltd",
		"sector_name": "Metals",
		"sub_sector": "Diversified Metals & Mining",
		"company_logo": pd.NA,
		"website": "https://www.vedantalimited.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=VEDL",
		"bse_url": "https://www.bseindia.com/stock-share-price/vedanta-ltd/VEDL/500295/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "Vedanta Ltd is a diversified natural resources company with interests in metals and mining.",
	},
	{
		"symbol": "WIPRO",
		"company_name": "Wipro Ltd",
		"sector_name": "IT",
		"sub_sector": "IT Services",
		"company_logo": pd.NA,
		"website": "https://www.wipro.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=WIPRO",
		"bse_url": "https://www.bseindia.com/stock-share-price/wipro-ltd/WIPRO/507685/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "Wipro Ltd is an IT services and consulting company.",
	},
	{
		"symbol": "ZOMATO",
		"company_name": "Zomato Ltd",
		"sector_name": "Consumer Services",
		"sub_sector": "Internet Services",
		"company_logo": pd.NA,
		"website": "https://www.zomato.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=ZOMATO",
		"bse_url": "https://www.bseindia.com/stock-share-price/zomato-ltd/ZOMATO/543320/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "Zomato Ltd is an internet platform for food delivery and restaurant discovery.",
	},
	{
		"symbol": "ZYDUSLIFE",
		"company_name": "Zydus Lifesciences Ltd",
		"sector_name": "Healthcare",
		"sub_sector": "Pharma",
		"company_logo": pd.NA,
		"website": "https://www.zyduslife.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=ZYDUSLIFE",
		"bse_url": "https://www.bseindia.com/stock-share-price/zydus-lifesciences-ltd/ZYDUSLIFE/532340/",
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "Zydus Lifesciences Ltd is a pharmaceutical company focused on healthcare and research.",
	},
	{
		"symbol": "AGTL",
		"company_name": "Adani Total Gas Ltd",
		"sector_name": "Energy",
		"sub_sector": "Gas Distribution",
		"company_logo": pd.NA,
		"website": "https://www.adanigas.com/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=AGTL",
		"bse_url": pd.NA,
		"face_value": pd.NA,
		"book_value": pd.NA,
		"about_company": "Adani Total Gas Ltd is engaged in City Gas Distribution (CGD) business.",
	},
	{
		"symbol": "INDIGO",
		"company_name": "Interglobe Aviation Ltd",
		"sector_name": "Transport",
		"sub_sector": "Aviation",
		"company_logo": "https://rb.gy/rv6gr8",
		"website": "http://www.goindigo.in/",
		"nse_url": "https://www.nseindia.com/get-quotes/equity?symbol=INDIGO",
		"bse_url": "https://www.bseindia.com/stock-share-price/interglobe-aviation-ltd/INDIGO/539448/",
		"face_value": 10.0,
		"book_value": 97.0,
		"about_company": "Interglobe Aviation Ltd (Indigo) is India's largest passenger airline operating as a low-cost carrier. Serving 86 destinations including 24 international destinations, it provides passengers with a simple, unbundled product, fulfilling its singular brand promise of providing low fares, on-time flights, and a courteous and hassle-free service to its customers. IndiGo commenced operations in August 2006 with a single aircraft and has grown its fleet to 262 aircrafts.",
	},
]


def ensure_output_dir() -> None:
	CLEAN_DIR.mkdir(parents=True, exist_ok=True)


def read_excel(path: Path, header: int = 1) -> pd.DataFrame:
	df = pd.read_excel(path, header=header)
	df.columns = df.columns.str.strip()
	return df


def normalize_text(value: object) -> object:
	if pd.isna(value):
		return pd.NA
	text = str(value).replace("\r", " ").replace("\n", " ").replace("/n", " ")
	text = re.sub(r"\s+", " ", text).strip()
	return pd.NA if text in {"", "NULL", "Null"} else text


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
	numerator = pd.to_numeric(numerator, errors="coerce")
	denominator = pd.to_numeric(denominator, errors="coerce")
	result = np.where(denominator.notna() & (denominator != 0), numerator / denominator, np.nan)
	return pd.Series(result, index=numerator.index)


def normalize_period_label(value: object) -> str | None:
	text = str(value).strip()
	if not text or text.lower() in {"nan", "none"}:
		return None
	if "TTM" in text.upper():
		return "TTM"

	parsed = pd.to_datetime(text, errors="coerce")
	if pd.notna(parsed):
		return f"{parsed.strftime('%b')} {int(parsed.year)}"

	match = re.search(r"([A-Za-z]{3,9})\s*[-/]?\s*(\d{2,4})", text)
	if match:
		month = match.group(1)[:3].title()
		year = int(match.group(2))
		if year < 100:
			year += 2000
		return f"{month} {year}"

	return text.upper()


def build_dim_company() -> pd.DataFrame:
	company_df = read_excel(COMPANIES_FILE)
	mapping_df = pd.read_csv(CLEAN_DIR / "sector_mapping.csv")

	company_df = company_df.rename(
		columns={"id": "symbol", "bse_profile": "bse_url", "nse_profile": "nse_url"}
	)
	if "chart_link" in company_df.columns:
		company_df = company_df.drop(columns=["chart_link"])

	company_df["symbol"] = company_df["symbol"].astype(str).str.strip().str.upper()
	mapping_df.columns = mapping_df.columns.str.strip().str.lower()
	mapping_df["symbol"] = mapping_df["symbol"].astype(str).str.strip().str.upper()

	company_df = company_df.merge(mapping_df, on="symbol", how="left")

	text_cols = company_df.select_dtypes(include=["object", "string"]).columns
	company_df[text_cols] = company_df[text_cols].apply(lambda col: col.map(normalize_text))

	company_df = company_df.rename(columns={"sector": "sector_name"})
	sector_df = (
		company_df[["sector_name"]]
		.dropna()
		.drop_duplicates()
		.assign(
			sector_code=lambda frame: frame["sector_name"].str.upper().str.replace(" ", "_", regex=False),
			description=lambda frame: frame["sector_name"].map(SECTOR_DESCRIPTION_MAP),
		)
		.sort_values("sector_name")
		.reset_index(drop=True)
	)
	sector_df["sector_id"] = range(1, len(sector_df) + 1)
	sector_df = sector_df[["sector_id", "sector_name", "sector_code", "description"]]
	sector_df.to_csv(CLEAN_DIR / "dim_sector.csv", index=False)

	company_df = company_df.merge(
		sector_df[["sector_id", "sector_name"]],
		on="sector_name",
		how="left",
	)

	extra_company_df = pd.DataFrame(EXTRA_COMPANY_ROWS)
	if not extra_company_df.empty:
		extra_company_df["symbol"] = extra_company_df["symbol"].astype(str).str.strip().str.upper()
		extra_company_df["sector_name"] = extra_company_df["sector_name"].astype(str).str.strip()
		text_cols = ["company_name", "sector_name", "sub_sector", "company_logo", "website", "nse_url", "bse_url", "about_company"]
		extra_company_df[text_cols] = extra_company_df[text_cols].apply(lambda col: col.map(normalize_text))
		extra_company_df["face_value"] = pd.to_numeric(extra_company_df["face_value"], errors="coerce")
		extra_company_df["book_value"] = pd.to_numeric(extra_company_df["book_value"], errors="coerce")
		extra_company_df = extra_company_df.merge(
			sector_df[["sector_id", "sector_name"]],
			on="sector_name",
			how="left",
		)
	company_df = company_df.drop(columns=["sector_name"])
	extra_company_df = extra_company_df.drop(columns=["sector_name"])
	company_df = pd.concat([company_df, extra_company_df], ignore_index=True)
	company_df = company_df.drop_duplicates(subset=["symbol"], keep="last")
	company_df = company_df[
		[
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
	]
	company_df.replace(["NULL", "Null", ""], pd.NA, inplace=True)
	company_df.to_csv(CLEAN_DIR / "dim_company.csv", index=False)
	return company_df


def build_dim_year() -> pd.DataFrame:
	labels: set[str] = set()
	candidate_period_cols = ["date", "year", "period", "fiscal_year", "reporting_period"]

	for file_path in [BALANCE_FILE, CASHFLOW_FILE, PROFIT_AND_LOSS_FILE]:
		df = read_excel(file_path)

		labels.update(str(column).strip() for column in df.columns[1:] if str(column).strip())

		normalized_cols = {str(column).strip().lower(): column for column in df.columns}
		period_col = next((normalized_cols[name] for name in candidate_period_cols if name in normalized_cols), None)
		if period_col is not None:
			values = df[period_col].dropna().astype(str).str.strip()
			labels.update(value for value in values if value)

	if not labels:
		raise ValueError("No valid period labels found in source files.")

	dim_year = pd.DataFrame({"raw_label": sorted(labels)})
	dim_year["clean_label"] = dim_year["raw_label"].str.strip()
	dim_year["is_ttm"] = dim_year["clean_label"].str.contains(r"\bTTM\b", case=False, na=False)

	month_abbr_to_num = {
		"JAN": 1,
		"FEB": 2,
		"MAR": 3,
		"APR": 4,
		"MAY": 5,
		"JUN": 6,
		"JUL": 7,
		"AUG": 8,
		"SEP": 9,
		"OCT": 10,
		"NOV": 11,
		"DEC": 12,
	}

	def parse_month_year(label: str):
		text = str(label).strip()
		if not text or "TTM" in text.upper():
			return pd.NA, pd.NA, pd.NA

		parsed = pd.to_datetime(text, errors="coerce")
		if pd.notna(parsed):
			return int(parsed.month), int(parsed.year), parsed.strftime("%b")

		match = re.search(r"([A-Za-z]{3,9})\s*[-/]?\s*(\d{4})", text)
		if match:
			month_key = match.group(1)[:3].upper()
			year_val = int(match.group(2))
			month_num = month_abbr_to_num.get(month_key, pd.NA)
			if pd.notna(month_num):
				return int(month_num), year_val, month_key.title()

		return pd.NA, pd.NA, pd.NA

	parsed_df = dim_year["clean_label"].apply(
		lambda value: pd.Series(parse_month_year(value), index=["month", "year", "month_str"])
	)
	dim_year = pd.concat([dim_year, parsed_df], axis=1)

	valid_period = dim_year["month"].notna() & dim_year["year"].notna()
	dim_year = dim_year[dim_year["is_ttm"] | valid_period].copy()

	year_int = dim_year["year"].astype("Int64")
	valid_year_range = year_int.between(1990, 2100, inclusive="both")
	dim_year = dim_year[dim_year["is_ttm"] | valid_year_range].copy()

	if dim_year.empty:
		raise ValueError("Period parsing produced no valid rows. Check source period labels and parser rules.")

	dim_year["year_label"] = np.where(
		dim_year["is_ttm"],
		"TTM",
		dim_year["month_str"] + " " + dim_year["year"].astype("Int64").astype(str),
	)

	dim_year["fiscal_year"] = dim_year["year"].astype("Int64")
	fiscal_rollover = (~dim_year["is_ttm"]) & (dim_year["month"].astype("Int64") >= 4)
	dim_year.loc[fiscal_rollover, "fiscal_year"] = dim_year.loc[fiscal_rollover, "fiscal_year"] + 1
	dim_year.loc[dim_year["is_ttm"], "fiscal_year"] = pd.NA

	def get_quarter(month):
		if pd.isna(month):
			return None
		if month == 3:
			return "Q4"
		if month == 6:
			return "Q1"
		if month == 9:
			return "Q2"
		if month == 12:
			return "Q3"
		return None

	dim_year["quarter"] = dim_year["month"].apply(get_quarter)
	dim_year.loc[dim_year["is_ttm"], "quarter"] = "TTM"

	dim_year["is_half_year"] = dim_year["month"].astype("Int64").eq(9).fillna(False).astype(bool)

	base_period_id = dim_year["year"].astype("Int64") * 100 + dim_year["month"].astype("Int64")
	dim_year["year_id"] = base_period_id.astype("Int64")
	dim_year.loc[dim_year["is_ttm"], "year_id"] = 999999
	dim_year["sort_order"] = base_period_id.astype("Int64")
	dim_year.loc[dim_year["is_ttm"], "sort_order"] = 999999

	# Guardrail: keep only valid surrogate keys expected by warehouse schema.
	dim_year = dim_year[dim_year["year_id"].notna()].copy()
	dim_year = dim_year[dim_year["year_id"] <= 999999].copy()
	dim_year["year_id"] = dim_year["year_id"].astype("Int64")
	dim_year["sort_order"] = dim_year["sort_order"].astype("Int64")

	dim_year_final = (
		dim_year[
			["year_id", "year_label", "fiscal_year", "quarter", "is_ttm", "is_half_year", "sort_order"]
		]
		.sort_values(["sort_order", "year_label"], na_position="last")
		.drop_duplicates(subset=["year_id"], keep="first")
	)
	dim_year_final.to_csv(CLEAN_DIR / "dim_year.csv", index=False)
	return dim_year_final


def build_dim_health_label() -> pd.DataFrame:
	health_labels = pd.DataFrame(
		[
			("POOR", 0, 20, "#E74C3C"),
			("WEAK", 21, 40, "#E67E22"),
			("AVERAGE", 41, 60, "#F1C40F"),
			("GOOD", 61, 80, "#27AE60"),
			("EXCELLENT", 81, 100, "#2ECC71"),
		],
		columns=["label_name", "min_score", "max_score", "color_hex"],
	)
	health_labels = health_labels.sort_values("min_score").reset_index(drop=True)
	health_labels["label_id"] = range(1, len(health_labels) + 1)
	health_labels = health_labels[["label_id", "label_name", "min_score", "max_score", "color_hex"]]
	health_labels.to_csv(CLEAN_DIR / "dim_health_label.csv", index=False)
	return health_labels


def build_fact_tables(dim_year: pd.DataFrame) -> dict[str, pd.DataFrame]:
	dim_year_lookup = (
		dim_year.assign(label_norm=dim_year["year_label"].map(normalize_period_label))
		.dropna(subset=["label_norm"])
		.drop_duplicates(subset=["label_norm"])
		.set_index("label_norm")["year_id"]
		.to_dict()
	)

	def map_year_id(value: object):
		return dim_year_lookup.get(normalize_period_label(value), pd.NA)

	balance = read_excel(BALANCE_FILE)
	balance["symbol"] = balance["company_id"].astype(str).str.strip().str.upper()
	balance["year_id"] = balance["year"].map(map_year_id).astype("Int64")
	balance = balance.dropna(subset=["year_id"]).copy()
	balance["debt_to_equity"] = safe_divide(balance["borrowings"], balance["equity_capital"] + balance["reserves"])
	balance["equity_ratio"] = safe_divide(balance["equity_capital"] + balance["reserves"], balance["total_assets"])
	balance["shares_outstanding"] = pd.NA
	balance["book_value_per_share"] = pd.NA
	fact_balance_sheet = balance[
		[
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
	].copy()
	fact_balance_sheet.to_csv(CLEAN_DIR / "fact_balance_sheet.csv", index=False)

	profit = read_excel(PROFIT_AND_LOSS_FILE)
	profit = profit.rename(
		columns={
			"company_id": "symbol",
			"opm_percentage": "opm_pct",
			"tax_percentage": "tax_pct",
			"dividend_payout": "dividend_payout_pct",
		}
	)
	profit["symbol"] = profit["symbol"].astype(str).str.strip().str.upper()
	profit["year_id"] = profit["year"].map(map_year_id).astype("Int64")
	profit = profit.dropna(subset=["year_id"]).copy()
	profit = profit.merge(
		fact_balance_sheet[["symbol", "year_id", "total_assets"]],
		on=["symbol", "year_id"],
		how="left",
		suffixes=("", "_bs"),
	)
	profit["opm_pct"] = safe_divide(profit["operating_profit"], profit["sales"]) * 100
	profit["net_profit_margin_pct"] = safe_divide(profit["net_profit"], profit["sales"]) * 100
	profit["expense_ratio_pct"] = safe_divide(profit["expenses"], profit["sales"]) * 100
	profit["interest_coverage"] = safe_divide(profit["operating_profit"], profit["interest"])
	profit["asset_turnover"] = safe_divide(profit["sales"], profit["total_assets"])
	profit["return_on_assets"] = safe_divide(profit["net_profit"], profit["total_assets"]) * 100
	fact_profit_loss = profit[
		[
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
	].copy()
	fact_profit_loss.to_csv(CLEAN_DIR / "fact_profit_loss.csv", index=False)

	cash = read_excel(CASHFLOW_FILE)
	cash["symbol"] = cash["company_id"].astype(str).str.strip().str.upper()
	cash["year_id"] = cash["year"].map(map_year_id).astype("Int64")
	cash = cash.dropna(subset=["year_id"]).copy()
	cash["free_cash_flow"] = pd.to_numeric(cash["operating_activity"], errors="coerce") + pd.to_numeric(
		cash["investing_activity"], errors="coerce"
	)
	cash = cash.merge(
		fact_profit_loss[["symbol", "year_id", "net_profit"]],
		on=["symbol", "year_id"],
		how="left",
	)
	cash["cash_conversion_ratio"] = safe_divide(cash["operating_activity"], cash["net_profit"])
	fact_cash_flow = cash[
		[
			"symbol",
			"year_id",
			"operating_activity",
			"investing_activity",
			"financing_activity",
			"net_cash_flow",
			"free_cash_flow",
			"cash_conversion_ratio",
		]
	].copy()
	fact_cash_flow.to_csv(CLEAN_DIR / "fact_cash_flow.csv", index=False)

	analysis = read_excel(ANALYSIS_FILE)
	analysis["symbol"] = analysis["company_id"].astype(str).str.strip().str.upper()
	analysis_metric_map = {
		"compounded_sales_growth": "compounded_sales_growth_pct",
		"compounded_profit_growth": "compounded_profit_growth_pct",
		"stock_price_cagr": "stock_price_cagr_pct",
		"roe": "roe_pct",
	}

	def parse_analysis_cell(text: object):
		text = str(text).strip()
		match = re.search(r"(?i)(TTM|10\s*Years?|5\s*Years?|3\s*Years?)\s*:?\s*([-+]?\d+(?:\.\d+)?)\s*%", text)
		if not match:
			return None, np.nan
		period_raw = match.group(1).upper().replace(" ", "")
		period_label = {"10YEARS": "10Y", "5YEARS": "5Y", "3YEARS": "3Y", "TTM": "TTM"}.get(period_raw)
		return period_label, float(match.group(2))

	analysis_records: list[dict[str, object]] = []
	for _, row in analysis.iterrows():
		per_period: dict[str, dict[str, object]] = {}
		for source_col, target_col in analysis_metric_map.items():
			period_label, metric_value = parse_analysis_cell(row[source_col])
			if period_label in {"10Y", "5Y", "3Y", "TTM"}:
				per_period.setdefault(period_label, {})[target_col] = metric_value
		for period_label, metrics in per_period.items():
			analysis_records.append({"symbol": row["symbol"], "period_label": period_label, **metrics})

	fact_analysis = pd.DataFrame(analysis_records)
	if not fact_analysis.empty:
		fact_analysis = fact_analysis.sort_values(["symbol", "period_label"]).drop_duplicates(
			subset=["symbol", "period_label"], keep="first"
		)
	fact_analysis.to_csv(CLEAN_DIR / "fact_analysis.csv", index=False)

	pros_cons = read_excel(PROS_AND_CONS_FILE)
	pros_cons["symbol"] = pros_cons["company_id"].astype(str).str.strip().str.upper()
	pros_cons["generated_at"] = pd.Timestamp.now(tz="UTC").floor("s")

	pros_rows = pros_cons[["symbol", "pros", "generated_at"]].dropna(subset=["pros"]).copy()
	pros_rows = pros_rows.rename(columns={"pros": "text"})
	pros_rows["is_pro"] = True
	pros_rows["category"] = "pros"
	pros_rows["source"] = "MANUAL"
	pros_rows["confidence"] = 1.0

	cons_rows = pros_cons[["symbol", "cons", "generated_at"]].dropna(subset=["cons"]).copy()
	cons_rows = cons_rows.rename(columns={"cons": "text"})
	cons_rows["is_pro"] = False
	cons_rows["category"] = "cons"
	cons_rows["source"] = "MANUAL"
	cons_rows["confidence"] = 1.0

	fact_pros_cons = pd.concat([pros_rows, cons_rows], ignore_index=True)[
		["symbol", "is_pro", "category", "text", "source", "confidence", "generated_at"]
	]
	fact_pros_cons.to_csv(CLEAN_DIR / "fact_pros_cons.csv", index=False)

	fact_ml_scores = pd.DataFrame(
		columns=[
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
	)
	fact_ml_scores.to_csv(CLEAN_DIR / "fact_ml_scores.csv", index=False)

	return {
		"fact_balance_sheet": fact_balance_sheet,
		"fact_profit_loss": fact_profit_loss,
		"fact_cash_flow": fact_cash_flow,
		"fact_analysis": fact_analysis,
		"fact_pros_cons": fact_pros_cons,
		"fact_ml_scores": fact_ml_scores,
	}


def main() -> None:
	ensure_output_dir()
	build_dim_company()
	dim_year = build_dim_year()
	build_dim_health_label()
	fact_tables = build_fact_tables(dim_year)

	for name, frame in fact_tables.items():
		print(f"{name}: {frame.shape}")


if __name__ == "__main__":
	main()
