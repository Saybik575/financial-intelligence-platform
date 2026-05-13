from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard_index, name='admin_index'),
    path('executive-summary/', views.executive_summary, name='executive_summary'),
    path('health-monitor/', views.health_monitor, name='health_monitor'),
    path('anomalies/', views.anomalies, name='anomalies'),
    path('data-quality/', views.data_quality, name='data_quality'),
    path('api-management/', views.api_management, name='api_management'),
    path('api-usage/', views.api_usage_analytics, name='api_usage_analytics'),
    path('webhooks/', views.webhooks_monitor, name='webhooks'),
    path('bulk-import/', views.bulk_import, name='bulk_import'),
    path('celery/', views.celery_monitor, name='celery_monitor'),
]
