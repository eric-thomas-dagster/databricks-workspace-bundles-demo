"""
Schedule definitions for Databricks Multi-Workspace & Asset Bundles Demo.

Defines schedules for hourly ETL, daily analytics, dbt transformations,
global consolidation, and weekly full refresh.
"""

from dagster import DefaultScheduleStatus, ScheduleDefinition

from .jobs import (
    end_to_end_job,
    eu_analytics_job,
    eu_dbt_job,
    eu_etl_job,
    global_consolidation_job,
    us_analytics_job,
    us_dbt_job,
    us_etl_job,
)


# ========================================
# Hourly ETL Schedules
# ========================================

us_etl_schedule = ScheduleDefinition(
    name="us_etl_hourly",
    job=us_etl_job,
    cron_schedule="0 * * * *",  # Every hour at minute 0
    default_status=DefaultScheduleStatus.RUNNING,
    description="Runs US ETL pipeline every hour to extract fresh data from source systems",
    tags={
        "schedule_type": "etl",
        "region": "US",
    },
)

eu_etl_schedule = ScheduleDefinition(
    name="eu_etl_hourly",
    job=eu_etl_job,
    cron_schedule="0 * * * *",  # Every hour at minute 0
    default_status=DefaultScheduleStatus.RUNNING,
    description="Runs EU ETL pipeline every hour to extract fresh data from source systems",
    tags={
        "schedule_type": "etl",
        "region": "EU",
    },
)


# ========================================
# Daily Analytics Schedules
# ========================================

us_analytics_schedule = ScheduleDefinition(
    name="us_analytics_daily",
    job=us_analytics_job,
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    default_status=DefaultScheduleStatus.RUNNING,
    description="Runs US analytics pipeline daily to refresh dashboards and reports",
    tags={
        "schedule_type": "analytics",
        "region": "US",
    },
)

eu_analytics_schedule = ScheduleDefinition(
    name="eu_analytics_daily",
    job=eu_analytics_job,
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    default_status=DefaultScheduleStatus.RUNNING,
    description="Runs EU analytics pipeline daily to refresh dashboards and reports",
    tags={
        "schedule_type": "analytics",
        "region": "EU",
    },
)


# ========================================
# Daily Global Consolidation Schedule
# ========================================

global_consolidation_schedule = ScheduleDefinition(
    name="global_consolidation_daily",
    job=global_consolidation_job,
    cron_schedule="0 4 * * *",  # Daily at 4 AM (after regional analytics)
    default_status=DefaultScheduleStatus.RUNNING,
    description="Runs global consolidation daily after regional analytics complete",
    tags={
        "schedule_type": "consolidation",
        "region": "GLOBAL",
    },
)


# ========================================
# Daily dbt Transformation Schedules
# ========================================

us_dbt_schedule = ScheduleDefinition(
    name="us_dbt_daily",
    job=us_dbt_job,
    cron_schedule="0 3 * * *",  # Daily at 3 AM (after ETL)
    default_status=DefaultScheduleStatus.RUNNING,
    description="Runs US dbt transformations daily to create customer analytics",
    tags={
        "schedule_type": "dbt",
        "region": "US",
    },
)

eu_dbt_schedule = ScheduleDefinition(
    name="eu_dbt_daily",
    job=eu_dbt_job,
    cron_schedule="0 3 * * *",  # Daily at 3 AM (after ETL)
    default_status=DefaultScheduleStatus.RUNNING,
    description="Runs EU dbt transformations daily to create customer analytics",
    tags={
        "schedule_type": "dbt",
        "region": "EU",
    },
)


# ========================================
# Weekly Full Refresh Schedule
# ========================================

weekly_full_refresh_schedule = ScheduleDefinition(
    name="weekly_full_refresh",
    job=end_to_end_job,
    cron_schedule="0 1 * * 0",  # Weekly on Sunday at 1 AM
    default_status=DefaultScheduleStatus.STOPPED,  # Manual trigger for full refresh
    description="Complete end-to-end refresh of all data across all regions (manual)",
    tags={
        "schedule_type": "full_refresh",
        "region": "ALL",
    },
)
