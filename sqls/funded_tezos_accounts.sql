#standardSQL
-- Read this article to understand this query https://medium.com/google-cloud/plotting-ethereum-address-growth-chart-55cc0e7207b2
WITH double_entry_book as (
    SELECT timestamp, IF(kind = 'contract', contract, delegate) AS address, change AS value
    FROM `public-data-finance.crypto_tezos.balance_updates`
    WHERE status IS NULL OR status = 'applied'
    UNION ALL
    SELECT timestamp, address, balance_change
    FROM `public-data-finance.crypto_tezos.migrations`
),
double_entry_book_grouped_by_date as (
    SELECT address, sum(value) AS balance_increment, DATE(timestamp) AS date
    FROM double_entry_book
    GROUP BY address, date
),
daily_balances_with_gaps AS (
    SELECT address, date, SUM(balance_increment) OVER (PARTITION BY address ORDER BY date) AS balance,
    LEAD(date, 1, CURRENT_DATE()) OVER (PARTITION BY address ORDER BY date) AS next_date
    FROM double_entry_book_grouped_by_date
),
calendar AS (
    SELECT date FROM UNNEST(GENERATE_DATE_ARRAY('2018-06-30', CURRENT_DATE())) AS date
),
daily_balances AS (
    SELECT address, calendar.date, balance
    FROM daily_balances_with_gaps
    JOIN calendar ON daily_balances_with_gaps.date <= calendar.date AND calendar.date < daily_balances_with_gaps.next_date
)
SELECT date, COUNT(*) AS address_count
FROM daily_balances
WHERE balance > 0
GROUP BY date
ORDER BY date DESC
