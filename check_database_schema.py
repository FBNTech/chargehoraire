import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Vérifier TOUS les triggers dans la base de données
print("=== TOUS LES TRIGGERS DANS LA BASE DE DONNÉES ===")
cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY tbl_name, name")
all_triggers = cursor.fetchall()

if all_triggers:
    for name, tbl_name, sql in all_triggers:
        print(f"\nTable: {tbl_name}")
        print(f"Trigger: {name}")
        print(f"SQL: {sql}")
        print("-" * 80)
else:
    print("Aucun trigger trouvé dans la base de données")

# Vérifier toutes les tables contenant "backup"
print("\n\n=== TABLES CONTENANT 'backup' ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%backup%'")
backup_tables = cursor.fetchall()

if backup_tables:
    for (table_name,) in backup_tables:
        print(f"- {table_name}")
else:
    print("Aucune table de backup trouvée")

# Vérifier le schéma de la table courses_course
print("\n\n=== SCHÉMA DE courses_course ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='courses_course'")
schema = cursor.fetchone()
if schema:
    print(schema[0])
else:
    print("Table courses_course non trouvée")

conn.close()
print("\n\nVérification terminée.")
