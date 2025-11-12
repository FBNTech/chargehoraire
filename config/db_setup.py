"""
Configuration pour activer les contraintes de clés étrangères SQLite
"""
from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def activate_foreign_keys(sender, connection, **kwargs):
    """Active les contraintes de clés étrangères pour SQLite"""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
        cursor.close()
