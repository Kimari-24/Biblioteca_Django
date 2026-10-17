"""Préstamos: prestar, devolver y cancelar (colección `loans` en Firestore).

Cada operación corre dentro de una transacción de Firestore: así dos personas
no pueden llevarse la última copia al mismo tiempo y el stock nunca queda mal.
Las reglas de negocio viven en `rules.py`.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from core.firebase import get_db
from features.books.services import books_collection

from . import rules
from .rules import ACTIVE, CANCELLED, RETURNED, LoanError


def _loans():
    return get_db().collection('loans')


def _decorate(doc):
    loan = {'id': doc.id, **doc.to_dict()}
    loan['overdue'] = rules.is_overdue(loan, timezone.now())
    return loan


def list_loans(user_id=None, status=''):
    """Préstamos más recientes primero; opcionalmente de un usuario y/o estado."""
    query = _loans()
    if user_id:
        query = query.where(filter=FieldFilter('user_id', '==', user_id))
    loans = [_decorate(d) for d in query.stream()]
    if status == 'overdue':
        loans = [loan for loan in loans if loan['overdue']]
    elif status:
        loans = [loan for loan in loans if loan['status'] == status]
    return sorted(loans, key=lambda loan: loan['loaned_at'], reverse=True)


def borrow(book_id, user):
    """Presta un libro a `user` (dict de sesión). Valida stock y límites."""
    db = get_db()
    book_ref = books_collection().document(book_id)
    loan_ref = _loans().document()
    user_active = _loans().where(filter=FieldFilter('user_id', '==', user['uid'])).where(
        filter=FieldFilter('status', '==', ACTIVE)
    )

    @firestore.transactional
    def run(transaction):
        snapshot = book_ref.get(transaction=transaction)
        book = snapshot.to_dict() if snapshot.exists else None
        active = [d.to_dict() for d in user_active.stream(transaction=transaction)]
        rules.check_can_borrow(book, book_id, active)

        now = timezone.now()
        transaction.update(book_ref, {'copies_available': firestore.Increment(-1)})
        transaction.set(loan_ref, {
            'book_id': book_id, 'book_title': book['title'], 'book_category': book['category'],
            'user_id': user['uid'], 'user_name': user['name'], 'user_email': user['email'],
            'status': ACTIVE, 'loaned_at': now,
            'due_at': now + timedelta(days=settings.LOAN_DAYS),
            'returned_at': None, 'cancelled_at': None,
        })

    run(db.transaction())
    return loan_ref.id


def _close(loan_id, user, new_status, date_field):
    """Cierra un préstamo activo (devolver o cancelar) y repone la copia."""
    db = get_db()
    loan_ref = _loans().document(loan_id)

    @firestore.transactional
    def run(transaction):
        snapshot = loan_ref.get(transaction=transaction)
        loan = snapshot.to_dict() if snapshot.exists else None
        rules.check_can_close(loan, user)
        book_ref = books_collection().document(loan['book_id'])
        book_exists = book_ref.get(transaction=transaction).exists

        transaction.update(loan_ref, {'status': new_status, date_field: timezone.now()})
        if book_exists:
            transaction.update(book_ref, {'copies_available': firestore.Increment(1)})

    run(db.transaction())


def return_loan(loan_id, user):
    _close(loan_id, user, RETURNED, 'returned_at')


def cancel_loan(loan_id, user):
    _close(loan_id, user, CANCELLED, 'cancelled_at')
