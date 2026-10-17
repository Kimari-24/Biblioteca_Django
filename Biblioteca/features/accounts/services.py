"""Usuarios: autenticación con Firebase Auth y perfil/rol en Firestore."""
import requests
from django.conf import settings
from firebase_admin import auth, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from core.firebase import get_db

SIGN_IN_URL = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword'

# Mensajes de error de la REST API de Firebase traducidos
AUTH_ERRORS = {
    'INVALID_LOGIN_CREDENTIALS': 'Correo o contraseña incorrectos.',
    'INVALID_PASSWORD': 'Correo o contraseña incorrectos.',
    'EMAIL_NOT_FOUND': 'Correo o contraseña incorrectos.',
    'USER_DISABLED': 'Esta cuenta está deshabilitada.',
    'TOO_MANY_ATTEMPTS_TRY_LATER': 'Demasiados intentos. Intenta más tarde.',
}


class AuthError(Exception):
    """Error de autenticación con un mensaje listo para mostrar al usuario."""


def sign_in(email, password):
    """Valida correo y contraseña contra Firebase Auth y devuelve los datos de sesión.

    La contraseña solo se puede verificar con la REST API (el Admin SDK no puede),
    por eso usamos `requests` aquí.
    """
    response = requests.post(
        SIGN_IN_URL,
        params={'key': settings.FIREBASE_WEB_API_KEY},
        json={'email': email, 'password': password, 'returnSecureToken': True},
        timeout=10,
    )
    if response.status_code != 200:
        code = response.json().get('error', {}).get('message', '')
        raise AuthError(AUTH_ERRORS.get(code.split(' ')[0], 'No se pudo iniciar sesión.'))

    # Verificamos el token con el Admin SDK en lugar de confiar a ciegas en la respuesta.
    get_db()
    decoded = auth.verify_id_token(response.json()['idToken'], clock_skew_seconds=10)
    return get_session_user(decoded['uid'], email, decoded.get('name', ''))


def get_session_user(uid, email, name=''):
    """Lee el rol del usuario en Firestore (lo crea como estudiante si no existe)."""
    ref = get_db().collection('users').document(uid)
    snapshot = ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
    else:
        data = {'email': email, 'name': name or email.split('@')[0], 'role': 'student'}
        ref.set({**data, 'created_at': firestore.SERVER_TIMESTAMP})
    return {'uid': uid, 'email': data['email'], 'name': data['name'], 'role': data['role']}


def create_user(name, email, password, role):
    """Crea la cuenta en Firebase Auth y su perfil (con el rol) en Firestore."""
    get_db()
    try:
        user = auth.create_user(email=email, password=password, display_name=name)
    except auth.EmailAlreadyExistsError:
        raise AuthError('Ya existe una cuenta con ese correo.')
    except ValueError as exc:
        raise AuthError(str(exc))
    get_db().collection('users').document(user.uid).set(
        {'email': email, 'name': name, 'role': role, 'created_at': firestore.SERVER_TIMESTAMP}
    )
    return user.uid


def register_student(name, email, password):
    """Registro público: siempre crea un estudiante."""
    return create_user(name, email, password, role='student')


def list_students():
    """Perfiles con rol estudiante: [{'uid', 'email', 'name', ...}]."""
    docs = get_db().collection('users').where(filter=FieldFilter('role', '==', 'student')).stream()
    return [{'uid': d.id, **d.to_dict()} for d in docs]
