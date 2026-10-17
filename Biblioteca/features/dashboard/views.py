from django.shortcuts import render

from core.decorators import librarian_required

from . import charts, stats


@librarian_required
def index(request):
    s = stats.dashboard_stats()
    return render(request, 'dashboard/index.html', {
        'kpis': s['kpis'],
        'chart_months': charts.loans_per_month(s['month_series'], first=True),
        'chart_status': charts.loans_by_status(s['status_counts']),
        'chart_top': charts.top_books(s['top_books']),
        'chart_category': charts.loans_by_category(s['by_category']),
    })
