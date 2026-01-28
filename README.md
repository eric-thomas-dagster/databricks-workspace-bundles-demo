# Databricks Multi-Workspace & Asset Bundles Demo

This demo showcases Dagster's integration with multiple Databricks workspaces and asset bundles, demonstrating how to orchestrate complex data workflows across regional boundaries with unified lineage tracking.

## Overview

This project demonstrates how Dagster orchestrates complex data workflows across regions:

- **Regional Workspaces**: Separate US and EU Databricks workspaces for data sovereignty and compliance
- **Regional Asset Bundles**: ETL pipelines deployed to each region (US and EU) for local data ingestion
- **Global Workspace**: Central workspace that aggregates data from regional workspaces
- **Cross-Regional Dependencies**: Global assets depend on regional assets with unified lineage tracking
- **Hybrid Architecture**: Asset bundles for ETL (IaC), workspace components for analytics (job discovery)
- **Conflict-Free Design**: Clear task key naming conventions prevent conflicts when both patterns target the same workspace
- **Demo Mode**: Run the entire demo locally without Databricks credentials

> **⚠️ Critical Architecture Note**: This demo uses both Asset Bundle and Workspace components targeting the **same Databricks workspace** (e.g., `DATABRICKS_US_HOST`). This works safely because:
> 1. The Workspace Component uses **explicit `assets_by_task_key` mapping**
> 2. It only creates assets for explicitly mapped tasks (e.g., `us_customer_analytics_task`)
> 3. It does NOT create assets for Asset Bundle tasks (e.g., `extract_us_*`), even though it discovers them
>
> **If you omit `assets_by_task_key`**, the Workspace Component will auto-discover ALL tasks (including Asset Bundle tasks) and create duplicate assets, causing Dagster to fail.
>
> See the "Critical Architecture Note" section in [REFERENCE.md](REFERENCE.md) for complete details on avoiding conflicts.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Dagster Orchestration                              │
│                   (Unified lineage across regions)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   US REGION          │  │   EU REGION          │  │   GLOBAL REGION      │
│ us.databricks.com    │  │ eu.databricks.com    │  │ global.databricks... │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
          │                           │                           │
   ┌──────┴──────┐             ┌──────┴──────┐                   │
   ▼             ▼             ▼             ▼                   │
┌────────┐  ┌────────┐   ┌────────┐  ┌────────┐                │
│US ETL  │  │US      │   │EU ETL  │  │EU      │                │
│Bundle  │  │Workspace│  │Bundle  │  │Workspace│                │
│(Asset  │  │(Jobs)  │   │(Asset  │  │(Jobs)  │                │
│Bundle) │  │        │   │Bundle) │  │        │                │
└────────┘  └────────┘   └────────┘  └────────┘                │
    │           │             │           │                     │
    ▼           ▼             ▼           ▼                     │
┌─────────────────┐     ┌─────────────────┐                    │
│ Bronze (US)     │     │ Bronze (EU)     │                    │
│ - Customers US  │     │ - Customers EU  │                    │
│ - Sales US      │     │ - Sales EU      │                    │
│ - Products US   │     │ - Products EU   │                    │
│ - Financials US │     │ - Financials EU │                    │
└─────────────────┘     └─────────────────┘                    │
    │           │             │           │                     │
    ▼           ▼             ▼           ▼                     │
┌─────────────────┐     ┌─────────────────┐                    │
│ Silver/Gold(US) │     │ Silver/Gold(EU) │                    │
│ - Customer360US │     │ - Customer360EU │                    │
│ - SalesInsightsUS│    │ - SalesInsightsEU│                   │
│ - FinSummary US │     │ - FinSummary EU │                    │
└─────────────────┘     └─────────────────┘                    │
    │                           │                               │
    └───────────────┬───────────┘                               │
                    │                                           │
                    │   Cross-Regional Dependencies             │
                    └───────────────────────────────────────────┘
                                                                │
                                                                ▼
                                                    ┌──────────────────────┐
                                                    │ Global Workspace     │
                                                    │ (Job Discovery)      │
                                                    └──────────────────────┘
                                                                │
                                                                ▼
                                                    ┌──────────────────────┐
                                                    │ Gold (Global)        │
                                                    │ - Global Customer    │
                                                    │ - Global Sales       │
                                                    │ - Global Financials  │
                                                    │ - Cross-Regional     │
                                                    │   Analysis           │
                                                    └──────────────────────┘
