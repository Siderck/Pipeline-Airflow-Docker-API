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
                    id varchar(30),
                    site_id varchar(30),
                    title varchar(50),
                    price varchar(10),
                    sold_quantity varchar(20),
                    thumbnail varchar(50),
                    created_date varchar(8),
                    primary key(id,created_date)
                )
              """
    )