import os
import json
import csv
import pandas as pd
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests

# Constantes
DATE = str(datetime.today().date()).replace('-', '')
OUTPUT_DIR = '/opt/airflow/dags/'  # Ruta dentro del contenedor Docker
CSV_FILE_PATH = os.path.join(OUTPUT_DIR, "file.csv")
OUTPUT_FILE_PATH = os.path.join(OUTPUT_DIR, "output_file.csv")


def get_key_from_item(item, key):
    #Obtiene la llave de un item o devuelve 'null' en caso de que no exista
    return str(item[key]).replace(' ', '').strip() if item.get(key) else "null"


def fetch_data_from_api():
    #Obtiene los datos requeridos de la API de Mercado Libre
    category = "MLC1403"
    url = f"https://api.mercadolibre.com/sites/MLC/search?category={category}#json"
    response = requests.get(url).text
    return json.loads(response).get("results", [])


def process_api_data(data):
    #Se procesan los datos obtenidos de la API y se convierten en un DataFrame usando Pandas
    records = []
    for item in data:
        _id = get_key_from_item(item, 'id')
        title = get_key_from_item(item, 'title')
        price = float(get_key_from_item(item, 'price')) if get_key_from_item(item, 'price') != "null" else None
        original_price = float(get_key_from_item(item, 'original_price')) if get_key_from_item(item, 'original_price') != "null" else None
        available_quantity = int(get_key_from_item(item, 'available_quantity')) if get_key_from_item(item, 'available_quantity') != "null" else 0
        thumbnail = get_key_from_item(item, 'thumbnail')

        records.append({
            'id': _id,
            'title': title,
            'price': price,
            'original_price': original_price,
            'available_quantity': available_quantity,
            'thumbnail': thumbnail,
            'created_date': DATE
        })
    
    return pd.DataFrame(records)


def save_data_to_csv(df):
    #Se guarda el DataFrame en un archivo tipo .CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(CSV_FILE_PATH, sep='\t', index=False)


def clean_data(input_file, output_file):
    #Se realiza limpieza de datos y se guarda el archivo limpio
    try:
        with open(input_file, mode='r') as infile, open(output_file, mode='w', newline='') as outfile:
            reader = csv.DictReader(infile, delimiter='\t')
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            for row in reader:
                try:
                    row['available_quantity'] = int(row['available_quantity'])
                    writer.writerow(row)
                except ValueError:
                    print(f"Skipping row with invalid available_quantity: {row['available_quantity']}")
    except Exception as e:
        print(f"Error cleaning data: {e}")


def load_data_to_postgres():
    #Carga de los datos limpios en PostgreSQL
    try:
        postgres_hook = PostgresHook(postgres_conn_id='postgres_localhost')
        connection = postgres_hook.get_conn()

        with connection.cursor() as cursor:
            with open(OUTPUT_FILE_PATH, 'r') as file:
                reader = csv.DictReader(file, delimiter='\t')
                for row in reader:
                    cursor.execute("""
                        INSERT INTO products_data (id, title, price, original_price, available_quantity, thumbnail, created_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING;
                    """, (row['id'], row['title'], row['price'], row['original_price'], row['available_quantity'], row['thumbnail'], row['created_date']))
            connection.commit()
    except Exception as e:
        print(f"Error loading data to PostgreSQL: {e}")


def deduplicate_and_insert():
    #Se insertan los datos de la tabla Staging a la tabla Principal sin duplicados
    insert_query = """
    INSERT INTO products_data (id, title, price, original_price, discount_percentage, available_quantity, thumbnail, created_date)
    SELECT
        id,
        title,
        price,
        original_price,
        CASE
            WHEN original_price IS NOT NULL AND price IS NOT NULL AND original_price > 0 AND price >= 0 THEN 
                ROUND(((original_price - price) / original_price) * 100, 2)
            ELSE NULL
        END AS discount_percentage,
        available_quantity,
        thumbnail,
        created_date
    FROM staging_products_data
    ON CONFLICT (id) DO NOTHING;
    """

    try:
        postgres_hook = PostgresHook(postgres_conn_id='postgres_localhost')
        connection = postgres_hook.get_conn()

        with connection.cursor() as cursor:
            cursor.execute(insert_query)
            connection.commit()
    except Exception as e:
        print(f"Error during deduplication and insert: {e}")


# Creación del DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='etl_to_postgres',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=lambda: save_data_to_csv(process_api_data(fetch_data_from_api())),
    )

    load_task = PythonOperator(
        task_id='load_to_staging',
        python_callable=load_data_to_postgres,
    )

    deduplicate_task = PythonOperator(
        task_id='deduplicate_and_insert',
        python_callable=deduplicate_and_insert,
    )

    extract_task >> load_task >> deduplicate_task
