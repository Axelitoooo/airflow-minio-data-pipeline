from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2

# Configuration des bases de données
DB_WAREHOUSE = {
    "user": "admin",
    "password": "admin",
    "host": "localhost",
    "port": "15434",
    "dbname": "warehouse_db"
}

DB_MART = {
    "user": "admin",
    "password": "admin",
    "host": "localhost",
    "port": "15435",
    "dbname": "mart_db"
}

def transfer_yellow_taxi_data(**kwargs):
    try:
        with psycopg2.connect(**DB_WAREHOUSE) as warehouse_conn, psycopg2.connect(**DB_MART) as mart_conn:
            with warehouse_conn.cursor() as warehouse_cursor, mart_conn.cursor() as mart_cursor:
                warehouse_cursor.execute("SELECT * FROM yellow_taxi_data;")
                while True:
                    rows = warehouse_cursor.fetchmany(1000)  # Transfert par lots
                    if not rows:
                        break
                    insert_query = """
                    INSERT INTO yellow_taxi_data (
                        VendorID, tpep_pickup_datetime, tpep_dropoff_datetime, passenger_count, 
                        trip_distance, RatecodeID, store_and_fwd_flag, PULocationID, DOLocationID, 
                        payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount, 
                        improvement_surcharge, total_amount, congestion_surcharge, Airport_fee
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                    mart_cursor.executemany(insert_query, rows)
                mart_conn.commit()
    except Exception as e:
        print(f"Erreur lors du transfert : {str(e)}")
        raise

def clean_locations_table(**kwargs):
    try:
        with psycopg2.connect(**DB_MART) as mart_conn:
            with mart_conn.cursor() as mart_cursor:
                alter_query = """
                ALTER TABLE locations
                DROP COLUMN IF EXISTS location_name,
                DROP COLUMN IF EXISTS location_type;
                """
                mart_cursor.execute(alter_query)
                mart_conn.commit()
    except Exception as e:
        print(f"Erreur lors du nettoyage : {str(e)}")
        raise

# Définition du DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    dag_id='etl_yellow_taxi_data',
    default_args=default_args,
    description='Transfert de données entre Warehouse et Mart',
    schedule_interval='@daily',  # Planification quotidienne
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    # Tâche de transfert des données
    transfer_task = PythonOperator(
        task_id='transfer_yellow_taxi_data',
        python_callable=transfer_yellow_taxi_data
    )

    # Tâche de nettoyage de la table locations
    clean_task = PythonOperator(
        task_id='clean_locations_table',
        python_callable=clean_locations_table
    )

    # Dépendance : transfert -> nettoyage
    transfer_task >> clean_task
