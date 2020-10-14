#standardSQL
SELECT baker, COUNT(*) AS block_count
FROM `public-data-finance.crypto_tezos.blocks`
GROUP BY baker
ORDER BY block_count DESC
LIMIT 1000