```

## Key Features

### 1. Regional Multi-Workspace Architecture

This demo shows **regional data processing** with separate workspaces per region:

**US Region** (`us.databricks.com`):
- **US ETL Bundle** (`databricks_bundles/databricks_us_etl.yml`): Data ingestion from US sources (Salesforce, NetSuite)
  - 4 bronze layer assets: US customers, sales, products, financials
  - Deployed as asset bundle (infrastructure as code)
- **US Analytics Workspace**: Regional analytics and reporting
  - 3 silver/gold assets: US customer 360, sales insights, financial summary
  - Uses workspace pattern (job discovery)

**EU Region** (`eu.databricks.com`):
- **EU ETL Bundle** (`databricks_bundles/databricks_eu_etl.yml`): Data ingestion from EU sources (SAP, Salesforce EU)
  - 4 bronze layer assets: EU customers, sales, products, financials
  - Deployed as asset bundle (infrastructure as code)
- **EU Analytics Workspace**: Regional analytics and reporting
  - 3 silver/gold assets: EU customer 360, sales insights, financial summary
  - Uses workspace pattern (job discovery)
  - GDPR-compliant processing

**Global Region** (`global.databricks.com`):
- **Global Analytics Workspace**: Cross-regional aggregation and analysis
  - 4 gold assets: global customer master, global sales, global financials, cross-regional analysis
  - Depends on outputs from both US and EU regions
  - Uses workspace pattern (job discovery)

### 2. Cross-Regional Dependencies

The demo includes realistic cross-regional dependencies:
- **Global Customer Master** depends on `customer_360_us` AND `customer_360_eu`
- **Global Sales Insights** depends on `sales_insights_us` AND `sales_insights_eu`
- **Global Financial Summary** depends on `financial_summary_us` AND `financial_summary_eu`
- **Cross-Regional Analysis** depends on multiple US and EU assets
- Demonstrates unified lineage tracking across regional boundaries

### 3. Data Sovereignty & Compliance

- **US Region**: SOX and GAAP compliance, US data stays in US workspace
- **EU Region**: GDPR and IFRS compliance, EU data stays in EU workspace
- **Global Region**: Consolidated reporting with proper data governance

### 4. Asset Groups for Organization

Assets are organized into groups by workspace for easier lineage navigation:

| Group | Region | Type | Assets | Description |
|-------|--------|------|--------|-------------|
| **us_etl** | US | Asset Bundle | 4 | Bronze layer data ingestion |
| **us_analytics** | US | Workspace | 3 | Silver/gold analytics |
| **us_dbt_analytics** | US | dbt | 2 | dbt customer transformations |
| **eu_etl** | EU | Asset Bundle | 4 | Bronze layer data ingestion |
| **eu_analytics** | EU | Workspace | 3 | Silver/gold analytics |
| **eu_dbt_analytics** | EU | dbt | 2 | dbt customer transformations |
| **global_analytics** | Global | Workspace | 4 | Cross-regional aggregation |
| **external_systems** | External | Mock | 2 | Downstream BI dashboards and warehouses |

**Benefits:**
- **Visual Organization**: Lineage graph clearly shows regional boundaries
- **Easy Navigation**: Filter by group to focus on specific workspaces
- **Cross-Regional Visibility**: See exactly which assets cross regional boundaries
- **Team Ownership**: Each group maps to a specific team and workspace

### 5. Jobs, Schedules, and Sensors

The demo includes comprehensive orchestration showcasing Dagster's coordination capabilities:

**11 Jobs** demonstrating different orchestration patterns:
- **Regional ETL Jobs**: `us_etl_pipeline`, `eu_etl_pipeline` (asset bundle execution)
- **Regional Analytics Jobs**: `us_analytics_pipeline`, `eu_analytics_pipeline` (workspace jobs)
- **dbt Transformation Jobs**: `us_dbt_pipeline`, `eu_dbt_pipeline` (dbt model execution)
- **External Systems Job**: `external_systems_refresh` (downstream BI/warehouse triggers)
- **Global Consolidation**: `global_consolidation_pipeline` (cross-regional dependencies)
- **End-to-End Jobs**: `us_regional_pipeline`, `eu_regional_pipeline`, `end_to_end_pipeline`

**8 Schedules** for time-based orchestration:
- **Hourly ETL**: `us_etl_hourly`, `eu_etl_hourly` (keep bronze layer fresh)
- **Daily Analytics**: `us_analytics_daily`, `eu_analytics_daily` (refresh dashboards)
- **Daily dbt**: `us_dbt_daily`, `eu_dbt_daily` (run dbt transformations)
- **Daily Global**: `global_consolidation_daily` (consolidate regional data)
- **Weekly Refresh**: `weekly_full_refresh` (complete system backfill)

**5 Sensors** for event-driven orchestration:
- **`regional_analytics_completion_sensor`**: Multi-asset sensor that triggers global consolidation when both US and EU analytics complete (demonstrates cross-workspace coordination)
- **`us_etl_completion_sensor`**: Triggers US analytics immediately when US ETL completes (demonstrates low-latency event-driven pattern)
- **`eu_etl_completion_sensor`**: Triggers EU analytics immediately when EU ETL completes (demonstrates low-latency event-driven pattern)
- **`cross_regional_dependency_monitor`**: Monitoring sensor that tracks cross-regional pipeline health without triggering jobs
- **`trigger_downstream_systems`**: Automatically triggers external dashboards and warehouses when global consolidation completes

**Orchestration Patterns:**
- Cross-workspace coordination across US, EU, and Global
- Schedule-based (hourly ETL, daily analytics) + event-driven (sensors)
- Multi-region dependencies with automatic triggering

→ **See [REFERENCE.md](REFERENCE.md) for complete job/schedule/sensor details and usage examples.**

### 6. Demo Mode

All components support demo mode via the `DAGSTER_DEMO_MODE` environment variable:
- Run the demo without Databricks credentials
- Test locally with simulated job execution
- Components properly subclass official dagster-databricks components
- Understand cross-regional architecture without infrastructure

### 7. dbt Transformations

Regional dbt projects for customer analytics demonstrating dbt integration with Databricks:

**US dbt Analytics** (`dbt_projects/us_analytics_dbt/`):
- **us_customer_metrics** (Silver): Customer lifetime value and order history aggregated from bronze layer
- **us_customer_cohorts** (Gold): Customer segmentation and cohort analysis for retention tracking

**EU dbt Analytics** (`dbt_projects/eu_analytics_dbt/`):
- Same dbt models as US (customer_metrics, customer_cohorts) with GDPR-compliant processing
- Separate dbt project maintains data sovereignty
- Assets prefixed with `eu_` to avoid naming conflicts

**Integration Pattern**:
- Uses `DbtProjectComponent` with demo mode support and custom translation
- Translation config adds regional prefixes (`us_` and `eu_`) to dbt model names
- Each dbt model becomes a Dagster asset with automatic lineage tracking
- Dependencies flow from bronze assets → dbt silver → dbt gold
- Executes via PipesDatabricksClient on Databricks (or simulated in demo mode)

**Benefits**:
- **Unified Lineage**: dbt models appear alongside Databricks assets in the same DAG
- **Flexible Tooling**: Combine dbt's SQL-based transformations with Databricks notebooks
- **Team Productivity**: dbt teams can use familiar workflows while Dagster handles orchestration

### 8. Downstream System Triggering

Demonstrates triggering external systems when Databricks processing completes, a common pattern for multi-system architectures:

**Mock External Systems**:
- **Executive Dashboard**: Tableau-style BI dashboard that refreshes when global consolidation completes
- **Data Warehouse Sync**: Snowflake-style data copy triggered after global processing

**How It Works**:
- `trigger_downstream_systems` sensor monitors all global consolidation assets
- When all global assets materialize, sensor automatically triggers downstream refreshes
- External systems appear in lineage graph as natural asset dependencies
- Shows event-driven pattern without requiring real external services

**Pattern**: This demonstrates how customers trigger downstream systems (BI dashboards, data warehouses, reporting tools) based on Databricks job completion. In production, this would call real APIs (Tableau REST API, Snowflake procedures, Looker refresh endpoints, etc.).

## Quick Start

### Prerequisites

- Python 3.10+
- uv package manager

### Option 1: Quick Start Script (Recommended)

```bash
cd my-demos/databricks-workspace-bundles-demo
./run-demo.sh
```

This script will:
1. Set all required environment variables for demo mode
2. Validate the configuration
3. Start the Dagster development server
4. Open http://localhost:3000 to view the UI

### Option 2: Manual Installation

1. Navigate to the demo directory:
   ```bash
   cd my-demos/databricks-workspace-bundles-demo
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables:
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env and set DAGSTER_DEMO_MODE=true for demo mode
   # Or export directly:
   export DAGSTER_DEMO_MODE=true
   export DATABRICKS_ETL_HOST="https://etl.databricks.com"
   export DATABRICKS_ETL_TOKEN="demo-token-etl"
   export DATABRICKS_ANALYTICS_HOST="https://analytics.databricks.com"
   export DATABRICKS_ANALYTICS_TOKEN="demo-token-analytics"
   export DATABRICKS_FINANCE_HOST="https://finance.databricks.com"
   export DATABRICKS_FINANCE_TOKEN="demo-token-finance"
   ```

4. Validate the configuration:
   ```bash
   uv run dg check defs
   ```

5. Start Dagster:
   ```bash
   uv run dg dev
   ```

6. Open the Dagster UI at `http://localhost:3000`

