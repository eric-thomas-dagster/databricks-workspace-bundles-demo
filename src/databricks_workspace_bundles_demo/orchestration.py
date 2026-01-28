"""
Orchestration configuration for Databricks Multi-Workspace & Asset Bundles Demo.

Demonstrates Dagster's orchestration capabilities across multiple Databricks workspaces
and asset bundles with jobs, schedules, and sensors.
"""

from dagster import (
    AssetKey,
    AssetSelection,
    DefaultScheduleStatus,
    DefaultSensorStatus,
    Definitions,
    RunRequest,
    ScheduleDefinition,
    SensorEvaluationContext,
    define_asset_job,
    multi_asset_sensor,
)


# ========================================
# Regional ETL Jobs (Bronze Layer)
# ========================================

us_etl_job = define_asset_job(
    name="us_etl_pipeline",
    selection=AssetSelection.groups("us_etl"),
    description="Extract raw data from US source systems into bronze layer",
    tags={
        "region": "US",
        "layer": "bronze",
        "integration_type": "asset_bundle",
        "frequency": "hourly",
    },
)

eu_etl_job = define_asset_job(
    name="eu_etl_pipeline",
    selection=AssetSelection.groups("eu_etl"),
    description="Extract raw data from EU source systems into bronze layer",
    tags={
        "region": "EU",
        "layer": "bronze",
        "integration_type": "asset_bundle",
        "frequency": "hourly",
    },
)


# ========================================
# Regional Analytics Jobs (Silver/Gold Layers)
# ========================================

us_analytics_job = define_asset_job(
    name="us_analytics_pipeline",
    selection=AssetSelection.groups("us_analytics"),
    description="Transform US data into analytics-ready tables and dashboards",
    tags={
        "region": "US",
        "layer": "silver_gold",
        "integration_type": "workspace_job",
        "frequency": "daily",
    },
)

eu_analytics_job = define_asset_job(
    name="eu_analytics_pipeline",
    selection=AssetSelection.groups("eu_analytics"),
    description="Transform EU data into analytics-ready tables and dashboards",
    tags={
        "region": "EU",
        "layer": "silver_gold",
        "integration_type": "workspace_job",
        "frequency": "daily",
    },
)


# ========================================
# Global Consolidation Job
# ========================================

global_consolidation_job = define_asset_job(
    name="global_consolidation_pipeline",
    selection=AssetSelection.groups("global_analytics"),
    description="Consolidate US and EU data into global analytics",
    tags={
        "region": "GLOBAL",
        "layer": "gold",
        "integration_type": "workspace_job",
        "frequency": "daily",
        "cross_regional": "true",
    },
)


# ========================================
# End-to-End Jobs
# ========================================

# Complete US regional pipeline (ETL + Analytics)
us_regional_job = define_asset_job(
    name="us_regional_pipeline",
    selection=AssetSelection.groups("us_etl", "us_analytics"),
    description="Complete US data pipeline from extraction to analytics",
    tags={
        "region": "US",
        "layer": "bronze_silver_gold",
        "pipeline": "regional",
    },
)

# Complete EU regional pipeline (ETL + Analytics)
eu_regional_job = define_asset_job(
    name="eu_regional_pipeline",
    selection=AssetSelection.groups("eu_etl", "eu_analytics"),
    description="Complete EU data pipeline from extraction to analytics",
    tags={
        "region": "EU",
        "layer": "bronze_silver_gold",
        "pipeline": "regional",
    },
)

# Complete end-to-end pipeline across all regions
end_to_end_job = define_asset_job(
    name="end_to_end_pipeline",
    selection=AssetSelection.groups("us_etl", "us_analytics", "eu_etl", "eu_analytics", "global_analytics"),
    description="Complete data pipeline across US, EU, and Global workspaces",
    tags={
        "region": "ALL",
        "layer": "bronze_silver_gold",
        "pipeline": "global",
        "cross_regional": "true",
    },
)


# ========================================
# Schedules
# ========================================

# Hourly ETL schedules for both regions
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

# Daily analytics schedules
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

# Daily global consolidation schedule
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

# Weekly end-to-end refresh
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


# ========================================
# Sensors
# ========================================

