## Variables

Below is the list of variables that can be configured in Airflow UI for Tezos ETL: 

- `output_bucket`: GCS bucket where exported files with blockchain data will be stored. 
- `export_start_date`: export start date, default: `2018-06-30`.
- `export_schedule_interval`: export cron schedule, default: `0 1 * * *`
- `provider_uris`: comma-separated list of provider URIs for [tezosetl export](https://tezos-etl.readthedocs.io/en/latest/commands/#export) command.
- `notification_emails`: comma-separated list of emails where notifications on DAG failures, retries and successes will be delivered.
- `export_max_active_runs`: max active DAG runs for export, default: `3`.
- `export_max_workers`: max workers for [tezosetl export](https://tezos-etl.readthedocs.io/en/latest/commands/#export) command, default: `30`.
- `destination_dataset_project_id`: GCS project id where destination BigQuery dataset is. 
- `load_schedule_interval`: load cron schedule, default: `0 2 * * *`
