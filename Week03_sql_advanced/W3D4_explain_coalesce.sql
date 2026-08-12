-- Titan Company - Week 3, Day 4: NULL Handling, Safe Division, Indexing

-- COALESCE: use preferred column, fall back to proxy when NULL
-- Mirrors the get_column_with_fallback() pattern already in the Python pipeline
SELECT
    year,
    avg_debtors,
    debtors,
    COALESCE(avg_debtors, debtors) AS debtors_final
FROM titan_full
ORDER BY year;

-- NULLIF: returns NULL if two values are equal, avoids division-by-zero
SELECT
    year,
    sales,
    inventory,
    sales / NULLIF(inventory, 0) AS inventory_turnover_safe
FROM titan_full
ORDER BY year;

-- EXPLAIN: see how MySQL executes a query, before indexing
EXPLAIN SELECT * FROM titan_full WHERE year = 2021;

-- Adding an index and re-checking the execution plan
ALTER TABLE titan_full ADD INDEX idx_year (year);
EXPLAIN SELECT * FROM titan_full WHERE year = 2021;