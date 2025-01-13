from urllib.request import urlopen, Request
from airflow.utils.dates import days_ago
from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
import os
import tempfile
import ssl
import urllib.error


def download_parquet(**kwargs):
    """Download the most recent available Parquet file from a URL."""
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    filename = "yellow_tripdata"
    extension = ".parquet"
    local_dir = tempfile.gettempdir()  # Use a temporary directory

    # Désactiver la vérification SSL (TEMPORAIRE, à corriger pour la production)
    ssl_context = ssl._create_unverified_context()

    # Rechercher le fichier disponible en remontant les mois
    for offset in range(6):  # Tester jusqu'à 6 mois en arrière
        month = pendulum.now().subtract(months=offset).format('YYYY-MM')
        full_url = f"{base_url}{filename}_{month}{extension}"
        local_file_path = os.path.join(local_dir, f"{filename}_{month}{extension}")

        try:
            print(f"Testing URL: {full_url}")
            req = Request(
                full_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
                }
            )

            # Télécharger le fichier si disponible
            with urlopen(req, context=ssl_context) as response, open(local_file_path, 'wb') as out_file:
                out_file.write(response.read())

            # Pass the local file path to the next task
            kwargs['ti'].xcom_push(key='file_path', value=local_file_path)
            return  # Arrêter la boucle une fois un fichier trouvé
        except urllib.error.HTTPError as e:
            print(f"Failed to access the URL for {month}: {e}")
        except Exception as e:
            print(f"Unexpected error for {month}: {e}")

    # Si aucun fichier n'est trouvé, lever une erreur
    raise RuntimeError("No available Parquet file found in the last 6 months")


def upload_file(**kwargs):
    """Upload the downloaded file to MinIO."""
    # Retrieve the file path from XCom
    file_path = kwargs['ti'].xcom_pull(key='file_path', task_ids='download_parquet')
    if not file_path or not os.path.exists(file_path):
        raise RuntimeError(f"File not found at {file_path}")

    from minio import Minio, S3Error

    # MinIO client configuration
    client = Minio(
        "minio:9000",
        secure=False,
        access_key="minio",
        secret_key="minio123"
    )
    bucket = 'yellow-taxi-data'

    # Extract file name from the path
    object_name = os.path.basename(file_path)

    try:
        # Check if the bucket exists; if not, create it
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        # Upload the file
        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path
        )
        print(f"File uploaded successfully: {object_name}")
    except S3Error as e:
        raise RuntimeError(f"Failed to upload the file to MinIO: {str(e)}") from e
    finally:
        # Remove the local file after upload
        os.remove(file_path)


# Define the DAG
with DAG(
        dag_id='Grab_NYC_Data_to_Minio',
        start_date=days_ago(1),
        schedule_interval=None,
        catchup=False,
        tags=['minio', 'read', 'write']
) as dag:
    # Task to download the file
    t1 = PythonOperator(
        task_id='download_parquet',
        python_callable=download_parquet
    )

    # Task to upload the file
    t2 = PythonOperator(
        task_id='upload_file_task',
        python_callable=upload_file
    )

    # Task dependencies
    t1 >> t2
