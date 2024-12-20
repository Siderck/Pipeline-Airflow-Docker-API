# Usa la imagen oficial de Airflow como base
FROM apache/airflow:2.10.3

# Copia los archivos de configuración, DAGs, plugins y otros recursos necesarios
# En este caso se espera que tengas una estructura de carpetas local adecuada para ello
# que se copiará al contenedor de Docker
COPY dags /opt/airflow/dags
COPY logs /opt/airflow/logs
COPY plugins /opt/airflow/plugins
COPY config /opt/airflow/config

# Establece las variables de entorno necesarias
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__EXECUTOR=CeleryExecutor
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
ENV AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow
ENV AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0
ENV AIRFLOW__CORE__FERNET_KEY=''
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
ENV AIRFLOW__API__AUTH_BACKENDS='airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'
ENV AIRFLOW__CORE__TEST_CONNECTION='Enabled'
ENV AIRFLOW__CORE__DAG_DIR_LIST_INTERVAL=30
ENV AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=30
ENV AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK=true

# Instalar dependencias adicionales si es necesario
# RUN pip install <paquete-suscribo>  # Descomenta esta línea si necesitas paquetes adicionales

# Configura el contenedor para que use un usuario específico para evitar problemas de permisos
USER ${AIRFLOW_UID:-50000}

# El comando de inicio predeterminado para este contenedor
CMD ["bash", "-c", "airflow webserver"]
