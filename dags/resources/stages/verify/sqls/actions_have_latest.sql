select if(
(
select count(*) from `{{params.destination_dataset_project_id}}.{{params.dataset_name}}.actions`
where date(block_timestamp) = '{{ds}}'
) > 0, 1,
cast((select 'There are no actions on {{ds}}') as int64))
