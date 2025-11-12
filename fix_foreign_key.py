"""
Script pour corriger la clé étrangère incorrecte dans attribution_attribution
"""
import sqlite3
import os
import shutil
from datetime import datetime

# Sauvegarder la base de données
backup_file = f'db.sqlite3.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f"=== CORRECTION DE LA CLÉ ÉTRANGÈRE ===\n")
print(f"1. Sauvegarde de la base dans: {backup_file}")
shutil.copy2('db.sqlite3', backup_file)

# Connexion
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Désactiver les clés étrangères temporairement
cursor.execute("PRAGMA foreign_keys=OFF")

print("\n2. Récupération des données existantes...")
# Récupérer toutes les données de attribution_attribution
cursor.execute("SELECT * FROM attribution_attribution")
columns = [description[0] for description in cursor.description]
data = cursor.fetchall()
print(f"   {len(data)} attributions trouvées")

print("\n3. Suppression de l'ancienne table...")
cursor.execute("DROP TABLE IF EXISTS attribution_attribution_old")
cursor.execute("ALTER TABLE attribution_attribution RENAME TO attribution_attribution_old")

print("\n4. Création de la nouvelle table avec la bonne référence...")
create_table_sql = """
CREATE TABLE "attribution_attribution" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "annee_academique" varchar(9) NULL,
    "type_charge" varchar(15) NULL,
    "date_creation" datetime NOT NULL,
    "date_modification" datetime NOT NULL,
    "code_ue_id" integer NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED,
    "matricule_id" varchar(20) NULL REFERENCES "teachers_teacher" ("matricule") DEFERRABLE INITIALLY DEFERRED
)
"""
cursor.execute(create_table_sql)

print("\n5. Recréation des index...")
# Supprimer les anciens index s'ils existent
cursor.execute("DROP INDEX IF EXISTS attribution_attribution_matricule_id_code_ue_id_annee_academique_b113ac22_uniq")
cursor.execute("DROP INDEX IF EXISTS attribution_attribution_code_ue_id_f34854b1")
cursor.execute("DROP INDEX IF EXISTS attribution_attribution_matricule_id_9ee0feac")

# Index unique pour la contrainte unique_together
cursor.execute("""
CREATE UNIQUE INDEX "attribution_attribution_matricule_id_code_ue_id_annee_academique_b113ac22_uniq"
ON "attribution_attribution" ("matricule_id", "code_ue_id", "annee_academique")
""")

# Index sur code_ue_id
cursor.execute("""
CREATE INDEX "attribution_attribution_code_ue_id_f34854b1"
ON "attribution_attribution" ("code_ue_id")
""")

# Index sur matricule_id
cursor.execute("""
CREATE INDEX "attribution_attribution_matricule_id_9ee0feac"
ON "attribution_attribution" ("matricule_id")
""")

print("\n6. Réinsertion des données...")
if data:
    placeholders = ','.join(['?' for _ in columns])
    insert_sql = f"INSERT INTO attribution_attribution ({','.join(columns)}) VALUES ({placeholders})"
    cursor.executemany(insert_sql, data)
    print(f"   {len(data)} attributions réinsérées")

print("\n7. Suppression de l'ancienne table...")
cursor.execute("DROP TABLE attribution_attribution_old")

# Réactiver les clés étrangères
cursor.execute("PRAGMA foreign_keys=ON")

# Vérifier l'intégrité
print("\n8. Vérification de l'intégrité...")
cursor.execute("PRAGMA integrity_check")
result = cursor.fetchone()[0]
print(f"   Intégrité: {result}")

# Vérifier la nouvelle structure
print("\n9. Vérification de la nouvelle structure...")
cursor.execute("PRAGMA foreign_key_list('attribution_attribution')")
fks = cursor.fetchall()
for fk in fks:
    print(f"   FK: {fk[3]} -> {fk[2]}.{fk[4]}")

# Commit et fermeture
conn.commit()
conn.close()

print("\n=== CORRECTION TERMINÉE ===")
print(f"\nLa clé étrangère pointe maintenant vers 'courses_course' au lieu de 'courses_course_backup'")
print(f"\nSauvegarde disponible dans: {backup_file}")
print("\nVous pouvez maintenant redémarrer le serveur Django.")
