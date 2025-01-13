from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

# Configuration PostgreSQL
WAREHOUSE_DB = "postgresql+psycopg2://postgres:admin@atl-datamart-main-db-warehouse-1:5432/warehouse_db"
DATAMART_DB = "postgresql+psycopg2://postgres:admin@atl-datamart-main-db-mart-1:5432/mart_db"

# Fonction pour extraire les données de rides
def extract_rides(**kwargs):
    engine = create_engine(WAREHOUSE_DB)
    query = "SELECT * FROM rides WHERE tpep_pickup_datetime >= '2024-01-01'"
    rides_data = pd.read_sql(query, engine)
    kwargs['ti'].xcom_push(key='rides_data', value=rides_data)

# Fonction pour transformer les données
def transform_rides(**kwargs):
    ti = kwargs['ti']
    rides_data = ti.xcom_pull(key='rides_data')
    rides_data['revenue_per_km'] = rides_data['total_amount'] / rides_data['trip_distance']
    ti.xcom_push(key='transformed_rides', value=rides_data)

# Fonction pour charger les données dans Datamart
def load_to_datamart(**kwargs):
    engine = create_engine(DATAMART_DB)
    ti = kwargs['ti']
    transformed_rides = ti.xcom_pull(key='transformed_rides')
    transformed_rides.to_sql('rides_analysis', engine, if_exists='replace', index=False)

# Définition du DAG
default_args = {
    'owner': 'axel',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    'etl_rides_pipeline',
    default_args=default_args,
    schedule='@daily'
) as dag:
    extract = PythonOperator(
        task_id='extract_rides',
        python_callable=extract_rides
    )
    transform = PythonOperator(
        task_id='transform_rides',
        python_callable=transform_rides
    )
    load = PythonOperator(
        task_id='load_to_datamart',
        python_callable=load_to_datamart
    )

    # Définir les dépendances des tâches
    extract >> transform >> load
