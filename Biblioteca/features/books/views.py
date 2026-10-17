from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.decorators import librarian_required, login_required
from core.pagination import paginate

from . import services
from .forms import BookForm
from .services import BookError


@login_required
def book_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    books = services.list_books(query, category)
    return render(request, 'books/list.html', {
        **paginate(request, books),
        'categories': services.list_categories(),
        'q': query,
        'category': category,
    })


@librarian_required
def book_create(request):
    form = BookForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        services.create_book(d['title'], d['author'], d['category'], d['isbn'], d['copies'])
        messages.success(request, 'Libro creado.')
        return redirect('books:list')
    return render(request, 'books/form.html', {'form': form, 'title': 'Nuevo libro'})


@librarian_required
def book_edit(request, book_id):
    book = services.get_book(book_id)
    if book is None:
        messages.error(request, 'El libro no existe.')
        return redirect('books:list')
    form = BookForm(request.POST or None, initial={
        'title': book['title'], 'author': book['author'], 'category': book['category'],
        'isbn': book['isbn'], 'copies': book['copies_total'],
    })
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            services.update_book(book_id, d['title'], d['author'], d['category'], d['isbn'], d['copies'])
        except BookError as exc:
            form.add_error('copies', str(exc))
        else:
            messages.success(request, 'Libro actualizado.')
            return redirect('books:list')
    return render(request, 'books/form.html', {'form': form, 'title': 'Editar libro'})


@librarian_required
@require_POST
def book_delete(request, book_id):
    try:
        services.delete_book(book_id)
        messages.success(request, 'Libro eliminado.')
    except BookError as exc:
        messages.error(request, str(exc))
    return redirect('books:list')
