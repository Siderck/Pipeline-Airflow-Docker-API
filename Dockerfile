# Usa la imagen base de Airflow
FROM ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.10.3}

# Establecer el usuario para evitar problemas de permisos con archivos creados dentro del contenedor
USER root

# Crea los directorios de logs, configuraciones y plugins
RUN mkdir -p /opt/airflow/logs /opt/airflow/config /opt/airflow/plugins

# Asigna permisos adecuados a los directorios
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/logs /opt/airflow/config /opt/airflow/plugins


USER ${AIRFLOW_UID:-50000}

# Establecer el directorio de trabajo para Airflow
WORKDIR /opt/airflow

# Exponer los puertos necesarios
EXPOSE 8080 5555

# Comando para iniciar Airflow (esto será reemplazado por docker-compose)
ENTRYPOINT ["entrypoint"]
CMD ["airflow", "version"]