7. In the UI, navigate to Assets to see the lineage graph with asset groups organized by region/workspace

## Assets Overview (26 Total Assets)

### US Region (9 Assets)

**US ETL Bundle** (Bronze Layer - 4 Assets):
| Asset | Source Systems | Description |
|-------|---------------|-------------|
| `raw_customer_data_us` | Salesforce US, NetSuite US | US customer master data from CRM and ERP |
| `raw_sales_orders_us` | ERP US, E-commerce Platform US | US sales order headers and line items |
| `raw_product_catalog_us` | PIM System US | US product master with SKUs and pricing |
| `raw_financial_transactions_us` | NetSuite US | US general ledger transactions (SOX, GAAP compliant) |

**US Analytics Workspace** (Silver/Gold Layer - 3 Assets):
| Asset | Dependencies | Description |
|-------|--------------|-------------|
| `customer_360_us` | raw_customer_data_us, raw_sales_orders_us | US customer 360 view (silver) |
| `sales_insights_us` | customer_360_us, raw_product_catalog_us | US sales insights and dashboards (gold) |
| `financial_summary_us` | raw_financial_transactions_us, sales_insights_us | US financial summary with P&L (gold) |

**US dbt Analytics** (dbt Silver/Gold Layer - 2 Assets):
| Asset | Type | Dependencies | Description |
|-------|------|--------------|-------------|
| `us_customer_metrics` | dbt (silver) | raw_customer_data_us, raw_sales_orders_us | Customer lifetime value and order history |
| `us_customer_cohorts` | dbt (gold) | us_customer_metrics | Customer segmentation and cohort analysis |

