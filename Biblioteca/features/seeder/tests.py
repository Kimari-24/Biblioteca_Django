import random
from collections import Counter
from datetime import timedelta
from types import SimpleNamespace

from django.conf import settings
from django.test import SimpleTestCase

from .management.commands.seed import BOOKS, Command


class SeedGenerationTests(SimpleTestCase):
    """Comprueba los invariantes de los datos generados, sin escribir en Firestore."""

    def setUp(self):
        random.seed(7)
        self.books = [
            {'ref': SimpleNamespace(id=f'b{i}'), 'title': t, 'author': a, 'category': c, 'isbn': i_,
             'copies_total': random.randint(2, 5)}
            for i, (t, a, c, i_) in enumerate(BOOKS)
        ]
        self.students = [{'uid': f's{i}', 'name': f'Est {i}', 'email': f'e{i}@x.com'} for i in range(2)]
        self.loans = Command()._generate_loans(self.books, self.students)

    def test_never_more_active_loans_than_copies(self):
        active = Counter(loan['book_id'] for loan in self.loans if loan['status'] == 'active')
        for book in self.books:
            self.assertLessEqual(active[book['ref'].id], book['copies_total'])

    def test_available_copies_match_active_loans(self):
        active = Counter(loan['book_id'] for loan in self.loans if loan['status'] == 'active')
        for book in self.books:
            self.assertEqual(book['copies_available'], book['copies_total'] - active[book['ref'].id])

    def test_students_respect_the_active_loan_limit(self):
        active = Counter(loan['user_id'] for loan in self.loans if loan['status'] == 'active')
        self.assertTrue(all(n <= settings.MAX_ACTIVE_LOANS for n in active.values()))

    def test_dates_are_coherent(self):
        for loan in self.loans:
            self.assertEqual(loan['due_at'] - loan['loaned_at'], timedelta(days=settings.LOAN_DAYS))
            if loan['returned_at']:
                self.assertGreaterEqual(loan['returned_at'], loan['loaned_at'])
            if loan['cancelled_at']:
                self.assertGreaterEqual(loan['cancelled_at'], loan['loaned_at'])

    def test_has_a_mix_of_statuses(self):
        self.assertGreaterEqual(len({loan['status'] for loan in self.loans}), 3)
