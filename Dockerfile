FROM ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.10.3}

# Cambiar al usuario root
USER root

# Instalar python3-venv y otras dependencias necesarias
RUN apt-get update && apt-get install -y \
    python3-venv \
    python3-pip \
    && apt-get clean

# Crear directorios necesarios y establecer permisos
RUN mkdir -p /opt/airflow/logs /opt/airflow/config /opt/airflow/plugins
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/logs /opt/airflow/config /opt/airflow/plugins

# Volver al usuario Airflow
USER ${AIRFLOW_UID:-50000}

# Establecer el directorio de trabajo
WORKDIR /opt/airflow

# Exponer puertos
EXPOSE 8080 5555

# Comando por defecto
ENTRYPOINT ["entrypoint"]
CMD ["airflow", "version"]
