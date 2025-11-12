import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Rechercher TOUS les triggers qui mentionnent "backup"
print("=== TOUS LES TRIGGERS MENTIONNANT 'backup' ===")
cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' AND sql LIKE '%backup%'")
triggers = cursor.fetchall()

if triggers:
    for name, tbl_name, sql in triggers:
        print(f"\nNom: {name}")
        print(f"Table: {tbl_name}")
        print(f"SQL: {sql}")
        print("-" * 80)
else:
    print("Aucun trigger trouvé mentionnant 'backup'")

# Rechercher tous les triggers sur attribution_attribution
print("\n=== TRIGGERS sur attribution_attribution ===")
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='attribution_attribution'")
attribution_triggers = cursor.fetchall()

if attribution_triggers:
    for name, sql in attribution_triggers:
        print(f"\nNom: {name}")
        print(f"SQL: {sql}")
        print("-" * 80)
else:
    print("Aucun trigger trouvé sur attribution_attribution")

conn.close()
print("\nVérification terminée.")
