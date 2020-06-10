SELECT *
FROM {{params.dataset_name_raw}}.blocks AS blocks
where true
    {% if not params.load_all_partitions %}
    and date(blocks.timestamp) = '{{ds}}'
    {% endif %}
