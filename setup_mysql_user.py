import pymysql

conn = pymysql.connect(host='localhost', user='root', password='')
cursor = conn.cursor()

# Créer la base de données si elle n'existe pas
cursor.execute('CREATE DATABASE IF NOT EXISTS chargehoraire CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')

# Créer l'utilisateur django_user
cursor.execute("CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'fbn';")

# Donner tous les privilèges sur la base de données
cursor.execute("GRANT ALL PRIVILEGES ON chargehoraire.* TO 'django_user'@'localhost';")

# Appliquer les changements
cursor.execute('FLUSH PRIVILEGES;')

conn.commit()
print('✅ Utilisateur django_user créé avec succès!')
print('   - Nom d\'utilisateur: django_user')
print('   - Mot de passe: fbn')
print('   - Base de données: chargehoraire')
print('   - Privilèges: ALL sur chargehoraire.*')
conn.close()
