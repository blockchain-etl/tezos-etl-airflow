#standardSQL
SELECT *
FROM `public-data-finance.crypto_tezos.transaction_operations`
WHERE status = 'applied'
ORDER BY amount DESC
LIMIT 1000