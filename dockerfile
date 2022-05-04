FROM puckel/docker-airflow:1.10.9

WORKDIR /usr/local/airflow/
ENV DAGS_FOLDER /usra/local/airflow/dags

COPY requirements.txt .
RUN pip install --user -r requirements.txt