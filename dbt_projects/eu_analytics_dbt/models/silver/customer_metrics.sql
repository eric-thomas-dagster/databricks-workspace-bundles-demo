-- Customer metrics aggregating bronze layer data (EU region, GDPR-compliant)
-- Depends on: raw_customer_data_eu, raw_sales_orders_eu

{{ config(
    materialized='incremental',
    unique_key='customer_id',
    tags=['silver', 'eu', 'customer_analytics', 'gdpr']
) }}

SELECT
    c.customer_id,
    c.customer_name,
    c.email,
    c.customer_since_date,
    COUNT(DISTINCT s.order_id) as total_orders,
    SUM(s.order_amount) as lifetime_value,
    MAX(s.order_date) as last_order_date,
    MIN(s.order_date) as first_order_date,
    CURRENT_TIMESTAMP() as updated_at
FROM {{ source('dagster', 'raw_customer_data_eu') }} c
LEFT JOIN {{ source('dagster', 'raw_sales_orders_eu') }} s
    ON c.customer_id = s.customer_id
GROUP BY
    c.customer_id,
    c.customer_name,
    c.email,
    c.customer_since_date