### EU Region (9 Assets)

**EU ETL Bundle** (Bronze Layer - 4 Assets):
| Asset | Source Systems | Description |
|-------|---------------|-------------|
| `raw_customer_data_eu` | Salesforce EU, SAP ECC | EU customer master data (GDPR-compliant) |
| `raw_sales_orders_eu` | SAP ECC, E-commerce Platform EU | EU sales order data |
| `raw_product_catalog_eu` | PIM System EU | EU product master with SKUs and pricing |
| `raw_financial_transactions_eu` | SAP FI/CO | EU general ledger transactions (IFRS, GDPR compliant) |

**EU Analytics Workspace** (Silver/Gold Layer - 3 Assets):
| Asset | Dependencies | Description |
|-------|--------------|-------------|
| `customer_360_eu` | raw_customer_data_eu, raw_sales_orders_eu | EU customer 360 view with GDPR compliance (silver) |
| `sales_insights_eu` | customer_360_eu, raw_product_catalog_eu | EU sales insights and dashboards (gold) |
| `financial_summary_eu` | raw_financial_transactions_eu, sales_insights_eu | EU financial summary with P&L (gold) |

**EU dbt Analytics** (dbt Silver/Gold Layer - 2 Assets):
| Asset | Type | Dependencies | Description |
|-------|------|--------------|-------------|
| `eu_customer_metrics` | dbt (silver) | raw_customer_data_eu, raw_sales_orders_eu | Customer lifetime value and order history (GDPR-compliant) |
| `eu_customer_cohorts` | dbt (gold) | eu_customer_metrics | Customer segmentation and cohort analysis (GDPR-compliant) |

