from rest_framework import serializers
from companies.models import Company
from ml.models import MLScore
from financials.models import ProfitLoss, Analysis
from .models import APIClient, WebhookSubscription, WebhookEvent, APIUsageLog


class CompanyBasicSerializer(serializers.ModelSerializer):
    """Minimal company serializer for partner API."""
    
    class Meta:
        model = Company
        fields = ['symbol', 'name', 'sector', 'country']


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Detailed company serializer for partner API."""
    
    class Meta:
        model = Company
        fields = [
            'symbol',
            'name',
            'sector',
            'country',
            'market_cap',
            'industry',
            'created_at',
            'updated_at',
        ]


class MLScoreSerializer(serializers.ModelSerializer):
    """ML score serializer for partner API."""
    
    health_label = serializers.CharField(read_only=True)
    
    class Meta:
        model = MLScore
        fields = [
            'symbol',
            'overall_score',
            'profitability_score',
            'growth_score',
            'leverage_score',
            'cashflow_score',
            'dividend_score',
            'trend_score',
            'health_label',
            'computed_at',
        ]


class ProfitLossSerializer(serializers.ModelSerializer):
    """Profit & Loss statement serializer for partner API."""
    
    class Meta:
        model = ProfitLoss
        fields = [
            'symbol',
            'year_id',
            'revenue',
            'cost_of_goods_sold',
            'gross_profit',
            'operating_income',
            'net_income',
            'eps',
            'updated_at',
        ]


class AnalysisSerializer(serializers.ModelSerializer):
    """Financial analysis serializer for partner API."""
    
    class Meta:
        model = Analysis
        fields = [
            'symbol',
            'period_label',
            'compounded_sales_growth_pct',
            'compounded_profit_growth_pct',
            'stock_price_cagr_pct',
            'roe_pct',
        ]


class ScoresResponseSerializer(serializers.Serializer):
    """Response serializer for Scores endpoint."""
    
    symbol = serializers.CharField()
    overall_score = serializers.FloatField()
    health_label = serializers.CharField()
    trend_score = serializers.FloatField(required=False)
    profitability_score = serializers.FloatField(required=False)


class ScreenerResponseSerializer(serializers.Serializer):
    """Response serializer for Screener endpoint."""
    
    symbol = serializers.CharField()
    name = serializers.CharField()
    sector = serializers.CharField()
    roe = serializers.FloatField()
    sales_growth = serializers.FloatField()
    health_label = serializers.CharField()
    overall_score = serializers.FloatField()


class BulkFinancialsResponseSerializer(serializers.Serializer):
    """Response serializer for Bulk Financials endpoint."""
    
    symbol = serializers.CharField()
    year = serializers.IntegerField()
    revenue = serializers.FloatField()
    net_income = serializers.FloatField()
    eps = serializers.FloatField()


class CompanyFullResponseSerializer(serializers.Serializer):
    """Response serializer for Company Full endpoint."""
    
    symbol = serializers.CharField()
    name = serializers.CharField()
    sector = serializers.CharField()
    country = serializers.CharField()
    market_cap = serializers.FloatField()
    overall_score = serializers.FloatField()
    health_label = serializers.CharField()
    financials = ProfitLossSerializer(many=True)
    analysis = AnalysisSerializer()


class APIKeySerializer(serializers.Serializer):
    """Serializer for API key creation/listing."""
    
    key_id = serializers.CharField(read_only=True)
    tier = serializers.CharField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    secret = serializers.SerializerMethodField()
    
    def get_secret(self, obj):
        """Return secret only on create, not on list."""
        request = self.context.get('request')
        if request and request.method == 'POST':
            return obj.get('secret')
        return None


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for webhook subscriptions."""
    
    event_type = serializers.ChoiceField(
        choices=WebhookSubscription.EVENT_CHOICES
    )
    
    class Meta:
        model = WebhookSubscription
        fields = [
            'id',
            'target_url',
            'event_type',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for webhook event tracking."""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id',
            'event_type',
            'company_symbol',
            'status',
            'response_code',
            'error_message',
            'attempt_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class APIUsageLogSerializer(serializers.ModelSerializer):
    """Serializer for API usage logs."""
    
    client_name = serializers.CharField(
        source='client.name',
        read_only=True
    )
    
    class Meta:
        model = APIUsageLog
        fields = [
            'id',
            'client_name',
            'endpoint',
            'method',
            'status_code',
            'response_time_ms',
            'ip_address',
            'request_size',
            'response_size',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
