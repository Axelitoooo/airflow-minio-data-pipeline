import pandas as pd

# Configuration de storage_options avec les informations de connexion
s3_options = {
    "key": "minio",
    "secret": "minio123",
    "client_kwargs": {
        "endpoint_url": "http://127.0.0.1:9000"
    }
}

# Chemin du fichier Parquet dans le bucket MinIO
file_path = "s3://yellow-taxi-data/yellow_tripdata_2024-01.parquet"

# Lire le fichier Parquet avec Pandas en utilisant les options de stockage
try:
    s3FileInput1 = pd.read_parquet(file_path, storage_options=s3_options)
    print(s3FileInput1.head())
except Exception as e:
    print("Erreur lors de la lecture du fichier Parquet :", e)
