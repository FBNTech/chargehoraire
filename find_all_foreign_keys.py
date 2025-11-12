import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=== TOUTES LES CLÉS ÉTRANGÈRES VERS courses_course ===\n")

# Obtenir toutes les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [row[0] for row in cursor.fetchall()]

found_any = False
for table in tables:
    cursor.execute(f"PRAGMA foreign_key_list('{table}')")
    fks = cursor.fetchall()
    
    for fk in fks:
        # fk = (id, seq, table_ref, from, to, on_update, on_delete, match)
        table_ref = fk[2]
        col_from = fk[3]
        col_to = fk[4]
        
        if 'courses_course' in table_ref:
            found_any = True
            print(f"Table: {table}")
            print(f"  Colonne locale: {col_from}")
            print(f"  Table référencée: {table_ref}")
            print(f"  Colonne distante: {col_to}")
            print(f"  Contrainte complète: {fk}")
            print("-" * 80)

if not found_any:
    print("Aucune clé étrangère trouvée vers courses_course (ou courses_course_backup)")

conn.close()
