"""
Script pour corriger TOUTES les clés étrangères incorrectes
"""
import sqlite3
import shutil
from datetime import datetime

# Sauvegarde
backup_file = f'db.sqlite3.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f"=== CORRECTION COMPLÈTE DES CLÉS ÉTRANGÈRES ===\n")
print(f"1. Sauvegarde: {backup_file}")
shutil.copy2('db.sqlite3', backup_file)

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys=OFF")

# ===== 1. TRACKING_PROGRESSSTATS =====
print("\n2. Correction de tracking_progressstats...")
cursor.execute("SELECT * FROM tracking_progressstats")
columns = [d[0] for d in cursor.description]
data = cursor.fetchall()
print(f"   {len(data)} enregistrements trouvés")

cursor.execute("DROP TABLE IF EXISTS tracking_progressstats_old")
cursor.execute("ALTER TABLE tracking_progressstats RENAME TO tracking_progressstats_old")

cursor.execute("""
CREATE TABLE "tracking_progressstats" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "total_assigned" integer NOT NULL,
    "total_scheduled" integer NOT NULL,
    "completion_rate" real NOT NULL,
    "last_updated" datetime NOT NULL,
    "course_id" integer NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED,
    "teacher_id" integer NULL REFERENCES "teachers_teacher" ("id") DEFERRABLE INITIALLY DEFERRED
)
""")

if data:
    placeholders = ','.join(['?' for _ in columns])
    cursor.executemany(f"INSERT INTO tracking_progressstats ({','.join(columns)}) VALUES ({placeholders})", data)
    print(f"   {len(data)} enregistrements réinsérés")

cursor.execute("DROP TABLE tracking_progressstats_old")

# ===== 2. TRACKING_TEACHINGPROGRESS =====
print("\n3. Correction de tracking_teachingprogress...")
cursor.execute("SELECT * FROM tracking_teachingprogress")
columns = [d[0] for d in cursor.description]
data = cursor.fetchall()
print(f"   {len(data)} enregistrements trouvés")

cursor.execute("DROP TABLE IF EXISTS tracking_teachingprogress_old")
cursor.execute("ALTER TABLE tracking_teachingprogress RENAME TO tracking_teachingprogress_old")

cursor.execute("""
CREATE TABLE "tracking_teachingprogress" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "total_hours_assigned" real NOT NULL,
    "total_hours_scheduled" real NOT NULL,
    "progress_percentage" real NOT NULL,
    "last_updated" datetime NOT NULL,
    "course_id" integer NULL REFERENCES "courses_course" ("id") DEFERRABLE INITIALLY DEFERRED,
    "teacher_id" integer NULL REFERENCES "teachers_teacher" ("id") DEFERRABLE INITIALLY DEFERRED
)
""")

if data:
    placeholders = ','.join(['?' for _ in columns])
    cursor.executemany(f"INSERT INTO tracking_teachingprogress ({','.join(columns)}) VALUES ({placeholders})", data)
    print(f"   {len(data)} enregistrements réinsérés")

cursor.execute("DROP TABLE tracking_teachingprogress_old")

# Réactiver les clés étrangères
cursor.execute("PRAGMA foreign_keys=ON")

# Vérification
print("\n4. Vérification finale...")
cursor.execute("PRAGMA integrity_check")
result = cursor.fetchone()[0]
print(f"   Intégrité: {result}")

print("\n5. Vérification des clés étrangères corrigées:")
for table in ['tracking_progressstats', 'tracking_teachingprogress', 'attribution_attribution']:
    cursor.execute(f"PRAGMA foreign_key_list('{table}')")
    fks = cursor.fetchall()
    for fk in fks:
        if 'course' in fk[2].lower():
            print(f"   {table}.{fk[3]} -> {fk[2]}.{fk[4]}")

conn.commit()
conn.close()

print("\n=== CORRECTION TERMINÉE ===")
print(f"\nToutes les clés étrangères pointent maintenant vers 'courses_course'")
print(f"Sauvegarde: {backup_file}")
print("\nRedémarrez le serveur Django pour appliquer les changements.")
