from sqlalchemy import create_engine
import pandas as pd

# Connexion à la base de données PostgreSQL via SQLAlchemy
try:
    # Remplacez par vos informations de connexion
    engine = create_engine("postgresql+psycopg2://postgres:admin@localhost:15435/mart_db")
    print("Connexion réussie à la base de données")
except Exception as e:
    print(f"Erreur lors de la connexion : {e}")
    exit(1)

# Charger les données depuis la table `rides`
try:
    query = "SELECT * FROM rides LIMIT 100"

    # Connexion et récupération des résultats
    with engine.connect() as connection:
        result = connection.execute(query)
        rides_data = pd.DataFrame(result.fetchall(), columns=result.keys())  # Convertir en DataFrame

    # Afficher les 5 premières lignes
    print(rides_data.head())
except Exception as e:
    print(f"Une erreur est survenue lors de l'exécution de la requête : {e}")
