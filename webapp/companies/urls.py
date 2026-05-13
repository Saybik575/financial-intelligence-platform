from django.urls import path
from .views import (
    CompanyListView,
    CompanyDetailView,
    company_page,
    company_detail_page,
    compare_companies,
    screener_page,
)

urlpatterns = [
    path('', CompanyListView.as_view(), name='company-list-api'),

    path('page/', company_page, name='company-page'),

    path(
        'page/<str:symbol>/',
        company_detail_page,
        name='company-detail-page'
    ),

    path(
        "compare/",
        compare_companies,
        name="compare-companies"
    ),

    path(
        "screener/",
        screener_page,
        name="screener-page"
    ),

    path(
        '<str:symbol>/',
        CompanyDetailView.as_view(),
        name='company-detail-api'
    ),
]