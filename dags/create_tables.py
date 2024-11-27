from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

# DAG para la creación de tablas y manejo de datos
with DAG(
    dag_id="create_tables",
    start_date=datetime(2024, 11, 18),
    schedule_interval=None,  # Ejecución manual para pruebas
    catchup=False,
) as dag:

    # Creación tabla principal en la base de datos
    create_main_table = PostgresOperator(
        task_id="crear_tabla_principal",
        postgres_conn_id="postgres_localhost",
        sql="""
            CREATE TABLE IF NOT EXISTS products_data (
                id VARCHAR(30) PRIMARY KEY,
                title VARCHAR(255),
                price DECIMAL(10, 2),
                original_price DECIMAL(10, 2),
                discount_percentage DECIMAL(5, 2),  -- Porcentaje de descuento
                available_quantity INTEGER,
                thumbnail VARCHAR(255),
                created_date VARCHAR(8)
            );

            -- Crear índice para búsquedas rápidas por fecha
            CREATE INDEX IF NOT EXISTS idx_created_date ON products_data(created_date);
        """,
    )

    # Creación tabla de Staging
    create_staging_table = PostgresOperator(
        task_id="crear_tabla_staging",
        postgres_conn_id="postgres_localhost",
        sql="""
            CREATE TABLE IF NOT EXISTS staging_products_data (
                id VARCHAR(30),
                title VARCHAR(255),
                price DECIMAL(10, 2),
                original_price DECIMAL(10, 2),
                discount_percentage DECIMAL(5, 2),  -- Porcentaje de descuento
                available_quantity INTEGER,
                thumbnail VARCHAR(255),
                created_date VARCHAR(8)
            );

            -- Vaciar la tabla de staging antes de cada nueva ejecución
            TRUNCATE TABLE staging_products_data;
        """,
    )

    # Flujo Airflow
    create_main_table >> create_staging_table
