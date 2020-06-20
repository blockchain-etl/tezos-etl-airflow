# Tezos ETL Airflow

## Setting Up

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
    
    gcloud composer environments update $ENVIRONMENT_NAME --location=us-central1 --update-pypi-package=tezos-etl==1.0.1
    ```

3. Follow the steps in [Configuring Airflow Variables](#configuring-airflow-variables) to configure Airfow variables.
    
4. Follow the steps in [Deploying Airflow DAGs](#deploying-airflow-dags) 
to deploy Airflow DAGs to Cloud Composer Environment.
 
5. Follow the steps [here](https://cloud.google.com/composer/docs/how-to/managing/creating#notification) 
to configure email notifications.

## Configuring Airflow Variables

- Edit `airflow_variables.json` and update configuration options. 
  You can find variables description in the table below. For the `tezos_output_bucket` variable 
  specify the bucket created on step 1 above. You can get it by running `echo $BUCKET`.
- Open Airflow UI. You can get its URL from `airflowUri` configuration option: 
  `gcloud composer environments describe ${ENVIRONMENT_NAME} --location us-central1`.
- Navigate to **Admin > Variables** in the Airflow UI, click **Choose File**, select `airflow_variables.json`, 
  and click **Import Variables**.
  
### Airflow Variables

Note that the variable names must be prefixed with `{chain}_`, e.g. `tezos_output_bucket`. 

| Variable | Description |
|---|---|
| `output_bucket` | GCS bucket where exported files with blockchain data will be stored |
| `export_start_date` | export start date, default: `2018-06-30` |
| `export_end_date` | export end date, used for integration testing, default: None |
| `export_schedule_interval` | export cron schedule, default: `0 1 * * *` |
| `provider_uris` | comma-separated list of provider URIs for [tezosetl export](https://tezos-etl.readthedocs.io/en/latest/commands/#export) command |
| `notification_emails` | comma-separated list of emails where notifications on DAG failures, retries and successes will be delivered |
| `export_max_active_runs` | max active DAG runs for export, default: `3` |
| `export_max_workers` | max workers for [tezosetl export](https://tezos-etl.readthedocs.io/en/latest/commands/#export) command, default: `30` |
| `destination_dataset_project_id` | GCS project id where destination BigQuery dataset is |
| `load_schedule_interval` | load cron schedule, default: `0 2 * * *` |
| `load_end_date` | load end date, used for integration testing, default: None |
  
## Deploying Airflow DAGs

- Get the value from `dagGcsPrefix` configuration option:
  `gcloud composer environments describe ${ENVIRONMENT_NAME} --location us-central1`.
- Upload DAGs to the bucket. Make sure to replace `<dag_gcs_prefix>` with the value from the previous step:
  `./upload_dags.sh <dag_gcs_prefix>`.
- To understand more about how the Airflow DAGs are structured 
  read [this article](https://cloud.google.com/blog/products/data-analytics/ethereum-bigquery-how-we-built-dataset).
- Note that it will take one or more days for `tezos_export_dag` to finish exporting the historical data.
- To setup automated deployment of DAGs refer to [Cloud Build](/docs/cloudbuild.md).

## Integration Testing

It is [recommended](https://cloud.google.com/composer/docs/how-to/using/testing-dags#faqs_for_testing_workflows) to use a dedicated Cloud Composer
environment for integration testing with Airflow.

To run integration tests:
 
- Create a new environment following the steps in the [Setting Up](#setting-up) section.
- On the [Configuring Airflow Variables](#configuring-airflow-variables) step specify the following additional configuration variables:
    - `export_end_date`: `2018-06-30`
    - `load_end_date`: `2018-06-30`
- This will run the DAGs only for the first day. At the end of the load DAG the verification tasks will ensure
the correctness of the result.