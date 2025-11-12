import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=== TOUS LES TRIGGERS DE LA BASE ===\n")
cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY tbl_name")
triggers = cursor.fetchall()

if triggers:
    for name, tbl_name, sql in triggers:
        print(f"Table: {tbl_name}")
        print(f"Trigger: {name}")
        print(f"SQL:\n{sql}\n")
        print("-" * 80)
else:
    print("Aucun trigger")

conn.close()