### Global Region (4 Assets)

**Global Analytics Workspace** (Gold Layer - 4 Assets with Cross-Regional Dependencies):
| Asset | Dependencies | Description |
|-------|--------------|-------------|
| `global_customer_master` | **customer_360_us, customer_360_eu** | Unified global customer master (cross-regional) |
| `global_sales_insights` | **sales_insights_us, sales_insights_eu**, global_customer_master | Consolidated global sales performance (cross-regional) |
| `global_financial_summary` | **financial_summary_us, financial_summary_eu** | Global consolidated financials with currency normalization (cross-regional) |
| `cross_regional_analysis` | **sales_insights_us, sales_insights_eu, customer_360_us, customer_360_eu** | Cross-regional performance comparison and market analysis |

### External Systems (2 Assets)

**Mock External Systems** (Triggered After Global Consolidation - 2 Assets):
| Asset | Type | Dependencies | Description |
|-------|------|--------------|-------------|
| `executive_dashboard` | External BI (Tableau) | global_customer_master, global_sales_insights, global_financial_summary | Executive dashboard refresh representing Tableau/Power BI/Looker |
| `data_warehouse_sync` | External Warehouse (Snowflake) | global_customer_master, global_sales_insights, global_financial_summary | Data warehouse sync representing Snowflake/Redshift/BigQuery |

These assets represent downstream systems that are automatically triggered when Databricks processing completes, demonstrating the pattern of event-driven external system integration.

## Component Configuration

All three teams use the same `CustomDatabricksAssetBundleComponent` pattern, which properly subclasses the official `DatabricksAssetBundleComponent`:

> **📝 Demo Mode Note**: This demo uses **custom component subclasses** (`CustomDatabricksAssetBundleComponent`, `CustomDatabricksWorkspaceComponent`, `CustomDbtProjectComponent`) to enable running the demo without real Databricks credentials via `DAGSTER_DEMO_MODE=true`. These custom components add demo mode simulation but otherwise delegate to the official Dagster components.
>
> **In a real production scenario**, you would use the official components directly:
> - `dagster_databricks.DatabricksAssetBundleComponent`
> - `dagster_databricks.DatabricksWorkspaceComponent`
> - `dagster_dbt.DbtProjectComponent`
>
> The custom components in this demo also add `databricks_workspace_host` metadata to all assets for demonstration purposes, but this is optional functionality not required for production use.

```yaml
# Example: asset_bundle_etl_us/defs.yaml
type: databricks_workspace_bundles_demo.components.CustomDatabricksAssetBundleComponent

attributes:
  # Path to bundle configuration (organized in databricks_bundles/ directory)
  databricks_config_path: "{{ project_root }}/databricks_bundles/databricks_us_etl.yml"

  # Workspace connection (uses environment variables)
  workspace:
    host: "{{ env.DATABRICKS_ANALYTICS_HOST | default('https://analytics.databricks.com') }}"
    token: "{{ env.DATABRICKS_ANALYTICS_TOKEN | default('demo-token-analytics') }}"

  # Compute configuration
  compute_config:
    is_serverless: true

  # Map Databricks task keys to Dagster asset specs
  assets_by_task_key:
    customer_analytics_task:
      - key: customer_360_view
        owners: ["analytics-team@company.com"]
        deps: [raw_customer_data, raw_sales_orders]
        description: "Comprehensive 360-degree customer view"
```

**Demo Mode**: Set `DAGSTER_DEMO_MODE=true` to enable simulation without Databricks CLI.

### Databricks Bundle Organization

