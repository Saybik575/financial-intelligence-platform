from rest_framework.generics import ListAPIView
from .models import Company
from .serializers import CompanySerializer
from rest_framework.generics import RetrieveAPIView
from django.shortcuts import render
from django.db import connection
from django.db.models import Q
from financials.models import (
    ProfitLoss,
    Analysis,
)
from django.core.paginator import Paginator
from .models import Sector
from ml.models import MLScore

class CompanyListView(ListAPIView):

    queryset = Company.objects.select_related(
        "sector"
    ).all()

    serializer_class = CompanySerializer

    search_fields = [
        "company_name",
        "symbol",
    ]

    ordering_fields = [
        "company_name",
        "symbol",
    ]

    filterset_fields = [
        "sector",
    ]

class CompanyDetailView(RetrieveAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    lookup_field = "symbol"

def home_page(request):

    context = {
        "company_count": Company.objects.count()
    }

    return render(
        request,
        "home.html",
        context
    )

def company_page(request):
    search_query = request.GET.get("q", "")
    sector_filter = request.GET.get("sector", "")
    sort_by = request.GET.get("sort", "")
    min_score = request.GET.get("min_score", "")
    min_sales = request.GET.get("min_sales", "")
    min_eps = request.GET.get("min_eps", "")

    # Base queryset
    companies = Company.objects.select_related("sector").all()

    # Exclude accidental CSV header rows if present
    if companies.filter(symbol__iexact='symbol').exists() or companies.filter(company_name__iexact='company_name').exists():
        companies = companies.exclude(symbol__iexact='symbol').exclude(company_name__iexact='company_name')

    # Apply search filter if provided
    if search_query:
        companies = companies.filter(
            Q(company_name__icontains=search_query) |
            Q(symbol__icontains=search_query)
        )

    # Apply sector filter if provided
    if sector_filter:
        try:
            companies = companies.filter(sector=sector_filter)
        except (ValueError, TypeError):
            pass

    # Apply sorting if provided; default to symbol ascending
    if sort_by:
        companies = companies.order_by(sort_by)
    else:
        companies = companies.order_by('symbol')

    # Get all sectors for the dropdown
    sectors = Sector.objects.all().order_by('sector_id')

    # Convert companies to list for filtering
    companies_list = list(companies)

    # Fetch latest scores
    latest_scores = {}
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT ON (s.symbol) s.symbol, s.overall_score, s.health_label, h.color_hex
            FROM fact_ml_scores s
            LEFT JOIN dim_health_label h
                ON UPPER(h.label_name) = UPPER(s.health_label)
            ORDER BY s.symbol, s.computed_at DESC NULLS LAST
            """
        )
        for symbol, overall_score, health_label, color_hex in cursor.fetchall():
            latest_scores[symbol] = {
                "symbol": symbol,
                "overall_score": overall_score,
                "health_label": health_label,
                "color_hex": color_hex or "#0d6efd",
            }

    latest_financials = {}

    financials = ProfitLoss.objects.order_by(
        "symbol",
        "-year_id"
    )

    for item in financials:

        if item.symbol not in latest_financials:
            latest_financials[item.symbol] = item

    # Apply financial filters
    filtered_companies = []

    for company in companies_list:

        score = latest_scores.get(company.symbol)

        financial = latest_financials.get(company.symbol)

        include_company = True

        # Minimum Health Score
        if min_score:

            if (
                not score or
                score["overall_score"] is None or
                score["overall_score"] < float(min_score)
            ):
                include_company = False

        # Minimum Sales
        if min_sales:

            if (
                not financial or
                financial.sales is None or
                financial.sales < float(min_sales)
            ):
                include_company = False

        # Minimum EPS
        if min_eps:

            if (
                not financial or
                financial.eps is None or
                financial.eps < float(min_eps)
            ):
                include_company = False

        if include_company:
            filtered_companies.append(company)

    companies_list = filtered_companies

    # Paginate (10 per page)
    paginator = Paginator(companies_list, 10)
    page_number = request.GET.get("page")
    companies_page = paginator.get_page(page_number)

    chart_data = {}

    for company in companies:

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
                    pl.sales
                FROM fact_profit_loss pl
                LEFT JOIN dim_year dy ON pl.year_id = dy.year_id
                WHERE pl.symbol = %s AND pl.year_id != 999999
                ORDER BY dy.sort_order ASC NULLS LAST
                """,
                [company.symbol]
            )
            rows = cursor.fetchall()
            
        chart_data[company.symbol] = {
            "years": [row[0] or str(row[1]) for row in rows],
            "sales": [float(row[1] or 0) for row in rows]
        }

    context = {
        "companies": companies_page,
        "search_query": search_query,
        "sector_filter": sector_filter,
        "sort_by": sort_by,
        "sectors": sectors,
        "latest_scores": latest_scores,
        "latest_financials": latest_financials,
        "min_score": min_score,
        "min_sales": min_sales,
        "min_eps": min_eps,
        "chart_data": chart_data,
    }

    return render(request, "companies/company_list.html", context)

