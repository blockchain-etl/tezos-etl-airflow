merge `{{params.destination_dataset_project_id}}.{{params.destination_dataset_name}}.transactions` dest
using {{params.dataset_name_temp}}.{{params.source_table}} source
on false
when not matched and date(block_timestamp) = '{{ds}}' then
insert (
    block_hash,
    block_number,
    block_timestamp,
    `hash`,
    status,
    cpu_usage_us,
    net_usage_words,
    signatures,
    compression,
    packed_context_free_data,
    context_free_data,
    packed_trx,
    expiration,
    ref_block_num,
    ref_block_prefix,
    max_net_usage_words,
    max_cpu_usage_ms,
    delay_sec,
    deferred,
    action_count
) values (
    block_hash,
    block_number,
    block_timestamp,
    `hash`,
    status,
    cpu_usage_us,
    net_usage_words,
    signatures,
    compression,
    packed_context_free_data,
    context_free_data,
    packed_trx,
    expiration,
    ref_block_num,
    ref_block_prefix,
    max_net_usage_words,
    max_cpu_usage_ms,
    delay_sec,
    deferred,
    action_count
)
when not matched by source and date(block_timestamp) = '{{ds}}' then
delete
