from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse

LIBRARIAN = 'librarian'
STUDENT = 'student'


def login_required(view):
    """Exige que haya un usuario en la sesión."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user'):
            return redirect_to_login(request.get_full_path(), reverse('accounts:login'))
        return view(request, *args, **kwargs)
    return wrapper


def role_required(role):
    """Exige estar logueado y tener el rol indicado."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.session['user']['role'] != role:
                messages.error(request, 'No tienes permiso para ver esa página.')
                return redirect('books:list')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


librarian_required = role_required(LIBRARIAN)
student_required = role_required(STUDENT)
