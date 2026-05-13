from django.contrib import admin

from .models import APIClient

from .utils import generate_api_secret


@admin.register(APIClient)
class APIClientAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "key_id",
        "rate_limit_per_minute",
        "is_active",
    )

    readonly_fields = (
        "key_id",
    )

    def save_model(
        self,
        request,
        obj,
        form,
        change
    ):

        if not obj.secret_encrypted:

            obj.secret_encrypted = (
                generate_api_secret()
            )

        super().save_model(
            request,
            obj,
            form,
            change
        )