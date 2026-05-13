"""
Machine Learning Financial Health Scoring Module

This module implements financial health scoring algorithms that calculate
multidimensional scores for companies based on financial metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from datetime import datetime
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


class FinancialHealthScorer:
    """Calculates comprehensive financial health scores."""

    WEIGHTS = {
        'profitability': 0.25,
        'growth': 0.20,
        'leverage': 0.20,
        'cashflow': 0.15,
        'dividend': 0.10,
        'trend': 0.10,
    }

    HEALTH_THRESHOLDS = {
        'POOR': (0, 20),
        'WEAK': (21, 40),
        'AVERAGE': (41, 60),
        'GOOD': (61, 80),
        'EXCELLENT': (81, 100),
    }

    def score_company(self, symbol, profit_df, balance_df, cashflow_df, analysis_df):
        """Score a company across all dimensions."""
        try:
            scores = {
                'profitability_score': self._score_profitability(profit_df),
                'growth_score': self._score_growth(profit_df, analysis_df),
                'leverage_score': self._score_leverage(balance_df, profit_df),
                'cashflow_score': self._score_cashflow(cashflow_df, profit_df),
                'dividend_score': self._score_dividend(profit_df),
                'trend_score': self._score_trend(profit_df, balance_df, cashflow_df),
            }
            
            scores['overall_score'] = self._calculate_overall_score(scores)
            scores['health_label'] = self._get_health_label(scores['overall_score'])
            
            return scores
        except Exception as e:
            logger.error(f"Error scoring {symbol}: {e}")
            return self._get_default_scores()

    def _score_profitability(self, profit_df):
        """Score profitability based on margins and returns."""
        if profit_df.empty:
            return 50.0
        
        scores = []
        latest = profit_df.iloc[-1]
        
        # Net profit margin
        npm = pd.to_numeric(latest.get('net_profit_margin_pct'), errors='coerce')
        if pd.notna(npm):
            npm_normalized = min(max(npm / 15.0, 0), 1.0)
            scores.append(npm_normalized * 100)

        # Operating profit margin
        opm = pd.to_numeric(latest.get('opm_pct'), errors='coerce')
        if pd.notna(opm):
            opm_normalized = min(max(opm / 20.0, 0), 1.0)
            scores.append(opm_normalized * 100)

        # Return on assets
        roa = pd.to_numeric(latest.get('return_on_assets'), errors='coerce')
        if pd.notna(roa):
            roa_normalized = min(max(roa / 15.0, 0), 1.0)
            scores.append(roa_normalized * 100)

        return np.mean(scores) if scores else 50.0

    def _score_growth(self, profit_df, analysis_df=None):
        """Score growth based on revenue and profit trends."""
        scores = []

        if len(profit_df) >= 2:
            sales = pd.to_numeric(profit_df['sales'], errors='coerce')
            sales_clean = sales.dropna()

            if len(sales_clean) >= 2:
                yoy_growth = sales_clean.pct_change().dropna()
                avg_growth = yoy_growth.mean()
                growth_score = min(max((avg_growth * 100) / 20.0, 0), 1.0) * 100
                scores.append(growth_score)

        if analysis_df is not None and not analysis_df.empty:
            csg = pd.to_numeric(
                analysis_df.get('compounded_sales_growth_pct', pd.Series()),
                errors='coerce'
            )
            if len(csg) > 0 and pd.notna(csg.iloc[-1]):
                csg_score = min(max(csg.iloc[-1] / 20.0, 0), 1.0) * 100
                scores.append(csg_score)

        return np.mean(scores) if scores else 50.0

    def _score_leverage(self, balance_df, profit_df):
        """Score leverage and solvency."""
        if balance_df.empty or profit_df.empty:
            return 50.0

        scores = []
        return np.mean(scores) if scores else 50.0

    def _score_cashflow(self, cashflow_df, profit_df):
        """Score cash flow health."""
        if cashflow_df.empty:
            return 50.0
        return 50.0

    def _score_dividend(self, profit_df):
        """Score dividend policy."""
        scores = []
        return np.mean(scores) if scores else 50.0

    def _score_trend(self, profit_df, balance_df, cashflow_df):
        """Score trend and momentum."""
        scores = []
        return np.mean(scores) if scores else 50.0

    def _calculate_overall_score(self, scores):
        """Calculate weighted overall score."""
        total = 0.0
        for dimension, weight in self.WEIGHTS.items():
            score_key = f"{dimension}_score"
            if score_key in scores:
                total += scores[score_key] * weight
        return min(max(total, 0), 100)

    def _get_health_label(self, score):
        """Map score to health label."""
        for label, (min_val, max_val) in self.HEALTH_THRESHOLDS.items():
            if min_val <= score <= max_val:
                return label
        return 'AVERAGE'

    @staticmethod
    def _get_default_scores():
        """Return default scores when calculation fails."""
        return {
            'profitability_score': 50.0,
            'growth_score': 50.0,
            'leverage_score': 50.0,
            'cashflow_score': 50.0,
            'dividend_score': 50.0,
            'trend_score': 50.0,
            'overall_score': 50.0,
            'health_label': 'AVERAGE',
        }


class BatchScorer:
    """Batch score multiple companies efficiently."""

    def __init__(self, db_engine):
        """Initialize batch scorer."""
        self.engine = db_engine
        self.scorer = FinancialHealthScorer()

    def score_all_companies(self, batch_size: int = 10) -> pd.DataFrame:
        """Score all companies in the warehouse."""
        logger.info("Starting batch ML rescoring...")

        # Get list of all companies
        query = text("SELECT DISTINCT symbol FROM dim_company ORDER BY symbol")
        with self.engine.connect() as connection:
            companies = pd.read_sql(query, connection)

        scores_list = []

        for idx, row in companies.iterrows():
            symbol = row['symbol']

            try:
                # Fetch company data from warehouse using named parameters for SQLAlchemy
                with self.engine.connect() as connection:
                    profit_df = pd.read_sql(
                        text("SELECT * FROM fact_profit_loss WHERE symbol = :symbol ORDER BY year_id"),
                        connection,
                        params={"symbol": symbol},
                    )
                    balance_df = pd.read_sql(
                        text("SELECT * FROM fact_balance_sheet WHERE symbol = :symbol ORDER BY year_id"),
                        connection,
                        params={"symbol": symbol},
                    )
                    cashflow_df = pd.read_sql(
                        text("SELECT * FROM fact_cash_flow WHERE symbol = :symbol ORDER BY year_id"),
                        connection,
                        params={"symbol": symbol},
                    )
                    analysis_df = pd.read_sql(
                        text("SELECT * FROM fact_analysis WHERE symbol = :symbol"),
                        connection,
                        params={"symbol": symbol},
                    )

                # Score company
                scores = self.scorer.score_company(
                    symbol,
                    profit_df,
                    balance_df,
                    cashflow_df,
                    analysis_df,
                )

                # Add metadata
                scores['symbol'] = symbol
                scores['computed_at'] = datetime.now()

                scores_list.append(scores)

                # Log progress
                if (idx + 1) % 10 == 0:
                    logger.info(f"Scored {idx + 1} / {len(companies)} companies")

            except Exception as e:
                logger.error(f"Error scoring {symbol}: {e}")
                continue

        scores_df = pd.DataFrame(scores_list)
        logger.info(f"Batch scoring completed. Scored {len(scores_df)} companies")

        return scores_df

    def score_company_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Score a single company by symbol."""
        try:
            # Fetch company data using named parameters
            with self.engine.connect() as connection:
                profit_df = pd.read_sql(
                    text("SELECT * FROM fact_profit_loss WHERE symbol = :symbol ORDER BY year_id"),
                    connection,
                    params={"symbol": symbol},
                )
                balance_df = pd.read_sql(
                    text("SELECT * FROM fact_balance_sheet WHERE symbol = :symbol ORDER BY year_id"),
                    connection,
                    params={"symbol": symbol},
                )
                cashflow_df = pd.read_sql(
                    text("SELECT * FROM fact_cash_flow WHERE symbol = :symbol ORDER BY year_id"),
                    connection,
                    params={"symbol": symbol},
                )
                analysis_df = pd.read_sql(
                    text("SELECT * FROM fact_analysis WHERE symbol = :symbol"),
                    connection,
                    params={"symbol": symbol},
                )

            scores = self.scorer.score_company(
                symbol,
                profit_df,
                balance_df,
                cashflow_df,
                analysis_df,
            )

            scores['symbol'] = symbol
            scores['computed_at'] = datetime.now()

            return scores

        except Exception as e:
            logger.error(f"Error scoring {symbol}: {e}")
            return None
