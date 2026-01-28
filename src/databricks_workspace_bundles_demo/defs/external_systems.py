"""
Mock external systems that are triggered based on Databricks job completion.

Represents external BI dashboards, data warehouses, or other downstream systems
that need to refresh when upstream Databricks processing completes.

This demonstrates how to trigger external systems in response to Databricks job
completion, a common pattern for customers with multi-system architectures.
"""

import os
from dagster import (
    asset,
    AssetExecutionContext,
    AssetKey,
    AutomationCondition,
    MaterializeResult,
)


@asset(
    key=["dashboards", "executive_dashboard"],
    group_name="external_systems",
    deps=[
        AssetKey(["gold", "global", "customer_master"]),
        AssetKey(["gold", "global", "sales_insights"]),
        AssetKey(["gold", "global", "financial_summary"]),
        AssetKey(["gold", "global", "cross_regional_analysis"]),
    ],
    automation_condition=AutomationCondition.eager(),
    description="Executive dashboard that displays global consolidated metrics. "
                "Auto-refreshes when global consolidation pipeline completes (Declarative Automation).",
    compute_kind="tableau",  # Shows Tableau icon in UI
    metadata={
        "dashboard_url": "https://tableau.example.com/executive-dashboard",
        "refresh_type": "full",
        "downstream_system": "Tableau Server",
        "automation": "eager - materializes when all upstream assets are fresh",
    }
)
def executive_dashboard(
    context: AssetExecutionContext,
) -> MaterializeResult:
    """
    Mock executive dashboard asset representing an external BI tool.

    In reality, this might:
    - Call Tableau's REST API to refresh extracts
    - Trigger Snowflake materialized view refresh
    - Update Looker cache
    - Refresh Power BI dataset

    Depends on all global consolidation assets to ensure data is ready.
    """
    demo_mode = os.getenv("DAGSTER_DEMO_MODE", "false").lower() == "true"

    if demo_mode:
        context.log.info("[DEMO MODE] Simulating executive dashboard refresh")
        context.log.info("In production, this would:")
        context.log.info("  - Call Tableau REST API: POST /api/3.x/sites/{site-id}/workbooks/{workbook-id}/refresh")
        context.log.info("  - Refresh Snowflake materialized views")
        context.log.info("  - Update BI tool caches")
        context.log.info("  - Send notification to business stakeholders")
    else:
        # Real implementation would call external API
        # Example:
        # import requests
        # response = requests.post(
        #     "https://tableau.example.com/api/refresh",
        #     json={"workbook_id": "executive-dashboard"}
        # )
        context.log.info("Triggering real dashboard refresh via API")

    return MaterializeResult(
        metadata={
            "refresh_timestamp": context.run.run_id,
            "data_sources_updated": 3,
            "demo_mode": demo_mode,
            "dashboard_views": 156,  # Mock metric
            "last_refresh_duration_seconds": 8.3,  # Mock metric
        }
    )


@asset(
    key=["data_warehouse", "snowflake_sync"],
    group_name="external_systems",
    deps=[
        AssetKey(["gold", "global", "customer_master"]),
        AssetKey(["gold", "global", "sales_insights"]),
        AssetKey(["gold", "global", "financial_summary"]),
        AssetKey(["gold", "global", "cross_regional_analysis"]),
    ],
    automation_condition=AutomationCondition.eager(),
    description="Data warehouse sync job that copies global data to external warehouse. "
                "Auto-triggers after global consolidation completes (Declarative Automation).",
    compute_kind="snowflake",  # Shows Snowflake icon in UI
    metadata={
        "warehouse": "Snowflake",
        "sync_type": "incremental",
        "target_database": "ANALYTICS_DW",
        "automation": "eager - materializes when all upstream assets are fresh",
    }
)
def data_warehouse_sync(
    context: AssetExecutionContext,
) -> MaterializeResult:
    """
    Mock data warehouse sync representing external data movement.

    In reality, this might:
    - Use Fivetran/Airbyte to sync data
    - Run Snowflake COPY INTO commands
    - Trigger dbt Cloud job in external warehouse
    - Update data catalog metadata

    Depends on all global consolidation assets to ensure data is ready.
    """
    demo_mode = os.getenv("DAGSTER_DEMO_MODE", "false").lower() == "true"

    if demo_mode:
        context.log.info("[DEMO MODE] Simulating data warehouse sync")
        context.log.info("In production, this would:")
        context.log.info("  - Sync 3 tables to Snowflake (global_customer, global_sales, global_financial)")
        context.log.info("  - Run incremental COPY INTO commands")
        context.log.info("  - Trigger downstream dbt Cloud job")
        context.log.info("  - Update data catalog metadata (Alation, Collibra, etc.)")
        context.log.info("  - Send completion notification to data engineering team")
    else:
        # Real implementation would call external API
        # Example:
        # import snowflake.connector
        # conn = snowflake.connector.connect(...)
        # cursor = conn.cursor()
        # cursor.execute("COPY INTO target_table FROM ...")
        context.log.info("Triggering real warehouse sync")

    return MaterializeResult(
        metadata={
            "tables_synced": ["global_customer", "global_sales", "global_financial"],
            "rows_copied": 150000,
            "bytes_transferred": 45_000_000,
            "demo_mode": demo_mode,
            "sync_duration_seconds": 12.7,  # Mock metric
        }
    )
