import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Rechercher tous les triggers liés à la table courses_course
print("=== TRIGGERS sur courses_course ===")
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='courses_course'")
triggers = cursor.fetchall()

if triggers:
    for name, sql in triggers:
        print(f"\nNom: {name}")
        print(f"SQL: {sql}")
        print("-" * 80)
else:
    print("Aucun trigger trouvé sur courses_course")

# Vérifier si la table backup existe
print("\n=== VÉRIFICATION DE LA TABLE BACKUP ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses_course_backup'")
backup_table = cursor.fetchone()

if backup_table:
    print("La table courses_course_backup existe")
else:
    print("La table courses_course_backup N'EXISTE PAS (source du problème)")

conn.close()
print("\nVérification terminée.")
