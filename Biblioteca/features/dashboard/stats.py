"""Estadísticas del dashboard.

`compute_stats` es una función pura (recibe listas, devuelve números) y se prueba sin
Firestore. `dashboard_stats` solo lee los datos y se los pasa.
"""
from collections import Counter

from django.utils import timezone

from features.books import services as books_service
from features.loans import services as loans_service

MONTHS_ES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def last_months(count, now):
    """Últimos `count` meses como lista de (año, mes), el más antiguo primero."""
    now = timezone.localtime(now)
    year, month = now.year, now.month
    months = []
    for _ in range(count):
        months.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return months[::-1]


def compute_stats(loans, books, now=None, months=6):
    now = now or timezone.now()
    status_counts = Counter()
    for loan in loans:
        key = 'overdue' if loan['overdue'] else loan['status']
        status_counts[key] += 1

    by_month = Counter()
    for loan in loans:
        local = timezone.localtime(loan['loaned_at'])
        by_month[(local.year, local.month)] += 1
    month_series = [(f'{MONTHS_ES[m - 1]} {y}', by_month[(y, m)]) for y, m in last_months(months, now)]

    return {
        'kpis': {
            'books': len(books),
            'copies_available': sum(b['copies_available'] for b in books),
            'loans': len(loans),
            'active': status_counts['active'] + status_counts['overdue'],
            'overdue': status_counts['overdue'],
        },
        'status_counts': status_counts,
        'month_series': month_series,
        'top_books': Counter(loan['book_title'] for loan in loans).most_common(8),
        'by_category': Counter(loan['book_category'] for loan in loans).most_common(),
    }


def dashboard_stats(months=6):
    return compute_stats(loans_service.list_loans(), books_service.list_books(), months=months)
