-- Titan Company - Week 3, Day 2: Ranking Functions
-- No logic changes needed - ranking functions are structure-agnostic.

-- Finding diff between ROW_NUMBER and RANK
SELECT year, roce,
    ROW_NUMBER() OVER (ORDER BY roce DESC) AS row_roce,
    RANK() OVER (ORDER BY roce DESC) AS rank_roce
FROM titan_full;

-- Rank ROCE within High/Low buckets using CTE and window function
WITH bucketed AS (
    SELECT
        year,
        roce,
        CASE WHEN roce > (SELECT AVG(roce) FROM titan_full) THEN 'high' ELSE 'low' END AS roce_bucket
    FROM titan_full
),
avg_roce AS (
    SELECT AVG(roce) AS avg_roce
    FROM titan_full
)
SELECT
    a.year, b.avg_roce,
    a.roce,
    a.roce_bucket,
    RANK() OVER (PARTITION BY roce_bucket ORDER BY roce DESC) AS rank_within_bucket
FROM bucketed a
CROSS JOIN avg_roce b
ORDER BY a.roce_bucket, rank_within_bucket;

-- Using NTILE for quartile grouping
SELECT
    year,
    roce,
    NTILE(4) OVER (ORDER BY roce DESC) AS roce_quartile
FROM titan_full
ORDER BY roce DESC;