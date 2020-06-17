# Tezos ETL Airflow

## Setup

1. Create a GCS bucket to hold export files:

    ```bash
    PROJECT=$(gcloud config get-value project 2> /dev/null)
    BUCKET=${PROJECT}-0
    gsutil mb gs://${BUCKET}/
    ```

2. Create a Google Cloud Composer environment:

    ```bash
    ENVIRONMENT_NAME=${PROJECT}-0
    gcloud composer environments create ${ENVIRONMENT_NAME} --location=us-central1 --zone=us-central1-a \
        --disk-size=30GB --machine-type=n1-standard-1 --node-count=3 --python-version=3 --image-version=composer-1.8.3-airflow-1.10.3 \
        --network=default --subnetwork=default
    
    gcloud composer environments update $ENVIRONMENT_NAME --location=us-central1 --update-pypi-package=tezos-etl==0.2.0
    ```

3. Upload Airflow variables: 

    - Edit `airflow_variables.json` and update configuration options. 
      You can find variable documentation in [variables.md](docs/variables.md)
    - Open Airflow UI. You can get its URL from airflowUri configuration option: 
      `gcloud composer environments describe ${ENVIRONMENT_NAME} --location us-central1`.
    - Navigate to **Admin > Variables** in the Airflow UI, click **Choose File**, select `airflow_variables.json`, 
      and click **Import Variables**.
    
4. Upload Airflow DAGs to the GCS bucket. 
    - Get Airflow DAGs URL from dagGcsPrefix configuration option:
      `gcloud composer environments describe ${ENVIRONMENT_NAME} --location us-central1`.
    - Upload DAGs to the bucket. Make sure to replace `<dag_gcs_prefix>` with your value:
      `./upload_dags.sh <dag_gcs_prefix>`.
    - Read an overview of how Airflow DAGs are structured: 
    https://cloud.google.com/blog/products/data-analytics/ethereum-bigquery-how-we-built-dataset.

5. Follow these steps to configure email notifications 
https://cloud.google.com/composer/docs/how-to/managing/creating#notification.