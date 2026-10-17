from datetime import datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase

from core.testing import LIBRARIAN, STUDENT, SessionTestCase

from . import rules, services
from .rules import LoanError

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=dt_timezone.utc)


def loan(**overrides):
    data = {
        'id': 'l1', 'book_id': 'b1', 'book_title': 'Clean Code', 'book_category': 'Programación',
        'user_id': STUDENT['uid'], 'user_name': 'Estudiante', 'user_email': 'est@example.com',
        'status': 'active', 'loaned_at': NOW - timedelta(days=3), 'due_at': NOW + timedelta(days=11),
        'overdue': False,
    }
    return {**data, **overrides}


class BorrowRulesTests(SimpleTestCase):
    book = {'title': 'Clean Code', 'copies_available': 1}

    def test_valid_borrow(self):
        rules.check_can_borrow(self.book, 'b1', active_loans=[])

    def test_book_must_exist(self):
        with self.assertRaisesMessage(LoanError, 'no existe'):
            rules.check_can_borrow(None, 'b1', [])

    def test_needs_available_copies(self):
        with self.assertRaisesMessage(LoanError, 'No hay copias'):
            rules.check_can_borrow({'copies_available': 0}, 'b1', [])

    def test_limit_of_active_loans(self):
        active = [loan(book_id=f'x{i}') for i in range(3)]
        with self.assertRaisesMessage(LoanError, 'Ya tienes 3 préstamos activos'):
            rules.check_can_borrow(self.book, 'b1', active)

    def test_cannot_borrow_same_book_twice(self):
        with self.assertRaisesMessage(LoanError, 'Ya tienes un préstamo activo de este libro'):
            rules.check_can_borrow(self.book, 'b1', [loan(book_id='b1')])

    def test_can_borrow_different_book_with_one_active(self):
        rules.check_can_borrow(self.book, 'b1', [loan(book_id='b2')])


class CloseRulesTests(SimpleTestCase):
    def test_owner_can_close(self):
        rules.check_can_close(loan(), STUDENT)

    def test_librarian_can_close_anyones_loan(self):
        rules.check_can_close(loan(), LIBRARIAN)

    def test_other_student_cannot(self):
        other = {**STUDENT, 'uid': 'otro'}
        with self.assertRaisesMessage(LoanError, 'no es tuyo'):
            rules.check_can_close(loan(), other)

    def test_only_active_loans_can_be_closed(self):
        for status in ('returned', 'cancelled'):
            with self.assertRaisesMessage(LoanError, 'ya no está activo'):
                rules.check_can_close(loan(status=status), STUDENT)

    def test_missing_loan(self):
        with self.assertRaises(LoanError):
            rules.check_can_close(None, STUDENT)


class OverdueTests(SimpleTestCase):
    def test_active_past_due_is_overdue(self):
        self.assertTrue(rules.is_overdue(loan(due_at=NOW - timedelta(days=1)), NOW))

    def test_active_before_due_is_not(self):
        self.assertFalse(rules.is_overdue(loan(due_at=NOW + timedelta(days=1)), NOW))

    def test_returned_is_never_overdue(self):
        self.assertFalse(rules.is_overdue(loan(status='returned', due_at=NOW - timedelta(days=9)), NOW))


class LoanViewTests(SessionTestCase):
    def test_student_borrows(self):
        self.login_as(STUDENT)
        with mock.patch.object(services, 'borrow') as borrow, \
                mock.patch.object(services, 'list_loans', return_value=[]):
            response = self.client.post('/loans/borrow/b1/', follow=True)
        borrow.assert_called_once_with('b1', STUDENT)
        self.assertContains(response, 'Préstamo registrado')

    def test_business_error_is_shown_to_the_user(self):
        self.login_as(STUDENT)
        with mock.patch.object(services, 'borrow', side_effect=LoanError('No hay copias disponibles de este libro.')), \
                mock.patch.object(services, 'list_loans', return_value=[]):
            response = self.client.post('/loans/borrow/b1/', follow=True)
        self.assertContains(response, 'No hay copias disponibles')

    def test_librarian_cannot_borrow(self):
        self.login_as(LIBRARIAN)
        with mock.patch.object(services, 'borrow') as borrow:
            self.client.post('/loans/borrow/b1/')
        borrow.assert_not_called()

    def test_borrow_requires_post(self):
        self.login_as(STUDENT)
        self.assertEqual(self.client.get('/loans/borrow/b1/').status_code, 405)

    def test_return_and_cancel_use_the_session_user(self):
        self.login_as(STUDENT)
        with mock.patch.object(services, 'return_loan') as ret, mock.patch.object(services, 'cancel_loan') as can:
            self.client.post('/loans/l1/return/')
            self.client.post('/loans/l1/cancel/')
        ret.assert_called_once_with('l1', STUDENT)
        can.assert_called_once_with('l1', STUDENT)

    def test_next_redirect_ignores_external_urls(self):
        self.login_as(STUDENT)
        with mock.patch.object(services, 'return_loan'):
            ok = self.client.post('/loans/l1/return/', {'next': '/loans/mine/?page=2'})
            bad = self.client.post('/loans/l1/return/', {'next': 'https://evil.example/'})
        self.assertEqual(ok['Location'], '/loans/mine/?page=2')
        self.assertEqual(bad['Location'], '/')

    def test_my_loans_only_asks_for_own_loans_and_paginates(self):
        self.login_as(STUDENT)
        many = [loan(id=f'l{i}', book_title=f'Libro {i:02}') for i in range(25)]
        with mock.patch.object(services, 'list_loans', return_value=many) as list_loans:
            response = self.client.get('/loans/mine/?page=2')
        list_loans.assert_called_once_with(user_id=STUDENT['uid'])
        self.assertContains(response, 'Libro 10')
        self.assertNotContains(response, 'Libro 09')
        self.assertContains(response, 'Página 2 de 3')

    def test_all_loans_keeps_status_filter_in_pagination(self):
        self.login_as(LIBRARIAN)
        many = [loan(id=f'l{i}') for i in range(25)]
        with mock.patch.object(services, 'list_loans', return_value=many) as list_loans:
            response = self.client.get('/loans/?status=active')
        list_loans.assert_called_once_with(status='active')
        self.assertContains(response, '?status=active&page=2')
