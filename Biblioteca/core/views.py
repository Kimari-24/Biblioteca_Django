from django.shortcuts import redirect


def home(request):
    """Cada rol aterriza en su página principal."""
    user = request.session.get('user')
    if user and user['role'] == 'librarian':
        return redirect('dashboard:index')
    return redirect('books:list')
