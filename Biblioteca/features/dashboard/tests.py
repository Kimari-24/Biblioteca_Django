from datetime import datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase

from core.testing import LIBRARIAN, STUDENT, SessionTestCase

from . import charts, stats

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=dt_timezone.utc)


def loan(title='Clean Code', category='Programación', status='returned', overdue=False, days_ago=3):
    return {'book_title': title, 'book_category': category, 'status': status, 'overdue': overdue,
            'loaned_at': NOW - timedelta(days=days_ago)}


BOOKS = [
    {'copies_available': 2, 'copies_total': 3},
    {'copies_available': 0, 'copies_total': 1},
]


class ComputeStatsTests(SimpleTestCase):
    def setUp(self):
        self.loans = [
            loan(status='active'),
            loan(status='active', overdue=True, days_ago=20),
            loan(status='returned', days_ago=40),
            loan(title='Cosmos', category='Ciencia', status='cancelled', days_ago=70),
            loan(title='Clean Code', status='returned', days_ago=100),
        ]
        self.s = stats.compute_stats(self.loans, BOOKS, now=NOW)

    def test_kpis(self):
        self.assertEqual(self.s['kpis'], {'books': 2, 'copies_available': 2, 'loans': 5, 'active': 2, 'overdue': 1})

    def test_overdue_is_counted_apart_from_active(self):
        self.assertEqual(self.s['status_counts']['active'], 1)
        self.assertEqual(self.s['status_counts']['overdue'], 1)

    def test_months_series_has_six_entries_ending_this_month(self):
        labels = [label for label, _ in self.s['month_series']]
        self.assertEqual(len(labels), 6)
        self.assertEqual(labels[-1], 'oct 2026')
        self.assertEqual(labels[0], 'may 2026')

    def test_months_without_loans_count_zero(self):
        by_label = dict(self.s['month_series'])
        self.assertEqual(sum(by_label.values()), 5)
        self.assertEqual(stats.compute_stats([], BOOKS, now=NOW)['month_series'][0][1], 0)

    def test_top_books_ordered_by_loans(self):
        self.assertEqual(self.s['top_books'][0], ('Clean Code', 4))

    def test_by_category(self):
        self.assertEqual(dict(self.s['by_category']), {'Programación': 4, 'Ciencia': 1})

    def test_last_months_crosses_the_year(self):
        jan = datetime(2026, 1, 15, tzinfo=dt_timezone.utc)
        self.assertEqual(stats.last_months(3, jan), [(2025, 11), (2025, 12), (2026, 1)])


class ChartTests(SimpleTestCase):
    def setUp(self):
        self.s = stats.compute_stats([loan(), loan(status='active')], BOOKS, now=NOW)

    def test_every_chart_renders_html(self):
        for html in (
            charts.loans_per_month(self.s['month_series']),
            charts.loans_by_status(self.s['status_counts']),
            charts.top_books(self.s['top_books']),
            charts.loans_by_category(self.s['by_category']),
        ):
            self.assertIn('plotly-graph-div', html)

    def test_plotly_js_is_loaded_only_once(self):
        first = charts.loans_per_month(self.s['month_series'], first=True)
        other = charts.loans_per_month(self.s['month_series'])
        self.assertIn('cdn.plot.ly', first)
        self.assertNotIn('cdn.plot.ly', other)

    def test_chart_container_has_a_fixed_height(self):
        self.assertIn('<div style="height:320px">', charts.loans_per_month(self.s['month_series']))

    def test_status_axis_goes_at_least_to_100(self):
        html = charts.loans_by_status(self.s['status_counts'])
        self.assertIn('"range":[0,100]', html)

    def test_status_axis_grows_beyond_100(self):
        big = stats.compute_stats([loan() for _ in range(150)], BOOKS, now=NOW)
        self.assertNotIn('"range":[0,100]', charts.loans_by_status(big['status_counts']))

    def test_charts_survive_empty_data(self):
        empty = stats.compute_stats([], [], now=NOW)
        self.assertIn('plotly-graph-div', charts.top_books(empty['top_books']))
        self.assertIn('plotly-graph-div', charts.loans_by_category(empty['by_category']))


class DashboardViewTests(SessionTestCase):
    def test_student_is_redirected(self):
        self.login_as(STUDENT)
        self.assertRedirects(self.client.get('/dashboard/'), '/books/', fetch_redirect_response=False)

    def test_librarian_sees_kpis_and_four_charts(self):
        self.login_as(LIBRARIAN)
        data = stats.compute_stats([loan(), loan(status='active')], BOOKS, now=NOW)
        with mock.patch.object(stats, 'dashboard_stats', return_value=data):
            response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'plotly-graph-div', count=4)
        self.assertContains(response, 'Préstamos totales')
