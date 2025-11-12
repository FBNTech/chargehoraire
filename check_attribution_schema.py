import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=== SCHÉMA DE attribution_attribution ===\n")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='attribution_attribution'")
schema = cursor.fetchone()
if schema:
    print(schema[0])
else:
    print("Table non trouvée")

print("\n\n=== TRIGGERS SUR attribution_attribution ===\n")
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='attribution_attribution'")
triggers = cursor.fetchall()
if triggers:
    for name, sql in triggers:
        print(f"Trigger: {name}")
        print(f"SQL: {sql}")
        print("-" * 80)
else:
    print("Aucun trigger")

print("\n\n=== INDEX SUR attribution_attribution ===\n")
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='attribution_attribution'")
indexes = cursor.fetchall()
if indexes:
    for name, sql in indexes:
        print(f"Index: {name}")
        print(f"SQL: {sql}")
        print("-" * 80)
else:
    print("Aucun index")

print("\n\n=== VÉRIFICATION DES CLÉS ÉTRANGÈRES ===\n")
cursor.execute("PRAGMA foreign_key_list('attribution_attribution')")
fks = cursor.fetchall()
if fks:
    for fk in fks:
        print(f"Table référencée: {fk[2]}, Colonne locale: {fk[3]}, Colonne distante: {fk[4]}")
else:
    print("Aucune clé étrangère")

conn.close()
