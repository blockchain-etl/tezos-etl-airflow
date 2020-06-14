{% for operation_type in params.operation_types %}
{% if loop.index0 > 0 %}UNION ALL{% endif %}
SELECT
    level,
    timestamp,
    block_hash,
    branch,
    signature,
    operation_hash,
    operation_group_index,
    operation_index,
    internal_operation_index,
    '{{operation_type}}' AS operation_kind
FROM
    `{{params.destination_dataset_project_id}}.{{params.dataset_name}}.{{operation_type}}_operations`
{% endfor %}
