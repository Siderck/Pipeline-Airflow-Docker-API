from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG(
    dag_id = "scraping_pipeline",
    start_date=datetime(2024,11,18)
) as dag:
    task_1 = PostgresOperator(
        task_id="Crear_tabla",
        postgres_conn_id = "postgres_localhost",
        sql = """
                create table if not exists prueba_ml (
                    id varchar(30) primary key,
                    title varchar(255),
                    price decimal(10, 2),
                    original_price decimal(10, 2),
                    discount_percentage decimal(5, 2),  -- Nuevo campo para el porcentaje de descuento
                    available_quantity integer,
                    thumbnail varchar(255),
                    created_date varchar(8)
                )
              """
    )
