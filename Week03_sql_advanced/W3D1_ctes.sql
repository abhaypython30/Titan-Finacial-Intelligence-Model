-- Titan Company - Week 3, Day 1: CTEs and YoY Change Detection

WITH avg_roce AS (
    SELECT AVG(roce) AS avg_value
    FROM titan_full
)
SELECT
    year,
    roce
FROM titan_full, avg_roce
WHERE roce > 1.0
ORDER BY year;


-- Chained CTE - Year-over-year ROCE change, flagged if move > 4 percentage points
WITH yoy_change AS (
    SELECT
        year,
        roce,
        (roce - LAG(roce, 1) OVER (ORDER BY year)) * 100 AS roce_change_pct
    FROM titan_full
),
flagged AS (
    SELECT year, roce, roce_change_pct
    FROM yoy_change
    WHERE ABS(roce_change_pct) > 4.0
)
SELECT * FROM flagged ORDER BY year;

-- EXPECTED FOR TITAN: given Week2's finding that FY2021 ROCE dropped from
-- ~18-20% average to 10.28%, this query should flag FY2021 (and possibly
-- the FY2022 recovery bounce-back) - if it doesn't, that's worth checking
-- against Week2's pandas-derived anomaly instead of assuming this SQL
-- query is automatically right.