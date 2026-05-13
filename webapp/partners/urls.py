from django.urls import path

from .views import (
    PartnerCompanyAPIView,
    PartnerScoresAPIView,
    PartnerScreenerAPIView,
    PartnerBulkFinancialsAPIView,
    PartnerCompanyFullAPIView,
    PartnerKeysAPIView,
    PartnerDeleteKeyAPIView,
    PartnerWebhooksAPIView,
    PartnerDeleteWebhookAPIView,
)


urlpatterns = [

    path(
        "v1/webhooks/",
        PartnerWebhooksAPIView.as_view(),
        name="partner-webhooks"
    ),

    path(
        "v1/webhooks/<int:webhook_id>/",
        PartnerDeleteWebhookAPIView.as_view(),
        name="partner-delete-webhook"
    ),

    path(
        "v1/keys/",
        PartnerKeysAPIView.as_view(),
        name="partner-keys"
    ),

    path(
        "v1/keys/<uuid:key_id>/",
        PartnerDeleteKeyAPIView.as_view(),
        name="partner-delete-key"
    ),

    path(
        "v1/companies/<str:symbol>/full/",
        PartnerCompanyFullAPIView.as_view(),
        name="partner-company-full"
    ),

    path(
        "v1/companies/",
        PartnerCompanyAPIView.as_view(),
        name="partner-companies"
    ),

    path(
        "v1/scores/",
        PartnerScoresAPIView.as_view(),
        name="partner-scores"
    ),

    path(
        "v1/screener/",
        PartnerScreenerAPIView.as_view(),
        name="partner-screener"
    ),

    path(
        "v1/bulk-financials/",
        PartnerBulkFinancialsAPIView.as_view(),
        name="partner-bulk-financials"
    ),
]