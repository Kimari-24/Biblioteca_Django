"""Siembra libros y préstamos de ejemplo en Firestore.

Uso:  python manage.py seed

Borra los libros y préstamos actuales y los vuelve a crear. Los usuarios NO se
tocan: los préstamos se reparten entre los estudiantes que ya existan.
"""
import random
from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.firebase import get_db
from features.accounts import services as accounts_service

BOOKS = [
    ('Cien años de soledad', 'Gabriel García Márquez', 'Novela', '9780307474728'),
    ('El coronel no tiene quien le escriba', 'Gabriel García Márquez', 'Novela', '9780060732714'),
    ('La vorágine', 'José Eustasio Rivera', 'Novela', '9788437604947'),
    ('Rayuela', 'Julio Cortázar', 'Novela', '9788437604572'),
    ('Pedro Páramo', 'Juan Rulfo', 'Novela', '9788437604947'),
    ('Don Quijote de la Mancha', 'Miguel de Cervantes', 'Clásicos', '9788420412146'),
    ('La Odisea', 'Homero', 'Clásicos', '9788424936518'),
    ('Crimen y castigo', 'Fiódor Dostoievski', 'Clásicos', '9788491050483'),
    ('Python Crash Course', 'Eric Matthes', 'Programación', '9781718502703'),
    ('Fluent Python', 'Luciano Ramalho', 'Programación', '9781492056355'),
    ('Clean Code', 'Robert C. Martin', 'Programación', '9780132350884'),
    ('Django for Beginners', 'William S. Vincent', 'Programación', '9781735467207'),
    ('Introduction to Algorithms', 'Thomas H. Cormen', 'Programación', '9780262046305'),
    ('Una breve historia del tiempo', 'Stephen Hawking', 'Ciencia', '9788498929294'),
    ('Cosmos', 'Carl Sagan', 'Ciencia', '9788408175216'),
    ('El gen egoísta', 'Richard Dawkins', 'Ciencia', '9788434413443'),
    ('Sapiens', 'Yuval Noah Harari', 'Historia', '9788499926223'),
    ('Armas, gérmenes y acero', 'Jared Diamond', 'Historia', '9788483068014'),
    ('Breve historia de Colombia', 'Jorge Orlando Melo', 'Historia', '9789587143393'),
    ('El principito', 'Antoine de Saint-Exupéry', 'Infantil', '9788478887194'),
    ('Matilda', 'Roald Dahl', 'Infantil', '9788420482514'),
    ('Padre rico, padre pobre', 'Robert Kiyosaki', 'Economía', '9781612680194'),
    ('Pensar rápido, pensar despacio', 'Daniel Kahneman', 'Economía', '9788499923260'),
    ('Hábitos atómicos', 'James Clear', 'Desarrollo personal', '9786075694566'),
]

MONTHS_BACK = 6        # los préstamos se reparten en los últimos 6 meses
LOANS_TO_CREATE = 90


class Command(BaseCommand):
    help = 'Crea libros y préstamos de ejemplo en Firestore.'

    def add_arguments(self, parser):
        parser.add_argument('--seed', type=int, default=42, help='Semilla aleatoria (resultados repetibles).')

    def handle(self, *args, **options):
        random.seed(options['seed'])
        db = get_db()
        students = accounts_service.list_students()
        if not students:
            raise CommandError('No hay estudiantes en Firestore. Crea o registra al menos uno primero.')

        self._clear(db, 'loans')
        self._clear(db, 'books')
        books = self._create_books(db)
        loans = self._generate_loans(books, students)
        self._write(db, books, loans)

        statuses = Counter(loan['status'] for loan in loans)
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {len(books)} libros y {len(loans)} préstamos '
            f'({statuses["active"]} activos, {statuses["returned"]} devueltos, '
            f'{statuses["cancelled"]} cancelados) para {len(students)} estudiantes.'
        ))

    def _clear(self, db, collection):
        for doc in db.collection(collection).stream():
            doc.reference.delete()

    def _create_books(self, db):
        books = []
        for title, author, category, isbn in BOOKS:
            copies = random.randint(2, 5)
            ref = db.collection('books').document()
            books.append({
                'ref': ref, 'title': title, 'author': author, 'category': category,
                'isbn': isbn, 'copies_total': copies,
            })
        return books

    def _generate_loans(self, books, students):
        """Genera el historial en memoria respetando stock y límite por estudiante."""
        now = timezone.now()
        # Libros populares: algunos pesan más para que el "top" sea interesante
        weights = [random.choice([1, 1, 2, 3, 6]) for _ in books]
        loans = []
        active_by_book, active_by_student = Counter(), Counter()

        for _ in range(LOANS_TO_CREATE):
            book = random.choices(books, weights)[0]
            student = random.choice(students)
            age_days = random.randint(0, MONTHS_BACK * 30)
            loaned_at = now - timedelta(days=age_days, hours=random.randint(0, 10))
            due_at = loaned_at + timedelta(days=settings.LOAN_DAYS)

            roll = random.random()
            if age_days < settings.LOAN_DAYS + 7:
                status = 'active' if roll < 0.6 else 'returned'
            else:
                status = 'returned' if roll < 0.85 else ('cancelled' if roll < 0.95 else 'active')

            if status == 'active' and (
                active_by_book[book['ref'].id] >= book['copies_total']
                or active_by_student[student['uid']] >= settings.MAX_ACTIVE_LOANS
            ):
                status = 'returned'

            returned_at = cancelled_at = None
            if status == 'active':
                active_by_book[book['ref'].id] += 1
                active_by_student[student['uid']] += 1
            elif status == 'returned':
                returned_at = min(loaned_at + timedelta(days=random.randint(1, settings.LOAN_DAYS + 6)), now)
            else:
                cancelled_at = min(loaned_at + timedelta(hours=random.randint(1, 36)), now)

            loans.append({
                'book_id': book['ref'].id, 'book_title': book['title'], 'book_category': book['category'],
                'user_id': student['uid'], 'user_name': student['name'], 'user_email': student['email'],
                'status': status, 'loaned_at': loaned_at, 'due_at': due_at,
                'returned_at': returned_at, 'cancelled_at': cancelled_at,
            })

        for book in books:
            book['copies_available'] = book['copies_total'] - active_by_book[book['ref'].id]
        return loans

    def _write(self, db, books, loans):
        batch = db.batch()
        for book in books:
            data = {k: v for k, v in book.items() if k != 'ref'}
            batch.set(book['ref'], data)
        for loan in loans:
            batch.set(db.collection('loans').document(), loan)
        batch.commit()
