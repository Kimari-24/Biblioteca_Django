def session_user(request):
    """Pone `current_user` disponible en todos los templates."""
    return {'current_user': request.session.get('user')}
