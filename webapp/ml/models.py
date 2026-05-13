from django.db import models

class MLScore(models.Model):

    symbol = models.CharField(max_length=20, primary_key=True)

    computed_at = models.DateTimeField(null=True, blank=True)

    overall_score = models.FloatField(null=True, blank=True)

    profitability_score = models.FloatField(null=True, blank=True)

    growth_score = models.FloatField(null=True, blank=True)

    leverage_score = models.FloatField(null=True, blank=True)

    cashflow_score = models.FloatField(null=True, blank=True)

    dividend_score = models.FloatField(null=True, blank=True)

    trend_score = models.FloatField(null=True, blank=True)

    health_label = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "fact_ml_scores"
        managed = False