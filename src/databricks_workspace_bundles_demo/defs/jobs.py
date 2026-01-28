"""
Job definitions for Databricks Multi-Workspace & Asset Bundles Demo.

Defines jobs for regional ETL, analytics, dbt transformations, global consolidation,
and external systems refresh across multiple Databricks workspaces.
"""

from dagster import AssetSelection, define_asset_job


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
# dbt Transformation Jobs
# ========================================

us_dbt_job = define_asset_job(
    name="us_dbt_pipeline",
    selection=AssetSelection.groups("us_dbt_analytics"),
    description="US dbt transformations for customer analytics",
    tags={
        "region": "US",
        "layer": "silver_gold",
        "integration_type": "dbt",
        "frequency": "daily",
    },
)

eu_dbt_job = define_asset_job(
    name="eu_dbt_pipeline",
    selection=AssetSelection.groups("eu_dbt_analytics"),
    description="EU dbt transformations for customer analytics",
    tags={
        "region": "EU",
        "layer": "silver_gold",
        "integration_type": "dbt",
        "frequency": "daily",
    },
)


# ========================================
# External Systems Jobs
# ========================================

external_systems_job = define_asset_job(
    name="external_systems_refresh",
    selection=AssetSelection.groups("external_systems"),
    description="Refresh external dashboards and data warehouse sync",
    tags={
        "integration_type": "external_bi",
        "frequency": "event_driven",
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
