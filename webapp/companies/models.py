from django.db import models

class Sector(models.Model):

    sector_id = models.IntegerField(primary_key=True)

    sector_name = models.CharField(max_length=255)

    class Meta:
        db_table = "dim_sector"
        managed = False

    def __str__(self):
        return self.sector_name

class Company(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True)
    company_name = models.CharField(max_length=255)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.DO_NOTHING,
        db_column="sector_id",
        null=True,
        blank=True
    )

    class Meta:
        db_table = "dim_company"
        managed = False

    def __str__(self):
        return self.company_name