All Databricks Asset Bundle configurations are organized in the `databricks_bundles/` directory, keeping them separate from Dagster code. This organization scales well for projects with dozens of asset bundles:

- **`databricks_bundles/databricks_us_etl.yml`**: US regional ETL bundle with 4 extraction tasks
- **`databricks_bundles/databricks_eu_etl.yml`**: EU regional ETL bundle with 4 extraction tasks

For larger projects, you can organize bundles by region, department, or function within this directory.

## Directory Structure

```
databricks-workspace-bundles-demo/
├── databricks_bundles/                 # Databricks Asset Bundle configurations
│   ├── databricks_us_etl.yml          # US regional ETL bundle config
│   └── databricks_eu_etl.yml          # EU regional ETL bundle config
├── src/
│   └── databricks_workspace_bundles_demo/
│       ├── components/
│       │   ├── __init__.py
│       │   ├── databricks_asset_bundle_component.py   # Bundle pattern
│       │   └── databricks_workspace_component.py      # Workspace pattern
│       ├── defs/
│       │   ├── __init__.py
│       │   ├── asset_bundle_etl_us/
│       │   │   └── defs.yaml           # US ETL bundle (Asset Bundle)
│       │   ├── asset_bundle_etl_eu/
│       │   │   └── defs.yaml           # EU ETL bundle (Asset Bundle)
│       │   ├── workspace_us/
│       │   │   └── defs.yaml           # US analytics workspace (Workspace)
│       │   ├── workspace_eu/
│       │   │   └── defs.yaml           # EU analytics workspace (Workspace)
│       │   └── workspace_global/
│       │       └── defs.yaml           # Global workspace (Workspace - cross-regional)
│       └── definitions.py
├── pyproject.toml
└── README.md
```

## Demo Talking Points

### For SAP (The Company)

1. **Regional Data Sovereignty**: Separate Databricks workspaces per region (US, EU, Global) with clear data boundaries:
   - US data stays in US workspace (SOX, GAAP compliance)
   - EU data stays in EU workspace (GDPR, IFRS compliance)
   - Global workspace aggregates for consolidated reporting

2. **Cross-Regional Orchestration**: Dagster provides unified orchestration across all regional workspaces:
   - Single control plane for US, EU, and Global workspaces
   - Complete lineage tracking across regional boundaries
   - Global analytics depend on regional outputs

3. **Hybrid Integration Per Region**: Each region uses the pattern that fits best:
   - **ETL (Asset Bundles)**: US and EU ETL deployed as bundles for infrastructure as code
   - **Analytics (Workspaces)**: US, EU, and Global analytics use job discovery pattern
   - Same bundle can deploy to multiple regions with different targets

4. **Realistic Regional Dependencies**:
   - Global customer master consolidates US and EU customer data
   - Global sales insights aggregates US and EU sales performance
   - Cross-regional analysis compares markets and identifies trends

5. **Compliance & Governance**:
   - GDPR-compliant processing in EU workspace
   - SOX/GAAP controls in US workspace
   - Unified compliance reporting at global level
   - Data classification and retention policies per region

6. **Medallion Architecture Across Regions**:
   - Bronze layer in each regional workspace (raw data stays local)
   - Silver layer for regional transformations
   - Gold layer in global workspace for consolidated metrics

### Dagster Value Props

1. **Multi-Region Orchestration**: Seamless coordination across US, EU, and Global workspaces in single deployment
2. **Cross-Regional Lineage**: Track dependencies that span regions (EU customer → Global customer master)
3. **Asset Groups for Organization**: Assets grouped by workspace (us_etl, us_analytics, eu_etl, eu_analytics, global_analytics) with visual boundaries in lineage graph
4. **Regional Autonomy**: US and EU teams manage their own workspaces independently
5. **Global Visibility**: Single UI shows all 18 assets across 3 regions with complete dependency graph
6. **Pattern Flexibility**: Asset bundles for ETL, workspaces for analytics - both patterns work together
7. **Compliance-Ready**: Region-specific metadata (GDPR, SOX, GAAP) with proper data classification

## Switching to Real Mode

To connect to actual Databricks workspaces:

