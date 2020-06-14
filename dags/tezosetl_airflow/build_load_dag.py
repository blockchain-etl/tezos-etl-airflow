from __future__ import print_function

import json
import logging
import os
import time
from datetime import datetime, timedelta

from tezosetl.enums.operations_types import OperationType

from airflow import models
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.sensors.gcs_sensor import GoogleCloudStorageObjectSensor
from airflow.operators.email_operator import EmailOperator
from airflow.operators.python_operator import PythonOperator
from google.cloud import bigquery
from google.cloud.bigquery import TimePartitioning, SchemaField

from tezosetl_airflow.bigquery_utils import submit_bigquery_job, read_bigquery_schema_from_json_recursive, \
    create_dataset

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


def build_load_dag(
        dag_id,
        output_bucket,
        destination_dataset_project_id,
        chain='tezos',
        notification_emails=None,
        load_start_date=datetime(2018, 7, 1),
        schedule_interval='0 0 * * *',
        load_all_partitions=True
):
    # Environment variable OUTPUT_BUCKET must be set and point to the GCS bucket
    # where files exported by export_dag.py are located

    dataset_name = f'crypto_{chain}'
    dataset_name_raw = f'crypto_{chain}_raw'
    dataset_name_temp = f'crypto_{chain}_temp'

    if not destination_dataset_project_id:
        raise ValueError('destination_dataset_project_id is required')

    environment = {
        'dataset_name': dataset_name,
        'dataset_name_raw': dataset_name_raw,
        'dataset_name_temp': dataset_name_temp,
        'destination_dataset_project_id': destination_dataset_project_id,
        'load_all_partitions': load_all_partitions
    }

    default_dag_args = {
        'depends_on_past': False,
        'start_date': load_start_date,
        'email_on_failure': True,
        'email_on_retry': True,
        'retries': 5,
        'retry_delay': timedelta(minutes=5)
    }

    if notification_emails and len(notification_emails) > 0:
        default_dag_args['email'] = [email.strip() for email in notification_emails.split(',')]

    # Define a DAG (directed acyclic graph) of tasks.
    dag = models.DAG(
        dag_id,
        catchup=False,
        schedule_interval=schedule_interval,
        default_args=default_dag_args)

    dags_folder = os.environ.get('DAGS_FOLDER', '/home/airflow/gcs/dags')

    def add_load_tasks(task, file_format='json', time_partitioning_field='timestamp'):
        # wait_sensor = GoogleCloudStorageObjectSensor(
        #     task_id='wait_latest_{task}'.format(task=task),
        #     timeout=60 * 60,
        #     poke_interval=60,
        #     bucket=output_bucket,
        #     object='export/{task}/block_date={datestamp}/{task}.{file_format}'.format(
        #         task=task, datestamp='{{ds}}', file_format=file_format),
        #     dag=dag
        # )

        def load_task():
            client = bigquery.Client()
            job_config = bigquery.LoadJobConfig()
            schema_path = os.path.join(dags_folder, 'resources/stages/raw/schemas/{task}.json'.format(task=task))
            job_config.schema = read_bigquery_schema_from_file(schema_path)
            job_config.source_format = bigquery.SourceFormat.CSV if file_format == 'csv' else bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
            job_config.write_disposition = 'WRITE_TRUNCATE'
            job_config.ignore_unknown_values = True
            if time_partitioning_field is not None:
                job_config.time_partitioning = TimePartitioning(field=time_partitioning_field)

            export_location_uri = 'gs://{bucket}/export'.format(bucket=output_bucket)
            uri = '{export_location_uri}/{task}/*.{file_format}'.format(
                export_location_uri=export_location_uri, task=task, file_format=file_format)
            table_ref = create_dataset(client, dataset_name_raw).table(task)
            load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)
            submit_bigquery_job(load_job, job_config)
            assert load_job.state == 'DONE'

        load_operator = PythonOperator(
            task_id='load_{task}'.format(task=task),
            python_callable=load_task,
            execution_timeout=timedelta(minutes=30),
            dag=dag
        )

        # wait_sensor >> load_operator
        return load_operator

    def add_enrich_tasks(task, time_partitioning_field='block_timestamp', dependencies=None):
        def enrich_task(ds, **kwargs):
            template_context = kwargs.copy()
            template_context['ds'] = ds
            template_context['params'] = environment

            client = bigquery.Client()

            # Need to use a temporary table because bq query sets field modes to NULLABLE and descriptions to null
            # when writeDisposition is WRITE_TRUNCATE

            # Create a temporary table
            temp_table_name = '{task}_{milliseconds}'.format(task=task, milliseconds=int(round(time.time() * 1000)))
            temp_table_ref = create_dataset(client, dataset_name_temp).table(temp_table_name)

            # Enriched schemas are same as raw
            schema_path = os.path.join(dags_folder, 'resources/stages/raw/schemas/{task}.json'.format(task=task))
            schema = read_bigquery_schema_from_file(schema_path)
            table = bigquery.Table(temp_table_ref, schema=schema)

            table.description = read_file('Data is exported using https://github.com/blockchain-etl/tezos-etl')
            if time_partitioning_field is not None:
                table.time_partitioning = TimePartitioning(field=time_partitioning_field)
            logging.info('Creating table: ' + json.dumps(table.to_api_repr()))
            table = client.create_table(table)
            assert table.table_id == temp_table_name

            # Query from raw to temporary table
            query_job_config = bigquery.QueryJobConfig()
            # Finishes faster, query limit for concurrent interactive queries is 50
            query_job_config.priority = bigquery.QueryPriority.INTERACTIVE
            query_job_config.destination = temp_table_ref

            sql_path = os.path.join(dags_folder, 'resources/stages/enrich/sqls/{task}.sql'.format(task=task))
            sql_template = read_file(sql_path)
            sql = kwargs['task'].render_template('', sql_template, template_context)
            print('Enrichment sql:')
            print(sql)

            query_job = client.query(sql, location='US', job_config=query_job_config)
            submit_bigquery_job(query_job, query_job_config)
            assert query_job.state == 'DONE'

            if load_all_partitions:
                # Copy temporary table to destination
                copy_job_config = bigquery.CopyJobConfig()
                copy_job_config.write_disposition = 'WRITE_TRUNCATE'
                dest_table_name = '{task}'.format(task=task)
                dest_table_ref = create_dataset(client, dataset_name, project=destination_dataset_project_id).table(dest_table_name)
                copy_job = client.copy_table(temp_table_ref, dest_table_ref, location='US', job_config=copy_job_config)
                submit_bigquery_job(copy_job, copy_job_config)
                assert copy_job.state == 'DONE'
            else:
                # Merge
                # https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement
                merge_job_config = bigquery.QueryJobConfig()
                # Finishes faster, query limit for concurrent interactive queries is 50
                merge_job_config.priority = bigquery.QueryPriority.INTERACTIVE

                merge_sql_path = os.path.join(
                    dags_folder, 'resources/stages/enrich/sqls/merge/merge_{task}.sql'.format(task=task))
                merge_sql_template = read_file(merge_sql_path)

                merge_template_context = template_context.copy()
                merge_template_context['params']['source_table'] = temp_table_name
                merge_template_context['params']['destination_dataset_project_id'] = destination_dataset_project_id
                merge_template_context['params']['destination_dataset_name'] = dataset_name
                merge_sql = kwargs['task'].render_template('', merge_sql_template, merge_template_context)
                print('Merge sql:')
                print(merge_sql)
                merge_job = client.query(merge_sql, location='US', job_config=merge_job_config)
                submit_bigquery_job(merge_job, merge_job_config)
                assert merge_job.state == 'DONE'

            # Delete temp table
            client.delete_table(temp_table_ref)

        enrich_operator = PythonOperator(
            task_id='enrich_{task}'.format(task=task),
            python_callable=enrich_task,
            provide_context=True,
            execution_timeout=timedelta(minutes=60),
            dag=dag
        )

        if dependencies is not None and len(dependencies) > 0:
            for dependency in dependencies:
                dependency >> enrich_operator
        return enrich_operator

    def add_verify_tasks(task, dependencies=None):
        # The queries in verify/sqls will fail when the condition is not met
        # Have to use this trick since the Python 2 version of BigQueryCheckOperator doesn't support standard SQL
        # and legacy SQL can't be used to query partitioned tables.
        sql_path = os.path.join(dags_folder, 'resources/stages/verify/sqls/{task}.sql'.format(task=task))
        sql = read_file(sql_path)
        verify_task = BigQueryOperator(
            task_id='verify_{task}'.format(task=task),
            bql=sql,
            params=environment,
            use_legacy_sql=False,
            dag=dag)
        if dependencies is not None and len(dependencies) > 0:
            for dependency in dependencies:
                dependency >> verify_task
        return verify_task

    all_tables = ['blocks', 'balance_updates'] + [f'{ot}_operations' for ot in OperationType.ALL]

    task_map = {
        'load': {}
    }
    for table in all_tables:
        load_task = add_load_tasks(table)
        task_map['load'][table] = load_task

    return dag


def read_bigquery_schema_from_file(filepath):
    file_content = read_file(filepath)
    json_content = json.loads(file_content)
    return read_bigquery_schema_from_json_recursive(json_content)


def read_file(filepath):
    with open(filepath) as file_handle:
        content = file_handle.read()
        return content
