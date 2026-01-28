# Quick Reference Guide

Essential reference for running and understanding the demo.

## Running the Demo

### Start the Demo
```bash
./run-demo.sh
# Opens http://localhost:3000
```

### Test Individual Jobs
```bash
# Regional ETL
uv run dagster job execute -j us_etl_pipeline
uv run dagster job execute -j eu_etl_pipeline

# Regional Analytics
uv run dagster job execute -j us_analytics_pipeline
uv run dagster job execute -j eu_analytics_pipeline

# Global Consolidation
uv run dagster job execute -j global_consolidation_pipeline

# Complete End-to-End
uv run dagster job execute -j end_to_end_pipeline
```

## Orchestration Components

### Jobs (11 Total)

| Job | Selection | Purpose |
|-----|-----------|---------|
| `us_etl_pipeline` | `us_etl` group | US bronze layer extraction |
| `eu_etl_pipeline` | `eu_etl` group | EU bronze layer extraction |
| `us_analytics_pipeline` | `us_analytics` group | US silver/gold analytics |
| `eu_analytics_pipeline` | `eu_analytics` group | EU silver/gold analytics |
| `us_dbt_pipeline` | `us_dbt_analytics` group | US dbt transformations |
| `eu_dbt_pipeline` | `eu_dbt_analytics` group | EU dbt transformations |
| `global_consolidation_pipeline` | `global_analytics` group | Cross-regional consolidation |
| `external_systems_refresh` | `external_systems` group | Refresh downstream dashboards/warehouses |
| `us_regional_pipeline` | `us_etl` + `us_analytics` | Complete US pipeline |
| `eu_regional_pipeline` | `eu_etl` + `eu_analytics` | Complete EU pipeline |
| `end_to_end_pipeline` | All groups | Complete multi-region pipeline |

### Schedules (8 Total)

| Schedule | Cron | Status | Purpose |
|----------|------|--------|---------|
| `us_etl_hourly` | `0 * * * *` | Running | Hourly US ETL |
| `eu_etl_hourly` | `0 * * * *` | Running | Hourly EU ETL |
| `us_analytics_daily` | `0 2 * * *` | Running | Daily US analytics at 2 AM |
| `eu_analytics_daily` | `0 2 * * *` | Running | Daily EU analytics at 2 AM |
| `us_dbt_daily` | `0 3 * * *` | Running | Daily US dbt at 3 AM (after ETL) |
| `eu_dbt_daily` | `0 3 * * *` | Running | Daily EU dbt at 3 AM (after ETL) |
| `global_consolidation_daily` | `0 4 * * *` | Running | Daily global at 4 AM |
| `weekly_full_refresh` | `0 1 * * 0` | Stopped | Weekly Sunday refresh (manual) |

### Sensors (5 Total)

| Sensor | Type | Status | Purpose |
|--------|------|--------|---------|
| `regional_analytics_completion_sensor` | Multi-asset | Running | Triggers global when US+EU complete |
| `us_etl_completion_sensor` | Multi-asset | Stopped | Event-driven US analytics trigger |
| `eu_etl_completion_sensor` | Multi-asset | Stopped | Event-driven EU analytics trigger |
| `cross_regional_dependency_monitor` | Multi-asset | Running | Monitors pipeline health |
| `trigger_downstream_systems` | Multi-asset | Running | Auto-triggers BI dashboards when global data ready |

## Asset Groups (8 Total)

| Group | Region | Type | Asset Count | Description |
|-------|--------|------|-------------|-------------|
| `us_etl` | US | Asset Bundle | 4 | Bronze layer data ingestion |
| `us_analytics` | US | Workspace | 3 | Silver/gold analytics |
| `us_dbt_analytics` | US | dbt Project | 2 | dbt customer transformations |
| `eu_etl` | EU | Asset Bundle | 4 | Bronze layer data ingestion |
| `eu_analytics` | EU | Workspace | 3 | Silver/gold analytics |
| `eu_dbt_analytics` | EU | dbt Project | 2 | dbt customer transformations |
| `global_analytics` | Global | Workspace | 4 | Cross-regional aggregation |
| `external_systems` | External | Mock Assets | 2 | Downstream BI dashboards and warehouses |