1. Set `DAGSTER_DEMO_MODE=false` (or unset the variable)
2. Set environment variables with real credentials:
   ```bash
   export DAGSTER_DEMO_MODE=false
   export DATABRICKS_ETL_HOST="https://your-etl-workspace.databricks.com"
   export DATABRICKS_ETL_TOKEN="your-real-token"
   export DATABRICKS_ANALYTICS_HOST="https://your-analytics-workspace.databricks.com"
   export DATABRICKS_ANALYTICS_TOKEN="your-real-token"
   export DATABRICKS_FINANCE_HOST="https://your-finance-workspace.databricks.com"
   export DATABRICKS_FINANCE_TOKEN="your-real-token"
   ```
3. Ensure your Databricks workspaces have matching job task keys (or configure filters in YAML)
4. Update the `databricks.yml` file with your bundle configuration
5. Restart Dagster

## Viewing in the Dagster UI

Once you start the Dagster UI (`uv run dg dev`), you'll see:

### Asset Groups (Organization)

1. **View Asset Groups**: Navigate to Assets → Groups to see the 5 regional groups
2. **Filter by Group**: Click on a group name to see only assets in that region/workspace
3. **Lineage Graph**: The asset graph visually separates assets by group, making regional boundaries clear
4. **Cross-Regional Dependencies**: Dependencies that cross group boundaries (e.g., global_analytics → us_analytics) are clearly visible

**Example**: Viewing the `global_customer_master` asset will show its dependencies on both `customer_360_us` (us_analytics group) and `customer_360_eu` (eu_analytics group), making the cross-regional aggregation immediately obvious.

### Need More Details?

→ **See [REFERENCE.md](REFERENCE.md)** for:
- Complete list of all jobs, schedules, and sensors
- Environment variables and configuration
- Troubleshooting guide

## Testing the Demo

### Test Asset Materialization

```bash
# Test a bronze layer asset (Asset Bundle)
export DAGSTER_DEMO_MODE=true
uv run dagster asset materialize -m databricks_workspace_bundles_demo.definitions --select raw_customer_data

# Test a silver layer asset (Analytics Workspace)
uv run dagster asset materialize -m databricks_workspace_bundles_demo.definitions --select customer_360_view

# Test cross-workspace dependencies (Finance depends on Analytics)
uv run dagster asset materialize -m databricks_workspace_bundles_demo.definitions --select ar_aging_analysis+
```

### Verify All Assets Load

```bash
# List all assets (should show 13 total)
uv run dagster asset list -m databricks_workspace_bundles_demo.definitions

# Expected assets:
# - 7 bronze layer assets (from Asset Bundle)
# - 3 analytics assets (from Analytics Workspace)
# - 3 finance assets (from Finance Workspace)
```

## Troubleshooting

### Validation Errors

```bash
# Check all definitions load correctly
uv run dg check defs

# If you get environment variable errors, ensure all required vars are set
env | grep DATABRICKS
```

### Missing Environment Variables

If you see `pydantic_core._pydantic_core.ValidationError` with `Input should be a valid string`, make sure all required environment variables are set:

```bash
export DAGSTER_DEMO_MODE=true
export DATABRICKS_ETL_HOST='https://etl.databricks.com'
export DATABRICKS_ETL_TOKEN='demo-token-etl'
export DATABRICKS_ANALYTICS_HOST='https://analytics.databricks.com'
export DATABRICKS_ANALYTICS_TOKEN='demo-token-analytics'
export DATABRICKS_FINANCE_HOST='https://finance.databricks.com'
export DATABRICKS_FINANCE_TOKEN='demo-token-finance'
```

### View Component Tree

```bash
uv run dg list components
```

## Next Steps

- Add sensors to trigger on S3 file arrivals
- Implement asset checks for data quality
- Add schedules for nightly/monthly processing
- Connect to real data sources (Salesforce, NetSuite, etc.)
- Deploy to Dagster Cloud for production
- Add data observability and alerting

## References

- [Dagster Databricks Integration](https://docs.dagster.io/integrations/libraries/databricks/dagster-databricks)
- [Creating Dagster Components](https://docs.dagster.io/guides/build/components/creating-new-components)
- [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
