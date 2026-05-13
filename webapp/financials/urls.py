from django.urls import path

from .views import (
    CompanyFinancialsView,
    CompanyChartDataView,
    ScreenerAPIView,
)


urlpatterns = [

    path(
        "v1/screener/",
        ScreenerAPIView.as_view(),
        name="screener-api"
    ),

    path(
        "charts/<str:symbol>/",
        CompanyChartDataView.as_view(),
        name="company-chart-data"
    ),

    path(
        "<str:symbol>/",
        CompanyFinancialsView.as_view(),
        name="company-financials"
    ),
]