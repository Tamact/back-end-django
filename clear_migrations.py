import psycopg2

# Connexion à la base de données
conn = psycopg2.connect(
    dbname="rhh",
    user="postgres",
    password="azerty12",
    host="localhost",
    port="5432"
)

# Créer un curseur
cur = conn.cursor()

# Supprimer les enregistrements de migration pour l'application recruitment
cur.execute("DELETE FROM django_migrations WHERE app = 'recruitment';")

# Valider les changements
conn.commit()

# Fermer la connexion
cur.close()
conn.close()
