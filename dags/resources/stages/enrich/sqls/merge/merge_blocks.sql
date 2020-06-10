merge `{{params.destination_dataset_project_id}}.{{params.destination_dataset_name}}.blocks` dest
using {{params.dataset_name_temp}}.{{params.source_table}} source
on false
when not matched and date(timestamp) = '{{ds}}' then
insert (
    `hash`,
    number ,
    timestamp,
    action_mroot,
    transaction_mroot,
    producer,
    transaction_count
) values (
     `hash`,
    number ,
    timestamp,
    action_mroot,
    transaction_mroot,
    producer,
    transaction_count
)
when not matched by source and date(timestamp) = '{{ds}}' then
delete
