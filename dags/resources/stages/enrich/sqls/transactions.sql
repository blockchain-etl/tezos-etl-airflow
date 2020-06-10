SELECT *
FROM {{params.dataset_name_raw}}.transactions AS transactions
where true
    {% if not params.load_all_partitions %}
    and date(transactions.block_timestamp) = '{{ds}}'
    {% endif %}
