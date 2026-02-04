-- Customer cohort analysis for retention tracking
-- Works for both US and EU regions based on target

{{
    config(
        materialized='table',
        tags=['gold', target.name, 'customer_cohorts']
    )
}}

SELECT
    DATE_TRUNC('month', registration_date) as cohort_month,
    COUNT(DISTINCT customer_id) as cohort_size,
    AVG(total_revenue) as avg_customer_value,
    AVG(total_orders) as avg_orders_per_customer
FROM {{ ref('customer_metrics') }}
GROUP BY 1
ORDER BY 1 DESC