@multi_asset_sensor(
    name="regional_analytics_completion_sensor",
    monitored_assets=AssetSelection.groups("us_analytics", "eu_analytics"),
    job=global_consolidation_job,
    default_status=DefaultSensorStatus.RUNNING,
    description="Triggers global consolidation when both US and EU analytics pipelines complete",
    minimum_interval_seconds=300,  # Check every 5 minutes
)
def regional_analytics_completion_sensor(context: SensorEvaluationContext):
    """
    Sensor that monitors US and EU analytics completion.
    Triggers global consolidation job when both regions have fresh data.

    This demonstrates cross-workspace orchestration where the global workspace
    waits for both regional workspaces to complete their processing.
    """
    # Get all materialization records
    records_by_key = context.latest_materialization_records_by_key()

    # Get materialization events for US analytics assets
    us_customer_360 = records_by_key.get(AssetKey("customer_360_us"))
    us_sales = records_by_key.get(AssetKey("sales_insights_us"))
    us_financial = records_by_key.get(AssetKey("financial_summary_us"))

    # Get materialization events for EU analytics assets
    eu_customer_360 = records_by_key.get(AssetKey("customer_360_eu"))
    eu_sales = records_by_key.get(AssetKey("sales_insights_eu"))
    eu_financial = records_by_key.get(AssetKey("financial_summary_eu"))

    # Check if all regional analytics assets have been materialized
    all_regional_assets = [
        us_customer_360, us_sales, us_financial,
        eu_customer_360, eu_sales, eu_financial,
    ]

    if not all(all_regional_assets):
        context.log.info("Not all regional analytics assets have been materialized yet")
        context.advance_all_cursors()
        return

    # Check if any regional assets have been updated since we last ran global consolidation
    # Get the latest materialization time across all regional assets
    latest_regional_update = max(
        record.event_log_entry.timestamp
        for record in all_regional_assets
        if record is not None
    )

    # Get latest global consolidation run
    global_customer = records_by_key.get(AssetKey("global_customer_master"))

    if global_customer is not None:
        last_global_run = global_customer.event_log_entry.timestamp

        # Only trigger if regional data is newer than global consolidation
        if latest_regional_update <= last_global_run:
            context.log.info(
                f"Global consolidation is up to date. Last regional update: {latest_regional_update}, "
                f"Last global run: {last_global_run}"
            )
            context.advance_all_cursors()
            return

    context.log.info(
        f"Regional analytics complete across US and EU. Triggering global consolidation. "
        f"Latest regional update: {latest_regional_update}"
    )

    context.advance_all_cursors()
    yield RunRequest(
        run_key=f"regional_completion_{latest_regional_update}",
        tags={
            "trigger": "regional_analytics_completion",
            "us_materialized": "true",
            "eu_materialized": "true",
        },
    )


@multi_asset_sensor(
    name="etl_completion_sensor",
    monitored_assets=AssetSelection.groups("us_etl"),
    job=us_analytics_job,
    default_status=DefaultSensorStatus.STOPPED,  # Stopped by default, schedules handle this
    description="Triggers US analytics when US ETL completes (alternative to schedule-based orchestration)",
    minimum_interval_seconds=60,
)
def us_etl_completion_sensor(context: SensorEvaluationContext):
    """
    Sensor that monitors US ETL completion and triggers US analytics.

    This demonstrates event-driven orchestration where downstream analytics
    is triggered immediately when upstream ETL completes, rather than waiting
    for a schedule.

    Note: This is stopped by default since we use schedules for regular orchestration,
    but can be enabled for event-driven workflows.
    """
    # Get all materialization records
    records_by_key = context.latest_materialization_records_by_key()

    # Get all US ETL assets
    us_etl_assets = [
        AssetKey("raw_customer_data_us"),
        AssetKey("raw_sales_orders_us"),
        AssetKey("raw_product_catalog_us"),
        AssetKey("raw_financial_transactions_us"),
    ]

    etl_records = [
        records_by_key.get(asset_key)
        for asset_key in us_etl_assets
    ]

    # Check if all ETL assets exist
    if not all(etl_records):
        context.log.info("Not all US ETL assets have been materialized yet")
        context.advance_all_cursors()
        return

    # Get the latest ETL completion time
    latest_etl_time = max(
        record.event_log_entry.timestamp
        for record in etl_records
        if record is not None
    )

    # Check if analytics has already run since this ETL completion
    us_customer_360 = records_by_key.get(AssetKey("customer_360_us"))

    if us_customer_360 is not None:
        last_analytics_run = us_customer_360.event_log_entry.timestamp
        if latest_etl_time <= last_analytics_run:
            context.log.info(
                f"Analytics already processed this ETL batch. "
                f"ETL time: {latest_etl_time}, Analytics time: {last_analytics_run}"
            )
            context.advance_all_cursors()
            return

    context.log.info(
        f"US ETL complete. Triggering analytics pipeline. ETL completion: {latest_etl_time}"
    )

    context.advance_all_cursors()
    yield RunRequest(
        run_key=f"etl_completion_{latest_etl_time}",
        tags={
            "trigger": "etl_completion",
            "region": "US",
        },
    )