## Environment Variables

### Demo Mode (Local Testing)
```bash
export DAGSTER_DEMO_MODE=true
# Simulates Databricks without credentials
```

### Production Mode (Real Databricks)
```bash
# US Region
export DATABRICKS_US_HOST=https://your-us-workspace.databricks.com
export DATABRICKS_US_TOKEN=your-token

# EU Region
export DATABRICKS_EU_HOST=https://your-eu-workspace.databricks.com
export DATABRICKS_EU_TOKEN=your-token

# Global Region
export DATABRICKS_GLOBAL_HOST=https://your-global-workspace.databricks.com
export DATABRICKS_GLOBAL_TOKEN=your-token
```

## Critical Architecture Note

⚠️ **Same Workspace Pattern**: This demo uses both Asset Bundle and Workspace components targeting the **same Databricks workspace** (e.g., `DATABRICKS_US_HOST`).

**Why This Works:**
- Workspace Component uses **explicit `assets_by_task_key` mapping**
- Only creates assets for explicitly mapped tasks
- Does NOT auto-discover Asset Bundle tasks
- No duplicate assets

**If you omit `assets_by_task_key`:**
- ❌ Workspace Component auto-discovers ALL tasks (including Asset Bundle tasks)
- ❌ Creates duplicate assets
- ❌ Dagster fails with "asset key defined multiple times"

## Official vs Custom Features

### Built Into dagster-databricks ✅
- `DatabricksWorkspaceComponent`
- `DatabricksAssetBundleComponent`
- `assets_by_task_key` parameter
- `databricks_filter` parameter (filter by job IDs only)

### Custom Demo Additions 🔧
- Demo mode support (`DAGSTER_DEMO_MODE` environment variable)
- Custom metadata fields (layer, region, compliance, etc.)
- `CustomDatabricksWorkspaceComponent` (subclasses official, adds demo mode)
- `CustomDatabricksAssetBundleComponent` (subclasses official, adds demo mode)

**When demo mode is disabled**, our custom components call `super().build_defs()` to use the official implementation.

## Directory Structure

```
databricks-workspace-bundles-demo/
├── README.md                       # Main documentation
├── REFERENCE.md                    # This file
├── databricks_bundles/             # Databricks bundle configs
│   ├── databricks_us_etl.yml
│   ├── databricks_eu_etl.yml
│   └── README.md
├── src/
│   └── databricks_workspace_bundles_demo/
│       ├── components/             # Custom components
│       │   ├── databricks_asset_bundle_component.py
│       │   └── databricks_workspace_component.py
│       ├── defs/                   # Component instances
│       │   ├── asset_bundle_etl_us/
│       │   ├── asset_bundle_etl_eu/
│       │   ├── workspace_us/
│       │   ├── workspace_eu/
│       │   └── workspace_global/
│       ├── definitions.py          # Loads components + orchestration
│       └── orchestration.py        # Jobs, schedules, sensors
├── pyproject.toml
└── run-demo.sh                     # Quick start script
```

## Troubleshooting

### Demo won't start
```bash
# Ensure demo mode is enabled
export DAGSTER_DEMO_MODE=true

# Reinstall dependencies
uv sync
uv pip install -e .

# Check definitions load
uv run python -c "from databricks_workspace_bundles_demo.definitions import defs; defs()"
```

### "Asset key defined multiple times" error
- ✅ Ensure `assets_by_task_key` is defined in all workspace components
- ❌ Don't omit `assets_by_task_key` when mixing patterns on same workspace

### Schedules not running
- Check schedule status in UI: http://localhost:3000/schedules
- Toggle "Running" switch to enable schedules

### Sensors not triggering
- Check sensor status in UI: http://localhost:3000/sensors
- Review sensor logs for evaluation results
- Ensure assets have been materialized at least once
