from unittest import mock

from django.test import SimpleTestCase

from core.testing import LIBRARIAN, STUDENT, SessionTestCase

from . import services
from .forms import BookForm
from .services import BookError


def make_books(n):
    return [
        {'id': f'b{i}', 'title': f'Libro {i:02}', 'author': 'Autor', 'category': 'Novela',
         'isbn': '', 'copies_total': 2, 'copies_available': 2}
        for i in range(n)
    ]


class BookFormTests(SimpleTestCase):
    def test_needs_at_least_one_copy(self):
        form = BookForm({'title': 'X', 'author': 'Y', 'category': 'Z', 'copies': 0})
        self.assertFalse(form.is_valid())
        self.assertIn('copies', form.errors)

    def test_isbn_is_optional(self):
        self.assertTrue(BookForm({'title': 'X', 'author': 'Y', 'category': 'Z', 'copies': 1}).is_valid())


class BookServiceRulesTests(SimpleTestCase):
    def book(self, total, available):
        return {'id': 'b1', 'copies_total': total, 'copies_available': available}

    def test_cannot_reduce_copies_below_those_on_loan(self):
        with mock.patch.object(services, 'get_book', return_value=self.book(5, 2)):  # 3 prestadas
            with self.assertRaises(BookError):
                services.update_book('b1', 'T', 'A', 'C', '', copies=2)

    def test_cannot_delete_book_with_copies_on_loan(self):
        with mock.patch.object(services, 'get_book', return_value=self.book(3, 2)):
            with self.assertRaisesMessage(BookError, 'préstamos activos'):
                services.delete_book('b1')

    def test_cannot_delete_missing_book(self):
        with mock.patch.object(services, 'get_book', return_value=None):
            with self.assertRaises(BookError):
                services.delete_book('nope')


class BookViewTests(SessionTestCase):
    def test_list_is_paginated(self):
        self.login_as(STUDENT)
        with mock.patch.object(services, 'list_books', return_value=make_books(25)), \
                mock.patch.object(services, 'list_categories', return_value=['Novela']):
            page1 = self.client.get('/books/')
            page3 = self.client.get('/books/?page=3')
        self.assertContains(page1, 'Libro 09')
        self.assertNotContains(page1, 'Libro 10')
        self.assertContains(page3, 'Libro 24')
        self.assertContains(page1, '25 libros')

    def test_pagination_links_keep_the_filters(self):
        self.login_as(STUDENT)
        with mock.patch.object(services, 'list_books', return_value=make_books(25)), \
                mock.patch.object(services, 'list_categories', return_value=[]):
            response = self.client.get('/books/?q=libro')
        self.assertContains(response, '?q=libro&page=2')

    def test_students_see_borrow_button_and_librarians_see_edit(self):
        with mock.patch.object(services, 'list_books', return_value=make_books(1)), \
                mock.patch.object(services, 'list_categories', return_value=[]):
            self.login_as(STUDENT)
            self.assertContains(self.client.get('/books/'), 'Prestar')
            self.login_as(LIBRARIAN)
            response = self.client.get('/books/')
        self.assertContains(response, 'Editar')
        self.assertNotContains(response, 'Prestar')

    def test_student_cannot_create_or_delete_books(self):
        self.login_as(STUDENT)
        self.assertRedirects(self.client.get('/books/new/'), '/books/', fetch_redirect_response=False)
        with mock.patch.object(services, 'delete_book') as delete:
            self.client.post('/books/b1/delete/')
        delete.assert_not_called()

    def test_librarian_creates_book(self):
        self.login_as(LIBRARIAN)
        with mock.patch.object(services, 'create_book') as create:
            response = self.client.post('/books/new/', {
                'title': 'Nuevo', 'author': 'Autor', 'category': 'Ciencia', 'isbn': '', 'copies': 3})
        self.assertRedirects(response, '/books/', fetch_redirect_response=False)
        create.assert_called_once_with('Nuevo', 'Autor', 'Ciencia', '', 3)

    def test_delete_error_is_shown_as_message(self):
        self.login_as(LIBRARIAN)
        with mock.patch.object(services, 'delete_book', side_effect=BookError('No se puede eliminar')), \
                mock.patch.object(services, 'list_books', return_value=[]), \
                mock.patch.object(services, 'list_categories', return_value=[]):
            response = self.client.post('/books/b1/delete/', follow=True)
        self.assertContains(response, 'No se puede eliminar')
