"""Conexión única a Firebase (Firestore + Auth) para todo el proyecto."""
import firebase_admin
from django.conf import settings
from firebase_admin import credentials, firestore


def get_db():
    """Devuelve el cliente de Firestore, inicializando Firebase la primera vez."""
    if settings.TESTING:
        raise RuntimeError('Los tests no deben tocar Firestore: usa mock.patch sobre el servicio.')
    try:
        firebase_admin.get_app()
    except ValueError:
        # Variables de entorno si existen; si no, el archivo .json de la llave.
        cred = credentials.Certificate(
            settings.FIREBASE_SERVICE_ACCOUNT or str(settings.FIREBASE_CREDENTIALS_PATH)
        )
        firebase_admin.initialize_app(cred)
    return firestore.client()
