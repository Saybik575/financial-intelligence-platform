from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import connection
from django.db.models import Count, Avg, Q, Min, Max
from django.utils import timezone
from datetime import timedelta
import json

from companies.models import Company
from ml.models import MLScore
from financials.models import Analysis, ProfitLoss
from partners.models import APIClient, APIUsageLog, WebhookSubscription, WebhookEvent
from config.celery import app as celery_app

# Decorator to ensure staff-only access
def staff_required(view_func):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        return view_func(request, *args, **kwargs)
    return login_required(wrapped_view)

@staff_required
def admin_dashboard_index(request):
    """Main admin dashboard landing page."""
    from companies.models import Company
    from partners.models import APIClient, WebhookSubscription
    
    total_companies = Company.objects.count()
    api_clients = APIClient.objects.count()
    webhooks_active = WebhookSubscription.objects.filter(is_active=True).count()
    
    return render(request, 'dashboard/index.html', {
        'page': 'index',
        'title': 'Admin Insights Dashboard',
        'total_companies': total_companies,
        'api_clients': api_clients,
        'webhooks_active': webhooks_active,
    })

@staff_required
def executive_summary(request):
    """Executive Summary: KPIs, sector chart, health scores."""
    # Calculate KPIs
    total_companies = Company.objects.count()
    total_financials = ProfitLoss.objects.count()
    
    ml_scores = MLScore.objects.all()
    avg_health_score = ml_scores.filter(
        overall_score__isnull=False
    ).aggregate(
        avg=Avg('overall_score')
    )['avg'] or 0
    
    # Health label distribution
    health_distribution = ml_scores.values('health_label').annotate(
        count=Count('symbol')
    ).order_by('-count')
    
    # Sector summary using warehouse tables with better data coverage
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COALESCE(ds.sector_name, 'Unknown') AS sector,
                COUNT(DISTINCT dc.symbol) AS count,
                AVG(fpl.return_on_assets) AS avg_roe,
                AVG(fpl.net_profit_margin_pct) AS avg_profit_margin
            FROM dim_company dc
            LEFT JOIN dim_sector ds ON ds.sector_id = dc.sector_id
            LEFT JOIN fact_profit_loss fpl ON fpl.symbol = dc.symbol
            GROUP BY COALESCE(ds.sector_name, 'Unknown')
            HAVING COUNT(DISTINCT dc.symbol) > 0
            ORDER BY count DESC
            LIMIT 10
            """
        )
        sector_stats = [
            {
                'sector': row[0],
                'count': row[1],
                'avg_roe': row[2] if row[2] is not None else 0,
                'avg_profit_margin': row[3] if row[3] is not None else 0,
            }
            for row in cursor.fetchall()
        ]
    
    # Recent activity
    recent_apis = APIUsageLog.objects.select_related('client').order_by('-created_at')[:5]
    recent_webhooks = WebhookEvent.objects.select_related(
        'webhook_subscription__client'
    ).order_by('-created_at')[:5]
    
    context = {
        'page': 'executive_summary',
        'title': 'Executive Summary',
        'total_companies': total_companies,
        'total_financials': total_financials,
        'avg_health_score': f"{avg_health_score:.2f}",
        'health_distribution': list(health_distribution),
        'sector_stats': list(sector_stats),
        'recent_apis': recent_apis,
        'recent_webhooks': recent_webhooks,
    }
    return render(request, 'dashboard/executive_summary.html', context)

@staff_required
def health_monitor(request):
    """Health Monitor: Color-coded company health table."""
    companies = Company.objects.select_related().all()
    
    # Enrich with ML scores
    company_health = []
    for company in companies:
        try:
            ml_score = MLScore.objects.get(symbol=company.symbol)
            health_label = ml_score.health_label
            overall_score = ml_score.overall_score
        except MLScore.DoesNotExist:
            health_label = "Unknown"
            overall_score = 0
        
        company_health.append({
            'company': company,
            'health_label': health_label,
            'overall_score': overall_score,
            'color': get_health_color(health_label),
        })
    
    # Sort by score descending
    company_health.sort(key=lambda x: x['overall_score'], reverse=True)
    
    context = {
        'page': 'health_monitor',
        'title': 'Health Monitor',
        'company_health': company_health,
    }
    return render(request, 'dashboard/health_monitor.html', context)

@staff_required
def anomalies(request):
    """Anomalies: Flagged companies and data quality issues."""
    # Companies with low scores
    low_scores = MLScore.objects.filter(
        overall_score__lt=40
    ).order_by('overall_score')[:20]
    
    # Recent anomaly flagged webhooks
    anomaly_webhooks = WebhookEvent.objects.filter(
        event_type='anomaly_flagged'
    ).select_related(
        'webhook_subscription__client'
    ).order_by('-created_at')[:50]
    
    # Failed financial records (missing key data)
    anomalous_analysis = Analysis.objects.filter(
        Q(roe_pct__isnull=True) | Q(compounded_profit_growth_pct__isnull=True)
    ).order_by('symbol')[:20]
    
    context = {
        'page': 'anomalies',
        'title': 'Anomalies & Flags',
        'low_scores': low_scores,
        'anomaly_webhooks': anomaly_webhooks,
        'anomalous_analysis': anomalous_analysis,
    }
    return render(request, 'dashboard/anomalies.html', context)

@staff_required
def data_quality(request):
    """Data Quality: Company vs year matrix, completeness."""
    # Get company-year combinations with financials
    companies = Company.objects.all()
    years = ProfitLoss.objects.values_list('year_id', flat=True).distinct().order_by('-year_id')[:5]
    
    quality_matrix = []
    for company in companies[:50]:  # Limit for performance
        row = {'company': company, 'years': {}}
        for year in years:
            has_data = ProfitLoss.objects.filter(
                symbol=company.symbol,
                year_id=year
            ).exists()
            row['years'][year] = has_data
        quality_matrix.append(row)
    
    # Completeness score
    total_slots = len(list(companies[:50])) * len(list(years))
    filled_slots = ProfitLoss.objects.filter(
        symbol__in=[c.symbol for c in companies[:50]],
        year_id__in=years
    ).count()
    completeness = (filled_slots / total_slots * 100) if total_slots > 0 else 0
    
    context = {
        'page': 'data_quality',
        'title': 'Data Quality Monitor',
        'quality_matrix': quality_matrix,
        'completeness': f"{completeness:.1f}%",
        'years': list(years),
    }
    return render(request, 'dashboard/data_quality.html', context)

@staff_required
def api_management(request):
    """API Management: Partners, tiers, active keys."""
    clients = APIClient.objects.annotate(
        total_calls=Count('apiusagelog'),
        webhook_count=Count('webhooksubscription')
    )
    
    tier_distribution = clients.values('tier').annotate(count=Count('id'))
    
    context = {
        'page': 'api_management',
        'title': 'API Management',
        'clients': clients,
        'tier_distribution': list(tier_distribution),
    }
    return render(request, 'dashboard/api_management.html', context)

@staff_required
def api_usage_analytics(request):
    """API Usage Analytics: Daily calls, endpoint breakdown, latency percentiles."""
    # Daily call volume (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_calls = APIUsageLog.objects.filter(
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Endpoint breakdown
    endpoint_stats = APIUsageLog.objects.values('endpoint').annotate(
        count=Count('id'),
        avg_response_time=Avg('response_time_ms'),
        error_rate=Count('id', filter=Q(status_code__gte=400)) / Count('id')
    ).order_by('-count')[:10]
    
    # Latency percentiles
    all_response_times = sorted(
        APIUsageLog.objects.values_list('response_time_ms', flat=True),
        reverse=False
    )
    p50 = all_response_times[int(len(all_response_times) * 0.5)] if all_response_times else 0
    p95 = all_response_times[int(len(all_response_times) * 0.95)] if all_response_times else 0
    
    # Status code distribution
    status_distribution = APIUsageLog.objects.values('status_code').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'page': 'api_usage_analytics',
        'title': 'API Usage Analytics',
        'daily_calls': list(daily_calls),
        'endpoint_stats': list(endpoint_stats),
        'p50_latency': f"{p50:.2f}ms",
        'p95_latency': f"{p95:.2f}ms",
        'status_distribution': list(status_distribution),
    }
    return render(request, 'dashboard/api_usage_analytics.html', context)

@staff_required
def webhooks_monitor(request):
    """Webhooks: Subscriptions, delivery success rates, failed events."""
    subscriptions = WebhookSubscription.objects.select_related(
        'client'
    ).annotate(
        total_events=Count('events'),
        success_count=Count('events', filter=Q(events__status='success')),
        failed_count=Count('events', filter=Q(events__status='failed')),
    )
    
    # Calculate success rates
    for sub in subscriptions:
        if sub.total_events > 0:
            sub.success_rate = (sub.success_count / sub.total_events * 100)
        else:
            sub.success_rate = 0
    
    # Recent failures
    recent_failures = WebhookEvent.objects.filter(
        status='failed'
    ).select_related(
        'webhook_subscription__client'
    ).order_by('-created_at')[:20]
    
    # Event type distribution
    event_distribution = WebhookEvent.objects.values('event_type').annotate(
        count=Count('id'),
        success=Count('id', filter=Q(status='success')),
        failed=Count('id', filter=Q(status='failed'))
    )
    
    context = {
        'page': 'webhooks',
        'title': 'Webhooks Monitor',
        'subscriptions': subscriptions,
        'recent_failures': recent_failures,
        'event_distribution': list(event_distribution),
    }
    return render(request, 'dashboard/webhooks_monitor.html', context)

@staff_required
def bulk_import(request):
    """Bulk Import: CSV upload and validation interface."""
    if request.method == 'POST':
        # Handle file upload
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # Parse and validate CSV
            import csv
            import io
            
            try:
                decoded_file = uploaded_file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(decoded_file))
                rows = list(reader)
                
                # Validation (sample)
                validation_errors = []
                for i, row in enumerate(rows, start=2):
                    if 'symbol' not in row or not row['symbol']:
                        validation_errors.append(f"Row {i}: Missing symbol")
                
                if validation_errors:
                    return render(
                        request,
                        'dashboard/bulk_import.html',
                        {
                            'page': 'bulk_import',
                            'title': 'Bulk Import',
                            'validation_errors': validation_errors,
                        }
                    )
                
                return render(
                    request,
                    'dashboard/bulk_import.html',
                    {
                        'page': 'bulk_import',
                        'title': 'Bulk Import',
                        'success': f"Uploaded {len(rows)} rows successfully",
                        'row_count': len(rows),
                    }
                )
            except Exception as e:
                return render(
                    request,
                    'dashboard/bulk_import.html',
                    {
                        'page': 'bulk_import',
                        'title': 'Bulk Import',
                        'error': str(e),
                    }
                )
    
    context = {
        'page': 'bulk_import',
        'title': 'Bulk Import',
    }
    return render(request, 'dashboard/bulk_import.html', context)

@staff_required
def celery_monitor(request):
    """Celery Monitor: Task status, queue stats, manual re-run."""
    try:
        app_inspect = celery_app.control.inspect()
        
        # Get active tasks
        active_tasks = app_inspect.active() or {}
        scheduled_tasks = app_inspect.scheduled() or {}
        
        # Count tasks
        total_active = sum(len(v) if v else 0 for v in active_tasks.values())
        total_scheduled = sum(len(v) if v else 0 for v in scheduled_tasks.values())
        
        context = {
            'page': 'celery_monitor',
            'title': 'Celery Monitor',
            'total_active': total_active,
            'total_scheduled': total_scheduled,
            'active_tasks': active_tasks,
            'scheduled_tasks': scheduled_tasks,
        }
    except Exception as e:
        context = {
            'page': 'celery_monitor',
            'title': 'Celery Monitor',
            'error': f"Could not connect to Celery: {str(e)}",
        }
    
    return render(request, 'dashboard/celery_monitor.html', context)

def get_health_color(health_label):
    """Map health label to color."""
    colors = {
        'Strong': '#10b981',      # Green
        'Healthy': '#3b82f6',      # Blue
        'Moderate': '#f59e0b',     # Amber
        'Weak': '#ef4444',         # Red
        'Unknown': '#9ca3af',      # Gray
    }
    return colors.get(health_label, '#9ca3af')
