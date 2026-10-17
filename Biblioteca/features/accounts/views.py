from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import LoginForm, RegisterForm
from .services import AuthError


def login_view(request):
    if request.session.get('user'):
        return redirect('core:home')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            user = services.sign_in(form.cleaned_data['email'], form.cleaned_data['password'])
        except AuthError as exc:
            form.add_error(None, str(exc))
        else:
            request.session.cycle_key()
            request.session['user'] = user
            messages.success(request, f"¡Hola, {user['name']}!")
            next_url = request.GET.get('next', '')
            return redirect(next_url if next_url.startswith('/') else 'core:home')
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.register_student(
                form.cleaned_data['name'], form.cleaned_data['email'], form.cleaned_data['password']
            )
        except AuthError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, 'Cuenta creada. Ya puedes iniciar sesión.')
            return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})


@require_POST
def logout_view(request):
    request.session.flush()
    return redirect('accounts:login')
