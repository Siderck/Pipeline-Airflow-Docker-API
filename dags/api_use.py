from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import pandas as pd
import requests
import os
import json
import csv

# Configurar la fecha actual
DATE = str(datetime.today().date()).replace('-', '')

# Función auxiliar
def getKeyFromItem(item, key):
    return str(item[key]).replace(' ', '').strip() if item.get(key) else "null"

# Función para realizar el ETL y guardar en .tsv
def get_most_relevant_item_by_category():
    category = "MLC1403"
    url = f"https://api.mercadolibre.com/sites/MLC/search?category={category}#json"
    response = requests.get(url).text
    response = json.loads(response)
    data = response["results"]

    records = []
    for item in data:
        _id = getKeyFromItem(item, 'id')
        title = getKeyFromItem(item, 'title')
        price = float(getKeyFromItem(item, 'price')) if getKeyFromItem(item, 'price') != "null" else None
        original_price = float(getKeyFromItem(item, 'original_price')) if getKeyFromItem(item, 'original_price') != "null" else None
        available_quantity = int(getKeyFromItem(item, 'available_quantity')) if getKeyFromItem(item, 'available_quantity') != "null" else 0  # Cambié a 0 en lugar de None
        thumbnail = getKeyFromItem(item, 'thumbnail')

        records.append({
            'id': _id,
            'title': title,
            'price': price,
            'original_price': original_price,
            'available_quantity': available_quantity,  # Ahora nunca será None
            'thumbnail': thumbnail,
            'created_date': DATE
        })

    # Convertir a DataFrame
    df = pd.DataFrame(records)

    # Crear el directorio si no existe
    output_dir = r"D:\airflow-docker\tmp"  # Cambiar a la ruta deseada
    os.makedirs(output_dir, exist_ok=True)

    # Guardar como archivo TSV
    file_path = os.path.join(output_dir, "file.tsv")  # Archivo en la ruta especificada
    df.to_csv(file_path, sep='\t', index=False)

# Función para limpiar los datos (por ejemplo, asegurarse de que 'available_quantity' sea un entero válido)
def clean_data(input_file, output_file):
    with open(input_file, mode='r') as infile, open(output_file, mode='w', newline='') as outfile:
        reader = csv.DictReader(infile, delimiter='\t')
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t')
        
        writer.writeheader()
        
        for row in reader:
            try:
                # Intentar convertir available_quantity a un entero
                row['available_quantity'] = int(row['available_quantity'])
                writer.writerow(row)
            except ValueError:
                # Si falla la conversión, puedes omitir la fila o manejar el error
                print(f"Skipping row with invalid available_quantity: {row['available_quantity']}")

# Función para cargar los datos en PostgreSQL
def load_tsv_to_postgres():
    input_file = '/opt/airflow/dags/file.tsv'  # Ruta dentro del contenedor
    output_file = '/opt/airflow/dags/output_file.csv'  # Ruta dentro del contenedor



    # Limpiar los datos antes de cargar
    clean_data(input_file, output_file)

    copy_query = """
    COPY prueba_ml (id, title, price, original_price, available_quantity, thumbnail, created_date)
    FROM STDIN
    WITH (FORMAT csv, DELIMITER E'\t', HEADER true);
    """

    # Usar PostgresHook
    postgres_hook = PostgresHook(postgres_conn_id='postgres_localhost')
    connection = postgres_hook.get_conn()

    with connection.cursor() as cursor:
        with open(output_file, 'r') as file:
            cursor.copy_expert(copy_query, file)
        connection.commit()

# Crear el DAG
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
        python_callable=get_most_relevant_item_by_category,
    )

    load_task = PythonOperator(
        task_id='load_to_postgres',
        python_callable=load_tsv_to_postgres,
    )

    extract_task >> load_task
