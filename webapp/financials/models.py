from django.db import models

class ProfitLoss(models.Model):

    symbol = models.CharField(max_length=20)

    year_id = models.IntegerField(db_column="year_id", primary_key=True)

    sales = models.FloatField(null=True, blank=True)

    net_profit = models.FloatField(null=True, blank=True)

    eps = models.FloatField(null=True, blank=True)

    opm_pct = models.FloatField(null=True, blank=True, db_column="opm_pct")

    class Meta:
        db_table = "fact_profit_loss"
        managed = False

class Analysis(models.Model):

    symbol = models.CharField(
        max_length=20,
        primary_key=True
    )

    period_label = models.CharField(max_length=50)

    compounded_sales_growth_pct = models.FloatField(
        null=True,
        blank=True
    )

    compounded_profit_growth_pct = models.FloatField(
        null=True,
        blank=True
    )

    stock_price_cagr_pct = models.FloatField(
        null=True,
        blank=True
    )

    roe_pct = models.FloatField(
        null=True,
        blank=True
    )

    class Meta:

        db_table = "fact_analysis"

        managed = False