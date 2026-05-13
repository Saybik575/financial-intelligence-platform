from rest_framework.views import APIView

from rest_framework.response import Response

from rest_framework.exceptions import Throttled

from django.http import JsonResponse

from companies.models import Company

from companies.serializers import CompanySerializer

from .auth import verify_hmac

from .models import APIClient

from .utils import generate_api_secret

from ml.models import MLScore

from django.db.models import Q

from financials.models import Analysis

from financials.models import ProfitLoss

from .models import WebhookSubscription

import time

from .tasks import log_api_usage

from .throttles import PartnerRateThrottle

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .serializers import (
    ScoresResponseSerializer,
    ScreenerResponseSerializer,
    BulkFinancialsResponseSerializer,
    CompanyFullResponseSerializer,
    APIKeySerializer,
    WebhookSubscriptionSerializer,
)
from rest_framework import status
from rest_framework.parsers import JSONParser


class PartnerAPIView(APIView):

    # throttle_classes = [
    #     PartnerRateThrottle
    # ]


    def initial(self, request, *args, **kwargs):

        self._partner_start_time = time.time()

        return super().initial(

            request,
            *args,
            **kwargs
        )


    def throttled(self, request, wait):

        raise Throttled(

            wait=wait,

            detail=getattr(
                self,
                "_partner_throttle_details",
                {
                    "error": "Rate limit exceeded"
                }
            )
        )


    def finalize_response(

        self,
        request,
        response,
        *args,
        **kwargs
    ):

        response = super().finalize_response(

            request,
            response,
            *args,
            **kwargs
        )

        client = getattr(
            request,
            "_partner_client",
            None
        )

        if hasattr(response, "data"):

            response_payload = response.data

        else:

            response_payload = getattr(
                response,
                "content",
                b""
            )

        try:

            # log_api_usage.delay(
            #
            #     client.id if client else None,
            #
            #     request.path,
            #
            #     request.method,
            #
            #     response.status_code,
            #
            #     (time.time() - self._partner_start_time) * 1000,
            #
            #     request.META.get(
            #         "REMOTE_ADDR"
            #     ),
            #
            #     len(request.body or b""),
            #
            #     len(str(response_payload).encode("utf-8")),
            # )

        except Exception:

            pass

        return response

class PartnerCompanyAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="list_top_companies",
        summary="List Top Companies",
        description="Get top 10 companies available in the system. Requires HMAC authentication.",
        tags=["Companies"],
        responses={
            200: OpenApiResponse(
                description="List of companies",
                examples={
                    "application/json": {
                        "partner": "Partner Name",
                        "results": [
                            {
                                "symbol": "TCS",
                                "name": "Tata Consultancy Services",
                                "sector": "IT",
                                "country": "India"
                            }
                        ]
                    }
                }
            ),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def get(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        companies = Company.objects.all()[:10]

        serializer = CompanySerializer(
            companies,
            many=True
        )

        return Response({

            "partner":
                client.name,

            "results":
                serializer.data
        })

class PartnerScoresAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="list_ml_scores",
        summary="Get ML Scores for Companies",
        description="Get health scores and labels for specific companies. Pass comma-separated symbols in query parameter.",
        tags=["Scores"],
        parameters=[
            OpenApiParameter(
                name="symbols",
                description="Comma-separated company symbols (e.g., TCS,INFY,WIPRO)",
                required=False,
                type=str,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="List of ML scores",
                response=ScoresResponseSerializer(many=True),
            ),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def get(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        symbols = request.GET.get(
            "symbols"
        )

        scores = MLScore.objects.all()

        latest_scores = {}

        for score in scores:

            if score.symbol not in latest_scores:

                latest_scores[
                    score.symbol
                ] = score

        if symbols:

            symbol_list = [
                s.strip()
                for s in symbols.split(",")
            ]

            latest_scores = {

                k: v for k, v in
                latest_scores.items()

                if k in symbol_list
            }

        results = []

        for symbol, score in (
            latest_scores.items()
        ):

            results.append({

                "symbol": symbol,

                "overall_score":
                    score.overall_score,

                "health_label":
                    score.health_label,
            })

        return Response(results)
        

class PartnerScreenerAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="screener_companies",
        summary="Screen Companies by Criteria",
        description="Screen companies based on ROE, sales growth, and health score criteria.",
        tags=["Screening"],
        parameters=[
            OpenApiParameter(
                name="min_roe",
                description="Minimum ROE percentage (e.g., 15.0)",
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name="min_sales_growth",
                description="Minimum sales growth percentage",
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name="min_health_score",
                description="Minimum health score (0-100)",
                required=False,
                type=float,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Screened companies",
                response=ScreenerResponseSerializer(many=True),
            ),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def get(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        min_roe = request.GET.get(
            "min_roe"
        )

        min_sales_growth = request.GET.get(
            "min_sales_growth"
        )

        min_health_score = request.GET.get(
            "min_health_score"
        )

        query = Q(period_label="10Y")

        if min_roe:

            query &= Q(
                roe_pct__gte=float(min_roe)
            )

        if min_sales_growth:

            query &= Q(
                compounded_sales_growth_pct__gte=
                float(min_sales_growth)
            )

        records = Analysis.objects.filter(query)

        results = []

        for record in records:

            company = Company.objects.filter(
                symbol=record.symbol
            ).first()

            score = MLScore.objects.filter(
                symbol=record.symbol
            ).first()

            if min_health_score:

                if (
                    not score or
                    score.overall_score <
                    float(min_health_score)
                ):

                    continue

            if company:

                results.append({

                    "symbol":
                        company.symbol,

                    "company_name":
                        company.company_name,

                    "sector":
                        str(company.sector),

                    "roe":
                        record.roe_pct,

                    "sales_growth":
                        record.compounded_sales_growth_pct,

                    "health_score":
                        score.overall_score
                        if score else None,

                    "health_label":
                        score.health_label
                        if score else None,
                })

        return Response({

            "partner":
                client.name,

            "count":
                len(results),

            "results":
                results
        })
    
class PartnerBulkFinancialsAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="get_bulk_financials",
        summary="Get Latest Financial Data in Bulk",
        description="Get latest financial data (P&L) for up to 10 companies at once.",
        tags=["Financials"],
        parameters=[
            OpenApiParameter(
                name="symbols",
                description="Comma-separated company symbols (required, max 10)",
                required=True,
                type=str,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Latest financial data",
                response=BulkFinancialsResponseSerializer(many=True),
            ),
            400: OpenApiResponse(description="Invalid request (missing symbols or too many)"),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def get(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        symbols = request.GET.get(
            "symbols"
        )

        if not symbols:

            return Response({

                "error":
                    "symbols parameter required"

            }, status=400)

        symbol_list = [

            s.strip().upper()

            for s in symbols.split(",")
        ]

        if len(symbol_list) > 10:

            return Response({

                "error":
                    "Maximum 10 symbols allowed"

            }, status=400)

        results = []

        for symbol in symbol_list:

            company = Company.objects.filter(
                symbol=symbol
            ).first()

            latest_financial = (
                ProfitLoss.objects.filter(
                    symbol=symbol
                )
                .order_by("-year_id")
                .first()
            )

            if company and latest_financial:

                results.append({

                    "symbol":
                        company.symbol,

                    "company_name":
                        company.company_name,

                    "sales":
                        latest_financial.sales,

                    "net_profit":
                        latest_financial.net_profit,

                    "eps":
                        latest_financial.eps,

                    "year_id":
                        latest_financial.year_id,
                })

        return Response({

            "partner":
                client.name,

            "count":
                len(results),

            "results":
                results
        })
    
class PartnerCompanyFullAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="get_company_full",
        summary="Get Full Company Details",
        description="Get comprehensive company details including financial history and ML scores.",
        tags=["Companies"],
        parameters=[
            OpenApiParameter(
                name="symbol",
                description="Company symbol (e.g., TCS)",
                required=True,
                type=str,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Full company details",
                response=CompanyFullResponseSerializer,
            ),
            404: OpenApiResponse(description="Company not found"),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def get(self, request, symbol):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        company = Company.objects.filter(
            symbol=symbol
        ).first()

        if not company:

            return Response({

                "error":
                    "Company not found"

            }, status=404)

        financials = ProfitLoss.objects.filter(
            symbol=symbol
        ).order_by("-year_id")

        score = MLScore.objects.filter(
            symbol=symbol
        ).first()

        financial_data = []

        for item in financials:

            financial_data.append({

                "year_id":
                    item.year_id,

                "sales":
                    item.sales,

                "net_profit":
                    item.net_profit,

                "eps":
                    item.eps,
            })

        response_data = {

            "partner":
                client.name,

            "company":
                CompanySerializer(company).data,

            "ml_score": {

                "overall_score":
                    score.overall_score
                    if score else None,

                "health_label":
                    score.health_label
                    if score else None,
            },

            "financial_history":
                financial_data,
        }

        return Response(response_data)
    
class PartnerKeysAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="list_api_keys",
        summary="List API Keys",
        description="List all API keys for the authenticated client.",
        tags=["API Management"],
        responses={
            200: OpenApiResponse(
                description="List of API keys",
                response=APIKeySerializer(many=True),
            ),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def get(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        results = [{

            "key_id":
                str(client.key_id),

            "name":
                client.name,

            "rate_limit_per_minute":
                client.rate_limit_per_minute,

            "is_active":
                client.is_active,

            "created_at":
                client.created_at,
        }]

        return Response(results)

    @extend_schema(
        operation_id="create_api_key",
        summary="Create New API Key",
        description="Create a new secondary API key for the authenticated client.",
        tags=["API Management"],
        responses={
            201: OpenApiResponse(
                description="New API key created",
                examples={
                    "application/json": {
                        "message": "New API key created",
                        "key_id": "uuid-here",
                        "secret": "secret-key-here"
                    }
                }
            ),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def post(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        new_secret = generate_api_secret()

        new_client = APIClient.objects.create(

            name=f"{client.name} Secondary Key",

            secret_encrypted=new_secret,

            rate_limit_per_minute=
                client.rate_limit_per_minute,
        )

        return Response({

            "message":
                "New API key created",

            "key_id":
                str(new_client.key_id),

            "secret":
                new_secret,
        })
    
class PartnerDeleteKeyAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="delete_api_key",
        summary="Delete API Key",
        description="Delete a specific API key by key_id.",
        tags=["API Management"],
        parameters=[
            OpenApiParameter(
                name="key_id",
                description="API Key UUID to delete",
                required=True,
                type=str,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="API key deleted",
                examples={
                    "application/json": {
                        "message": "API key deleted"
                    }
                }
            ),
            404: OpenApiResponse(description="Key not found"),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def delete(self, request, key_id):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        target_key = APIClient.objects.filter(
            key_id=key_id
        ).first()

        if not target_key:

            return Response({

                "error":
                    "Key not found"

            }, status=404)

        target_key.delete()

        return Response({

            "message":
                "API key deleted"
        })
    
class PartnerWebhooksAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="list_webhooks",
        summary="List Webhook Subscriptions",
        description="List all webhook subscriptions for the authenticated client.",
        tags=["Webhooks"],
        responses={
            200: OpenApiResponse(
                description="List of webhooks",
                response=WebhookSubscriptionSerializer(many=True),
            ),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def get(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        webhooks = (
            WebhookSubscription.objects
            .filter(client=client)
        )

        results = []

        for webhook in webhooks:

            results.append({

                "id":
                    webhook.id,

                "target_url":
                    webhook.target_url,

                "event_type":
                    webhook.event_type,

                "is_active":
                    webhook.is_active,

                "created_at":
                    webhook.created_at,
            })

        return Response(results)

    @extend_schema(
        operation_id="create_webhook",
        summary="Create Webhook Subscription",
        description="Subscribe to webhook events (score_updated, anomaly_flagged).",
        tags=["Webhooks"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "target_url": {
                        "type": "string",
                        "description": "HTTP endpoint to POST events to"
                    },
                    "event_type": {
                        "type": "string",
                        "enum": ["score_updated", "anomaly_flagged"],
                        "description": "Type of event to subscribe to"
                    }
                },
                "required": ["target_url", "event_type"]
            }
        },
        responses={
            201: OpenApiResponse(
                description="Webhook created",
                examples={
                    "application/json": {
                        "message": "Webhook created",
                        "id": 123
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid request"),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def post(self, request):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        target_url = request.data.get(
            "target_url"
        )

        event_type = request.data.get(
            "event_type"
        )

        if not target_url or not event_type:

            return Response({

                "error":
                    "target_url and event_type required"

            }, status=400)

        allowed_events = {
            choice[0]
            for choice in WebhookSubscription.EVENT_CHOICES
        }

        if event_type not in allowed_events:

            return Response({

                "error":
                    "Invalid event_type",

                "allowed_events":
                    sorted(allowed_events)
            }, status=400)

        webhook = (
            WebhookSubscription.objects
            .create(

                client=client,

                target_url=target_url,

                event_type=event_type,
            )
        )

        return Response({

            "message":
                "Webhook created",

            "id":
                webhook.id,
        })
    
class PartnerDeleteWebhookAPIView(PartnerAPIView):

    @extend_schema(
        operation_id="delete_webhook",
        summary="Delete Webhook Subscription",
        description="Delete a specific webhook subscription by ID.",
        tags=["Webhooks"],
        parameters=[
            OpenApiParameter(
                name="webhook_id",
                description="Webhook subscription ID to delete",
                required=True,
                type=int,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Webhook deleted",
                examples={
                    "application/json": {
                        "message": "Webhook deleted"
                    }
                }
            ),
            404: OpenApiResponse(description="Webhook not found"),
            401: OpenApiResponse(description="Invalid API signature")
        },
    )
    def delete(self, request, webhook_id):

        client = verify_hmac(request)

        if not client:

            return JsonResponse({

                "error":
                    "Invalid API signature"

            }, status=401)

        webhook = (
            WebhookSubscription.objects
            .filter(

                id=webhook_id,

                client=client
            )
            .first()
        )

        if not webhook:

            return Response({

                "error":
                    "Webhook not found"

            }, status=404)

        webhook.delete()

        return Response({

            "message":
                "Webhook deleted"
        })