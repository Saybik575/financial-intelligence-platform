from rest_framework.generics import ListAPIView

from .models import ProfitLoss

from .models import Analysis

from ml.models import MLScore

from companies.models import Company

from .serializers import ProfitLossSerializer

from rest_framework.response import Response

from rest_framework.views import APIView

from django.db import connection

from django.db.models import Q

class CompanyFinancialsView(ListAPIView):

    serializer_class = ProfitLossSerializer

    def get_queryset(self):

        symbol = self.kwargs["symbol"]

        return ProfitLoss.objects.filter(
            symbol=symbol
        ).order_by("-year_id")
    
class CompanyChartDataView(APIView):

    def get(self, request, symbol):

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CASE
                        WHEN pl.year_id = 999999 THEN 'TTM'
                        WHEN MOD(pl.year_id, 100) = 12 THEN 'Mar ' || ((pl.year_id / 100) + 1)::TEXT
                        WHEN MOD(pl.year_id, 100) = 3 THEN 'Mar ' || (pl.year_id / 100)::TEXT
                        ELSE COALESCE(dy.year_label, CAST(pl.year_id AS TEXT))
                    END AS year_label,
                    pl.sales,
                    pl.net_profit,
                    pl.eps
                FROM fact_profit_loss pl
                LEFT JOIN dim_year dy ON pl.year_id = dy.year_id
                WHERE pl.symbol = %s AND pl.year_id != 999999
                ORDER BY dy.sort_order ASC NULLS LAST
                """,
                [symbol]
            )
            rows = cursor.fetchall()

        data = {
            "years": [row[0] or str(row[1]) for row in rows],
            "sales": [float(row[1] or 0) for row in rows],
            "net_profit": [float(row[2] or 0) for row in rows],
            "eps": [float(row[3] or 0) for row in rows],
        }

        return Response(data)


class ScreenerAPIView(APIView):

    def get(self, request):

        min_roe = request.GET.get("min_roe")

        min_sales_growth = request.GET.get("min_sales_growth")

        min_health_score = request.GET.get("min_health_score")

        results = []

        # If only health score filter, query MLScore directly
        if (
            not min_roe and
            not min_sales_growth and
            min_health_score
        ):

            scores = MLScore.objects.filter(
                overall_score__gte=float(
                    min_health_score
                )
            ).order_by(
                'symbol', '-computed_at'
            ).distinct('symbol')

            symbols_with_score = [
                s.symbol for s in scores
            ]

            records = Analysis.objects.filter(
                period_label="10Y",
                symbol__in=symbols_with_score
            )

            for record in records:

                score = MLScore.objects.filter(
                    symbol=record.symbol
                ).order_by(
                    'symbol', '-computed_at'
                ).first()

                company = Company.objects.filter(
                    symbol=record.symbol
                ).first()

                if company and score:

                    if (
                        score.overall_score <
                        float(min_health_score)
                    ):
                        continue

                    results.append({
                        "symbol": company.symbol,
                        "company_name": company.company_name,
                        "sector": str(company.sector),
                        "roe": record.roe_pct,
                        "sales_growth":
                            record.compounded_sales_growth_pct,
                        "health_score":
                            score.overall_score,
                    })

        else:

            # Standard query with Analysis records
            query = Q(period_label="10Y")

            if min_roe:

                query &= Q(
                    roe_pct__gte=float(min_roe)
                )

            if min_sales_growth:

                query &= Q(
                    compounded_sales_growth_pct__gte=float(
                        min_sales_growth
                    )
                )

            records = Analysis.objects.filter(
                query
            )

            for record in records:

                company = Company.objects.filter(
                    symbol=record.symbol
                ).first()

                score = MLScore.objects.filter(
                    symbol=record.symbol
                ).order_by(
                    "-computed_at"
                ).first()

                if company:

                    if min_health_score:

                        if (
                            not score or
                            score.overall_score <
                            float(min_health_score)
                        ):
                            continue

                    results.append({
                        "symbol": company.symbol,
                        "company_name": company.company_name,
                        "sector": str(company.sector),
                        "roe": record.roe_pct,
                        "sales_growth":
                            record.compounded_sales_growth_pct,
                        "health_score":
                            score.overall_score if score else None,
                    })

        return Response(results)