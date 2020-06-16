SELECT IF(
(
    SELECT SUM(number_of_operations)
    FROM `{{params.destination_dataset_project_id}}.{{params.dataset_name}}.blocks`
    WHERE DATE(timestamp) <= '{{ds}}'
) =
(
    SELECT COUNT(*)
    FROM `{{params.destination_dataset_project_id}}.{{params.dataset_name}}.operations`
    WHERE DATE(timestamp) <= '{{ds}}'
), 1,
CAST((SELECT 'Total number of operations is not equal to sum of number_of_operations in blocks table') AS INT64))
