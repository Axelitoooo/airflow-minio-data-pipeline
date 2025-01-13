import pandas as pd

# Configuration des options pour accéder à MinIO en tant que S3
s3_options = {
    "key": "minio",           # Access Key
    "secret": "minio123",      # Secret Key
    "client_kwargs": {
        "endpoint_url": "http://127.0.0.1:9000"  # URL du service MinIO
    }
}

# Chemin du fichier Parquet dans MinIO
file_path = "s3://yellow-taxi-data/yellow_tripdata_2024-01.parquet"

# Lire le fichier Parquet avec Pandas
df = pd.read_parquet(file_path, storage_options=s3_options)
print(df.head())
