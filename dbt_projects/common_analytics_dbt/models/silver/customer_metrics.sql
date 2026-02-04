-- Customer metrics aggregating bronze layer data
-- Works for both US and EU regions based on target

{{
    config(
        materialized='incremental',
        unique_key='customer_id',
        tags=['silver', target.name, 'customer_analytics']
    )
}}

{% set region = target.name %}

SELECT
    c.customer_id,
    c.customer_name,
    c.email,
    c.customer_since_date as registration_date,
    COUNT(DISTINCT s.order_id) as total_orders,
    SUM(s.order_amount) as total_revenue,
    MAX(s.order_date) as last_order_date,
    MIN(s.order_date) as first_order_date,
    CURRENT_TIMESTAMP() as updated_at
FROM {{ source('dagster', 'raw_customer_data_' ~ region) }} c
LEFT JOIN {{ source('dagster', 'raw_sales_orders_' ~ region) }} s
    ON c.customer_id = s.customer_id
GROUP BY
    c.customer_id,
    c.customer_name,
    c.email,
    c.customer_since_date
