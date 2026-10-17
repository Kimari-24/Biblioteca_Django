"""Catálogo de libros (colección `books` en Firestore)."""
from core.firebase import get_db


class BookError(Exception):
    """Regla de negocio incumplida al modificar un libro."""


def books_collection():
    return get_db().collection('books')


def list_books(query='', category=''):
    """Lista libros ordenados por título; filtra por texto y categoría en Python."""
    books = [{'id': d.id, **d.to_dict()} for d in books_collection().stream()]
    query = query.strip().lower()
    if query:
        books = [b for b in books if query in b['title'].lower() or query in b['author'].lower()]
    if category:
        books = [b for b in books if b['category'] == category]
    return sorted(books, key=lambda b: b['title'].lower())


def list_categories():
    return sorted({d.to_dict()['category'] for d in books_collection().stream()})


def get_book(book_id):
    snapshot = books_collection().document(book_id).get()
    return {'id': snapshot.id, **snapshot.to_dict()} if snapshot.exists else None


def create_book(title, author, category, isbn, copies):
    ref = books_collection().document()
    ref.set({
        'title': title, 'author': author, 'category': category, 'isbn': isbn,
        'copies_total': copies, 'copies_available': copies,
    })
    return ref.id


def update_book(book_id, title, author, category, isbn, copies):
    """Edita un libro; ajusta las copias disponibles según el nuevo total."""
    book = get_book(book_id)
    if book is None:
        raise BookError('El libro no existe.')
    on_loan = book['copies_total'] - book['copies_available']
    if copies < on_loan:
        raise BookError(f'No puedes bajar a {copies} copias: hay {on_loan} prestadas.')
    books_collection().document(book_id).update({
        'title': title, 'author': author, 'category': category, 'isbn': isbn,
        'copies_total': copies, 'copies_available': copies - on_loan,
    })


def delete_book(book_id):
    """Elimina un libro. Si hay copias prestadas (disponibles < totales) no se puede."""
    book = get_book(book_id)
    if book is None:
        raise BookError('El libro no existe.')
    if book['copies_available'] < book['copies_total']:
        raise BookError('No se puede eliminar: tiene préstamos activos.')
    books_collection().document(book_id).delete()