@multi_asset_sensor(
    name="eu_etl_completion_sensor",
    monitored_assets=AssetSelection.groups("eu_etl"),
    job=eu_analytics_job,
    default_status=DefaultSensorStatus.STOPPED,  # Stopped by default, schedules handle this
    description="Triggers EU analytics when EU ETL completes (alternative to schedule-based orchestration)",
    minimum_interval_seconds=60,
)
def eu_etl_completion_sensor(context: SensorEvaluationContext):
    """
    Sensor that monitors EU ETL completion and triggers EU analytics.

    This demonstrates event-driven orchestration where downstream analytics
    is triggered immediately when upstream ETL completes, rather than waiting
    for a schedule.

    Note: This is stopped by default since we use schedules for regular orchestration,
    but can be enabled for event-driven workflows.
    """
    # Get all materialization records
    records_by_key = context.latest_materialization_records_by_key()

    # Get all EU ETL assets
    eu_etl_assets = [
        AssetKey("raw_customer_data_eu"),
        AssetKey("raw_sales_orders_eu"),
        AssetKey("raw_product_catalog_eu"),
        AssetKey("raw_financial_transactions_eu"),
    ]

    etl_records = [
        records_by_key.get(asset_key)
        for asset_key in eu_etl_assets
    ]

    # Check if all ETL assets exist
    if not all(etl_records):
        context.log.info("Not all EU ETL assets have been materialized yet")
        context.advance_all_cursors()
        return

    # Get the latest ETL completion time
    latest_etl_time = max(
        record.event_log_entry.timestamp
        for record in etl_records
        if record is not None
    )

    # Check if analytics has already run since this ETL completion
    eu_customer_360 = records_by_key.get(AssetKey("customer_360_eu"))

    if eu_customer_360 is not None:
        last_analytics_run = eu_customer_360.event_log_entry.timestamp
        if latest_etl_time <= last_analytics_run:
            context.log.info(
                f"Analytics already processed this ETL batch. "
                f"ETL time: {latest_etl_time}, Analytics time: {last_analytics_run}"
            )
            context.advance_all_cursors()
            return

    context.log.info(
        f"EU ETL complete. Triggering analytics pipeline. ETL completion: {latest_etl_time}"
    )

    context.advance_all_cursors()
    yield RunRequest(
        run_key=f"etl_completion_{latest_etl_time}",
        tags={
            "trigger": "etl_completion",
            "region": "EU",
        },
    )


@multi_asset_sensor(
    name="cross_regional_dependency_monitor",
    monitored_assets=AssetSelection.groups("us_analytics", "eu_analytics", "global_analytics"),
    default_status=DefaultSensorStatus.RUNNING,
    description="Monitors cross-regional dependencies and logs status for visibility",
    minimum_interval_seconds=600,  # Check every 10 minutes
)
def cross_regional_dependency_monitor(context: SensorEvaluationContext):
    """
    Monitoring sensor that tracks the status of cross-regional dependencies.

    This sensor doesn't trigger jobs, but provides visibility into the state
    of the multi-region data pipeline. Useful for monitoring and alerting.
    """
    # Get all materialization records
    records_by_key = context.latest_materialization_records_by_key()

    # Define the dependency graph
    dependencies = {
        "global_customer_master": ["customer_360_us", "customer_360_eu"],
        "global_sales_insights": ["sales_insights_us", "sales_insights_eu", "global_customer_master"],
        "global_financial_summary": ["financial_summary_us", "financial_summary_eu"],
        "cross_regional_analysis": ["sales_insights_us", "sales_insights_eu", "customer_360_us", "customer_360_eu"],
    }

    status_report = []

    for global_asset, upstream_assets in dependencies.items():
        # Check if all upstream assets are materialized
        upstream_records = [
            records_by_key.get(AssetKey(asset))
            for asset in upstream_assets
        ]

        all_upstream_ready = all(upstream_records)

        # Get global asset status
        global_record = records_by_key.get(AssetKey(global_asset))

        if all_upstream_ready and global_record:
            # Check if global asset is stale
            latest_upstream = max(
                record.event_log_entry.timestamp
                for record in upstream_records
                if record is not None
            )
            global_time = global_record.event_log_entry.timestamp

            is_stale = latest_upstream > global_time
            status = "STALE" if is_stale else "UP_TO_DATE"
        elif all_upstream_ready and not global_record:
            status = "READY_TO_MATERIALIZE"
        else:
            status = "WAITING_FOR_UPSTREAM"

        status_report.append(f"{global_asset}: {status}")

    context.log.info("Cross-regional dependency status:\n" + "\n".join(status_report))

    # Advance cursor to mark these events as processed
    context.advance_all_cursors()

    # Don't yield any RunRequests - this is monitoring only


# ========================================
# Orchestration Definitions
# ========================================

orchestration_defs = Definitions(
    jobs=[
        # Regional jobs
        us_etl_job,
        eu_etl_job,
        us_analytics_job,
        eu_analytics_job,
        global_consolidation_job,
        # End-to-end jobs
        us_regional_job,
        eu_regional_job,
        end_to_end_job,
    ],
    schedules=[
        # Hourly ETL
        us_etl_schedule,
        eu_etl_schedule,
        # Daily analytics
        us_analytics_schedule,
        eu_analytics_schedule,
        # Daily global consolidation
        global_consolidation_schedule,
        # Weekly full refresh
        weekly_full_refresh_schedule,
    ],
    sensors=[
        regional_analytics_completion_sensor,
        us_etl_completion_sensor,
        eu_etl_completion_sensor,
        cross_regional_dependency_monitor,
    ],
)
