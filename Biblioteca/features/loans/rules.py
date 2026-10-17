"""Reglas de negocio de los préstamos como funciones puras (sin Firestore).

Los servicios leen los datos dentro de una transacción y llaman a estas funciones
para decidir si la operación es válida. Así las reglas se pueden probar sin base de datos.
"""
from django.conf import settings

ACTIVE, RETURNED, CANCELLED = 'active', 'returned', 'cancelled'


class LoanError(Exception):
    """Regla de negocio incumplida; el mensaje se muestra al usuario."""


def check_can_borrow(book, book_id, active_loans):
    """`book`: dict del libro (o None). `active_loans`: préstamos activos del estudiante."""
    if book is None:
        raise LoanError('El libro no existe.')
    if book['copies_available'] < 1:
        raise LoanError('No hay copias disponibles de este libro.')
    if len(active_loans) >= settings.MAX_ACTIVE_LOANS:
        raise LoanError(f'Ya tienes {settings.MAX_ACTIVE_LOANS} préstamos activos.')
    if any(loan['book_id'] == book_id for loan in active_loans):
        raise LoanError('Ya tienes un préstamo activo de este libro.')


def check_can_close(loan, user):
    """Devolver o cancelar: solo el dueño o un bibliotecario, y solo si sigue activo."""
    if loan is None:
        raise LoanError('El préstamo no existe.')
    if user['role'] != 'librarian' and loan['user_id'] != user['uid']:
        raise LoanError('Ese préstamo no es tuyo.')
    if loan['status'] != ACTIVE:
        raise LoanError('Ese préstamo ya no está activo.')


def is_overdue(loan, now):
    return loan['status'] == ACTIVE and loan['due_at'] < now
