from rest_framework import serializers

from .models import Company
from financials.models import ProfitLoss


class CompanySerializer(serializers.ModelSerializer):

    sector_name = serializers.CharField(
        source="sector.sector_name",
        read_only=True
    )

    class Meta:

        model = Company

        fields = [
            "symbol",
            "company_name",
            "sector",
            "sector_name",
        ]


class ProfitLossSerializer(serializers.ModelSerializer):

    class Meta:

        model = ProfitLoss

        fields = "__all__"