def company_detail_page(request, symbol):

    company = Company.objects.get(symbol=symbol)

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
                pl.eps,
                pl.opm_pct
            FROM fact_profit_loss pl
            LEFT JOIN dim_year dy ON pl.year_id = dy.year_id
            WHERE pl.symbol = %s
            ORDER BY dy.sort_order DESC NULLS LAST, pl.year_id DESC
            LIMIT 10
            """,
            [symbol],
        )
        financial_rows = cursor.fetchall()

    financials = [
        {
            "year_label": row[0],
            "sales": row[1],
            "net_profit": row[2],
            "eps": row[3],
            "opm_pct": row[4],
        }
        for row in financial_rows
    ]

    latest_score = None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.overall_score, s.health_label, h.color_hex
            FROM fact_ml_scores s
            LEFT JOIN dim_health_label h
                ON UPPER(h.label_name) = UPPER(s.health_label)
            WHERE s.symbol = %s
            ORDER BY s.computed_at DESC NULLS LAST
            LIMIT 1
            """,
            [symbol],
        )
        row = cursor.fetchone()
        if row:
            latest_score = {
                "overall_score": row[0],
                "health_label": row[1],
                "color_hex": row[2] or "#0d6efd",
            }

    context = {
        "company": company,
        "financials": financials,
        "latest_score": latest_score
    }

    return render(
        request,
        "companies/company_detail.html",
        context
    )

def compare_companies(request):

    symbols = request.GET.getlist("symbols")

    companies = (
        Company.objects.filter(symbol__in=symbols)
        .order_by("symbol")
        .distinct("symbol")
    )

    latest_financials = {}

    for company in companies:

        latest_financials[company.symbol] = (
            ProfitLoss.objects.filter(
                symbol=company.symbol
            )
            .order_by("-year_id")
            .first()
        )

    latest_scores = {}

    for company in companies:

        latest_scores[company.symbol] = (
            MLScore.objects.filter(
                symbol=company.symbol
            )
            .order_by("-computed_at")
            .first()
        )

    chart_data = {}

    for company in companies:

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
                    pl.sales
                FROM fact_profit_loss pl
                LEFT JOIN dim_year dy ON pl.year_id = dy.year_id
                WHERE pl.symbol = %s AND pl.year_id != 999999
                ORDER BY dy.sort_order ASC NULLS LAST
                """,
                [company.symbol]
            )
            rows = cursor.fetchall()
            
        chart_data[company.symbol] = {
            "years": [row[0] or str(row[1]) for row in rows],
            "sales": [float(row[1] or 0) for row in rows]
        }

    context = {
        "companies": companies,
        "all_companies": Company.objects.order_by("symbol").distinct("symbol"),
        "latest_financials": latest_financials,
        "latest_scores": latest_scores,
        "selected_symbols": symbols,
        "chart_data": chart_data
    }

    return render(
        request,
        "companies/compare.html",
        context
    )

def screener_page(request):

    return render(
        request,
        "companies/screener.html"
    )

def sector_detail_page(request, name):

    sector = Sector.objects.filter(
        sector_name=name
    ).first()

    companies = Company.objects.filter(
        sector=sector
    )

    company_data = []

    for company in companies:

        score = MLScore.objects.filter(
            symbol=company.symbol
        ).order_by("-computed_at").first()

        analysis = Analysis.objects.filter(
            symbol=company.symbol,
            period_label="10Y"
        ).first()

        financial = ProfitLoss.objects.filter(
            symbol=company.symbol
        ).order_by("-year_id").first()

        company_data.append({

            "company": company,

            "score":
                score.overall_score
                if score else None,

            "health_label":
                score.health_label
                if score else None,

            "roe":
                analysis.roe_pct
                if analysis else None,

            "sales_growth":
                analysis.compounded_sales_growth_pct
                if analysis else None,

            "sales":
                financial.sales
                if financial else None,
        })

    company_data = sorted(
        company_data,
        key=lambda x: x["score"] or 0,
        reverse=True
    )

    sector_revenue = {}

    for company in companies:

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
                    pl.sales
                FROM fact_profit_loss pl
                LEFT JOIN dim_year dy ON pl.year_id = dy.year_id
                WHERE pl.symbol = %s AND pl.year_id != 999999
                ORDER BY dy.sort_order ASC NULLS LAST
                """,
                [company.symbol]
            )
            rows = cursor.fetchall()

        for year_label, sales in rows:

            sales = float(sales or 0)

            if year_label not in sector_revenue:

                sector_revenue[year_label] = 0

            sector_revenue[year_label] += sales

    years = sorted(
        sector_revenue.keys(),
        key=lambda x: (
            int(x.split()[-1])
            if len(x.split()) > 1 else 0
        )
    )

    revenue_values = [
        sector_revenue[y]
        for y in years
    ]

    roe_values = []

    growth_values = []

    for item in company_data:

        if item["roe"] is not None:

            roe_values.append(
                item["roe"]
            )

        if item["sales_growth"] is not None:

            growth_values.append(
                item["sales_growth"]
            )

    avg_roe = (
        sum(roe_values) / len(roe_values)
        if roe_values else 0
    )

    avg_growth = (
        sum(growth_values) /
        len(growth_values)
        if growth_values else 0
    )

    context = {

        "sector": sector,

        "company_data": company_data,

        "top_companies":
            company_data[:3],

        "bottom_companies":
            company_data[-3:],

        "years": years,

        "revenue_values": revenue_values,
        
        "avg_roe": round(avg_roe, 2),

        "avg_growth":
            round(avg_growth, 2),
    }

    return render(
        request,
        "companies/sector_detail.html",
        context
    )