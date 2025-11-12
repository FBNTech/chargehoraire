"""
Script pour créer manuellement les tables tracking avec le bon schéma
"""
import sqlite3
from datetime import datetime
import shutil

# Sauvegarde
backup_file = f'db.sqlite3.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f"=== CRÉATION MANUELLE DES TABLES TRACKING ===\n")
print(f"1. Sauvegarde: {backup_file}")
shutil.copy2('db.sqlite3', backup_file)

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys=OFF")

# Supprimer les anciennes tables
print("\n2. Suppression des anciennes tables...")
cursor.execute("DROP TABLE IF EXISTS tracking_teachingprogress")
cursor.execute("DROP TABLE IF EXISTS tracking_progressstats")
cursor.execute("DROP TABLE IF EXISTS tracking_academicweek")

# Créer tracking_academicweek
print("\n3. Création de tracking_academicweek...")
cursor.execute("""
CREATE TABLE "tracking_academicweek" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "codesemaine" varchar(20) NOT NULL,
    "start_date" date NOT NULL,
    "end_date" date NOT NULL,
    "academic_year" varchar(20) NOT NULL,
    "is_active" bool NOT NULL,
    "semestre_id" integer NULL REFERENCES "reglage_semestre" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("codesemaine", "academic_year")
)
""")

cursor.execute("""
CREATE INDEX "tracking_academicweek_semestre_id_5a951f91"
ON "tracking_academicweek" ("semestre_id")
""")

# Créer tracking_progressstats
print("4. Création de tracking_progressstats...")
cursor.execute("""
CREATE TABLE "tracking_progressstats" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "academic_year" varchar(20) NOT NULL,
    "total_hours_done" decimal NOT NULL,
    "last_update" datetime NOT NULL,
    "course_id" integer NOT NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED,
    "teacher_id" integer NOT NULL REFERENCES "teachers_teacher" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("course_id", "teacher_id", "academic_year")
)
""")

cursor.execute("""
CREATE INDEX "tracking_progressstats_course_id_fac34cd9"
ON "tracking_progressstats" ("course_id")
""")

cursor.execute("""
CREATE INDEX "tracking_progressstats_teacher_id_a536cfa1"
ON "tracking_progressstats" ("teacher_id")
""")

# Créer tracking_teachingprogress
print("5. Création de tracking_teachingprogress...")
cursor.execute("""
CREATE TABLE "tracking_teachingprogress" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "hours_done" decimal NOT NULL,
    "comment" text NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "status" varchar(20) NOT NULL,
    "course_id" integer NOT NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED,
    "teacher_id" integer NOT NULL REFERENCES "teachers_teacher" ("id") DEFERRABLE INITIALLY DEFERRED,
    "week_id" integer NOT NULL REFERENCES "reglage_semainecours" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("course_id", "teacher_id", "week_id")
)
""")

cursor.execute("""
CREATE INDEX "tracking_teachingprogress_course_id_a29b8b51"
ON "tracking_teachingprogress" ("course_id")
""")

cursor.execute("""
CREATE INDEX "tracking_teachingprogress_teacher_id_86ec32f1"
ON "tracking_teachingprogress" ("teacher_id")
""")

cursor.execute("""
CREATE INDEX "tracking_teachingprogress_week_id_3ee45a5d"
ON "tracking_teachingprogress" ("week_id")
""")

# Vérification
print("\n6. Vérification des tables créées...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tracking_%' ORDER BY name")
tables = cursor.fetchall()
for (table,) in tables:
    print(f"   ✓ {table}")

# Vérifier les FK
print("\n7. Vérification des clés étrangères...")
for table in ['tracking_progressstats', 'tracking_teachingprogress']:
    cursor.execute(f"PRAGMA foreign_key_list('{table}')")
    fks = cursor.fetchall()
    for fk in fks:
        print(f"   {table}.{fk[3]} -> {fk[2]}.{fk[4]}")

# Réactiver les clés étrangères
cursor.execute("PRAGMA foreign_keys=ON")

# Vérifier l'intégrité
print("\n8. Vérification de l'intégrité...")
cursor.execute("PRAGMA integrity_check")
result = cursor.fetchone()[0]
print(f"   Intégrité: {result}")

conn.commit()
conn.close()

print("\n=== CRÉATION TERMINÉE ===")
print(f"\nSauvegarde: {backup_file}")
print("\nLes tables tracking ont été créées avec le bon schéma.")
print("Redémarrez le serveur Django.")
