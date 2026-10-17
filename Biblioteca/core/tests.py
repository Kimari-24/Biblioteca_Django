from django.core.paginator import Paginator
from django.test import RequestFactory, SimpleTestCase

from .pagination import paginate
from .testing import LIBRARIAN, STUDENT, SessionTestCase


class PaginateTests(SimpleTestCase):
    def test_splits_items_and_keeps_filters(self):
        request = RequestFactory().get('/books/', {'q': 'python', 'page': '2'})
        ctx = paginate(request, list(range(25)), per_page=10)
        self.assertEqual(list(ctx['page_obj']), list(range(10, 20)))
        self.assertEqual(ctx['page_obj'].paginator.num_pages, 3)
        self.assertEqual(ctx['querystring'], 'q=python')  # sin `page`

    def test_invalid_page_falls_back_to_valid_one(self):
        request = RequestFactory().get('/', {'page': '999'})
        self.assertEqual(paginate(request, list(range(25)), per_page=10)['page_obj'].number, 3)
        request = RequestFactory().get('/', {'page': 'abc'})
        self.assertEqual(paginate(request, list(range(25)), per_page=10)['page_obj'].number, 1)

    def test_many_pages_are_elided(self):
        request = RequestFactory().get('/', {'page': '10'})
        ctx = paginate(request, list(range(200)), per_page=10)
        self.assertIn(Paginator.ELLIPSIS, ctx['page_range'])
        self.assertLess(len(ctx['page_range']), 20)


class AccessControlTests(SessionTestCase):
    def test_anonymous_is_sent_to_login_with_next(self):
        response = self.client.get('/books/')
        self.assertRedirects(response, '/login/?next=/books/', fetch_redirect_response=False)

    def test_student_cannot_open_librarian_pages(self):
        self.login_as(STUDENT)
        for url in ('/dashboard/', '/loans/', '/books/new/'):
            self.assertRedirects(self.client.get(url), '/books/', fetch_redirect_response=False)

    def test_librarian_cannot_open_student_pages(self):
        self.login_as(LIBRARIAN)
        self.assertRedirects(self.client.get('/loans/mine/'), '/books/', fetch_redirect_response=False)

    def test_home_redirects_by_role(self):
        self.login_as(LIBRARIAN)
        self.assertRedirects(self.client.get('/'), '/dashboard/', fetch_redirect_response=False)
        self.login_as(STUDENT)
        self.assertRedirects(self.client.get('/'), '/books/', fetch_redirect_response=False)
