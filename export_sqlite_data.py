#!/usr/bin/env python
"""
Script pour exporter les données de SQLite vers MySQL
"""
import os
import sqlite3
import pymysql
from django.conf import settings
import django

# Initialiser Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def export_sqlite_to_mysql():
    # Connexion à SQLite
    sqlite_conn = sqlite3.connect('db.sqlite3')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connexion à MySQL
    mysql_conn = pymysql.connect(
        host=settings.DATABASES['default']['HOST'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
        charset='utf8mb4'
    )
    mysql_cursor = mysql_conn.cursor()
    
    # Obtenir toutes les tables de SQLite
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = sqlite_cursor.fetchall()
    
    print(f"Tables trouvées: {[table[0] for table in tables]}")
    
    for table_name, in tables:
        if table_name == 'sqlite_sequence':
            continue
            
        print(f"\nExportation de la table: {table_name}")
        
        # Obtenir les données de SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  Pas de données dans {table_name}")
            continue
        
        # Obtenir les noms des colonnes
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = sqlite_cursor.fetchall()
        columns = [col[1] for col in columns_info]
        
        print(f"  Colonnes: {columns}")
        print(f"  Nombre de lignes: {len(rows)}")
        
        # Insérer dans MySQL
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            mysql_cursor.executemany(insert_query, rows)
            mysql_conn.commit()
            print(f"  ✅ {len(rows)} lignes importées avec succès")
        except Exception as e:
            print(f"  ❌ Erreur lors de l'import: {e}")
            mysql_conn.rollback()
    
    # Fermer les connexions
    sqlite_conn.close()
    mysql_conn.close()
    print("\nExportation terminée!")

if __name__ == "__main__":
    export_sqlite_to_mysql()
