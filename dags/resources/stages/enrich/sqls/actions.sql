SELECT *
FROM {{params.dataset_name_raw}}.actions AS actions
where true
    {% if not params.load_all_partitions %}
    and date(actions.block_timestamp) = '{{ds}}'
    {% endif %}