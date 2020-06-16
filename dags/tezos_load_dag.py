from __future__ import print_function

import logging

from tezosetl_airflow.build_load_dag import build_load_dag
from tezosetl_airflow.variables import read_load_dag_vars

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

# airflow DAG
DAG = build_load_dag(
    dag_id='tezos_load_dag',
    chain='tezos',
    **read_load_dag_vars(
        var_prefix='tezos_',
        load_schedule_interval='0 2 * * *'
    )
)
