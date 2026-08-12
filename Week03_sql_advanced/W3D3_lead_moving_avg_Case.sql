-- Titan Company - Week 3, Day 3: Forward-Looking Windows and Trend Bucketing

-- LEAD() - forward-looking comparison
SELECT
    year, roce,
    LEAD(roce, 1) OVER (ORDER BY year) AS next_year_roce
FROM titan_full;

-- 3-Year Moving Average - window frame syntax
SELECT
    year, roce,
    AVG(roce) OVER (ORDER BY year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS avg3yr
FROM titan_full
ORDER BY year;

-- CASE WHEN - trend bucketing on YoY change
WITH yoy AS (
    SELECT
        year,
        roce,
        (roce - LAG(roce, 1) OVER (ORDER BY year)) * 100 AS roce_change_pct
    FROM titan_full
)
SELECT
    year,
    roce,
    roce_change_pct,
    CASE
        WHEN roce_change_pct > 3 THEN 'improving'
        WHEN roce_change_pct < -3 THEN 'declining'
        ELSE 'stable'
    END AS trend_category
FROM yoy
ORDER BY year;

-- EXPECTED FOR TITAN: given Week2's era summary, FY2021 should show
-- 'declining' (the COVID trough) and FY2022 should show 'improving'
-- (recovery bounce) - cross-check against the actual output.