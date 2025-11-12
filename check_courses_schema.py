import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=== SCHÉMA DE courses_course ===\n")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='courses_course'")
schema = cursor.fetchone()
if schema:
    print(schema[0])
else:
    print("Table non trouvée")

print("\n\n=== INDEX SUR courses_course ===\n")
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='courses_course'")
indexes = cursor.fetchall()
if indexes:
    for name, sql in indexes:
        print(f"Index: {name}")
        print(f"SQL: {sql if sql else '(auto-créé par SQLite)'}")
        print("-" * 80)
else:
    print("Aucun index")

print("\n\n=== VÉRIFICATION DE LA CLÉ PRIMAIRE ===\n")
cursor.execute("PRAGMA table_info('courses_course')")
for col in cursor.fetchall():
    col_id, name, type_, notnull, default, pk = col
    if pk:
        print(f"Clé primaire: {name} ({type_})")

conn.close()
