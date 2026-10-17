from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.decorators import librarian_required, login_required, student_required
from core.pagination import paginate

from . import services
from .rules import LoanError


@student_required
@require_POST
def borrow(request, book_id):
    try:
        services.borrow(book_id, request.session['user'])
        messages.success(request, 'Préstamo registrado. ¡Disfruta la lectura!')
    except LoanError as exc:
        messages.error(request, str(exc))
    return redirect('loans:mine')


@login_required
@require_POST
def return_loan(request, loan_id):
    return _close(request, loan_id, services.return_loan, 'Libro devuelto.')


@login_required
@require_POST
def cancel_loan(request, loan_id):
    return _close(request, loan_id, services.cancel_loan, 'Préstamo cancelado.')


def _close(request, loan_id, action, success_message):
    try:
        action(loan_id, request.session['user'])
        messages.success(request, success_message)
    except LoanError as exc:
        messages.error(request, str(exc))
    next_url = request.POST.get('next', '')
    return redirect(next_url if next_url.startswith('/') else 'core:home')


@student_required
def my_loans(request):
    loans = services.list_loans(user_id=request.session['user']['uid'])
    return render(request, 'loans/mine.html', paginate(request, loans))


@librarian_required
def all_loans(request):
    status = request.GET.get('status', '')
    loans = services.list_loans(status=status)
    return render(request, 'loans/all.html', {**paginate(request, loans), 'status': status})
