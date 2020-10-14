#standardSQL
WITH double_entry_book as (
    SELECT IF(kind = 'contract', contract, delegate) AS address, change AS value
    FROM `public-data-finance.crypto_tezos.balance_updates`
    WHERE status IS NULL OR status = 'applied'
    UNION ALL
    SELECT address, balance_change
    FROM `public-data-finance.crypto_tezos.migrations`
)
SELECT address, SUM(value) AS balance
FROM double_entry_book
GROUP BY address
ORDER BY balance DESC
LIMIT 1000