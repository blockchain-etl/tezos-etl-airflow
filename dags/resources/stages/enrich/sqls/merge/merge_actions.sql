merge `{{params.destination_dataset_project_id}}.{{params.destination_dataset_name}}.actions` dest
using {{params.dataset_name_temp}}.{{params.source_table}} source
on false
when not matched and date(block_timestamp) = '{{ds}}' then
insert (
    block_hash,
    block_number,
    block_timestamp,
    transaction_hash,
    account,
    name,
    authorization,
    data,
    hex_data
) values (
    block_hash,
    block_number,
    block_timestamp,
    transaction_hash,
    account,
    name,
    authorization,
    data,
    hex_data
)
when not matched by source and date(block_timestamp) = '{{ds}}' then
delete
