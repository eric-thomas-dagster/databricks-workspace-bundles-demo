-- Customer cohort analysis for retention tracking (EU region, GDPR-compliant)
-- Depends on: customer_metrics (dbt model)

{{ config(
    materialized='table',
    tags=['gold', 'eu', 'customer_cohorts', 'gdpr']
) }}

SELECT
    DATE_TRUNC('month', last_order_date) as cohort_month,
    CASE
        WHEN lifetime_value >= 10000 THEN 'High Value'
        WHEN lifetime_value >= 5000 THEN 'Medium Value'
        ELSE 'Low Value'
    END as customer_segment,
    COUNT(*) as customer_count,
    AVG(lifetime_value) as avg_lifetime_value,
    AVG(total_orders) as avg_orders_per_customer,
    MIN(lifetime_value) as min_lifetime_value,
    MAX(lifetime_value) as max_lifetime_value
FROM {{ ref('customer_metrics') }}
GROUP BY
    cohort_month,
    customer_segment
ORDER BY
    cohort_month DESC,
    customer_segment
