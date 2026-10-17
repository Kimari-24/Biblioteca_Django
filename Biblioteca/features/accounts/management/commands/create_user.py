"""Crea un usuario (estudiante o bibliotecario) en Firebase.

Uso:  python manage.py create_user ana@example.com "Ana Torres" --role librarian
La contraseña se pide por teclado: no queda guardada en ningún archivo.
"""
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from features.accounts import services


class Command(BaseCommand):
    help = 'Crea un usuario en Firebase Auth con su rol en Firestore.'

    def add_arguments(self, parser):
        parser.add_argument('email')
        parser.add_argument('name', help='Nombre completo (entre comillas si tiene espacios).')
        parser.add_argument('--role', choices=['student', 'librarian'], default='student')

    def handle(self, *args, **options):
        password = getpass('Contraseña (mínimo 6 caracteres): ')
        if getpass('Repite la contraseña: ') != password:
            raise CommandError('Las contraseñas no coinciden.')
        try:
            services.create_user(options['name'], options['email'], password, options['role'])
        except services.AuthError as exc:
            raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS(f"Usuario {options['email']} creado con rol {options['role']}."))
