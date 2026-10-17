from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from core.testing import STUDENT, SessionTestCase

from . import services
from .forms import RegisterForm
from .services import AuthError


class SignInTests(SimpleTestCase):
    def test_firebase_error_is_translated(self):
        response = mock.Mock(status_code=400)
        response.json.return_value = {'error': {'message': 'INVALID_LOGIN_CREDENTIALS'}}
        with mock.patch('features.accounts.services.requests.post', return_value=response):
            with self.assertRaisesMessage(AuthError, 'Correo o contraseña incorrectos.'):
                services.sign_in('a@b.com', 'mala')

    def test_unknown_firebase_error_gets_generic_message(self):
        response = mock.Mock(status_code=400)
        response.json.return_value = {'error': {'message': 'ALGO_RARO'}}
        with mock.patch('features.accounts.services.requests.post', return_value=response):
            with self.assertRaisesMessage(AuthError, 'No se pudo iniciar sesión.'):
                services.sign_in('a@b.com', 'x')


class RegisterFormTests(SimpleTestCase):
    def test_passwords_must_match(self):
        form = RegisterForm({'name': 'Ana', 'email': 'a@b.com', 'password': 'abcdef', 'password2': 'abcdeX'})
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_password_min_length(self):
        form = RegisterForm({'name': 'Ana', 'email': 'a@b.com', 'password': '123', 'password2': '123'})
        self.assertFalse(form.is_valid())


class LoginViewTests(SessionTestCase):
    def test_successful_login_stores_user_in_session(self):
        with mock.patch('features.accounts.services.sign_in', return_value=STUDENT):
            response = self.client.post('/login/', {'email': 'est@example.com', 'password': 'clave-de-prueba'})
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(self.client.session['user'], STUDENT)

    def test_failed_login_shows_error_and_no_session(self):
        with mock.patch('features.accounts.services.sign_in', side_effect=AuthError('Correo o contraseña incorrectos.')):
            response = self.client.post('/login/', {'email': 'est@example.com', 'password': 'x'})
        self.assertContains(response, 'Correo o contraseña incorrectos.')
        self.assertNotIn('user', self.client.session)

    def test_next_must_be_a_local_path(self):
        with mock.patch('features.accounts.services.sign_in', return_value=STUDENT):
            response = self.client.post('/login/?next=https://evil.example/', {'email': 'a@b.com', 'password': 'x'})
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_logout_clears_session_and_requires_post(self):
        self.login_as(STUDENT)
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.client.post('/logout/')
        self.assertNotIn('user', self.client.session)


class CreateUserTests(SimpleTestCase):
    def test_register_student_always_uses_student_role(self):
        with mock.patch.object(services, 'create_user') as create:
            services.register_student('Ana', 'ana@example.com', 'abcdef')
        create.assert_called_once_with('Ana', 'ana@example.com', 'abcdef', role='student')

    def test_command_asks_password_and_creates_user(self):
        with mock.patch('features.accounts.management.commands.create_user.getpass', return_value='secreto1'), \
                mock.patch.object(services, 'create_user') as create:
            call_command('create_user', 'bib@example.com', 'Bibliotecaria', '--role', 'librarian', stdout=StringIO())
        create.assert_called_once_with('Bibliotecaria', 'bib@example.com', 'secreto1', 'librarian')

    def test_command_rejects_different_passwords(self):
        with mock.patch('features.accounts.management.commands.create_user.getpass', side_effect=['uno12345', 'dos12345']), \
                mock.patch.object(services, 'create_user') as create:
            with self.assertRaisesMessage(CommandError, 'no coinciden'):
                call_command('create_user', 'bib@example.com', 'Bibliotecaria')
        create.assert_not_called()
