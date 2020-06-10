select if(
(
select sum(action_count)
from `{{params.destination_dataset_project_id}}.{{params.dataset_name}}.transactions`
where date(block_timestamp) <= '{{ds}}'
) =
(
select count(*)
from `{{params.destination_dataset_project_id}}.{{params.dataset_name}}.actions`
where date(block_timestamp) <= '{{ds}}'
), 1,
cast((select 'Total number of actions is not equal to sum of action_count in transactions table') as int64))
