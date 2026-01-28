# dbt Projects

This directory contains dbt projects for regional data transformations within the Databricks Multi-Workspace demo.

## Structure

```
dbt_projects/
├── us_analytics_dbt/          # US region dbt project
│   ├── dbt_project.yml        # Project configuration
│   ├── profiles.yml           # Databricks connection settings
│   └── models/
│       ├── silver/
│       │   └── customer_metrics.sql        # Customer aggregations
│       └── gold/
│           └── customer_cohorts.sql        # Cohort analysis
└── eu_analytics_dbt/          # EU region dbt project
    ├── dbt_project.yml        # Project configuration
    ├── profiles.yml           # Databricks connection settings (GDPR-compliant)
    └── models/
        ├── silver/
        │   └── customer_metrics.sql        # Customer aggregations (GDPR)
        └── gold/
            └── customer_cohorts.sql        # Cohort analysis (GDPR)
```

## dbt Models

### US Region

**Silver Layer - customer_metrics**:
- Aggregates customer data from bronze layer
- Dependencies: `raw_customer_data_us`, `raw_sales_orders_us`
- Calculates: total orders, lifetime value, order dates
- Materialization: Incremental (efficient for large datasets)

**Gold Layer - customer_cohorts**:
- Customer segmentation and cohort analysis
- Dependencies: `customer_metrics` (dbt model)
- Segments: High Value (>$10K), Medium Value ($5K-$10K), Low Value (<$5K)
- Materialization: Table (full refresh)

### EU Region

Same models as US but:
- References EU bronze tables (`raw_customer_data_eu`, `raw_sales_orders_eu`)
- Includes GDPR tags for compliance tracking
- Uses EU Databricks workspace connection

## Integration with Dagster

These dbt projects are integrated into Dagster using `CustomDbtProjectComponent`:
- Each dbt model becomes a Dagster asset
- Dependencies are automatically tracked in the lineage graph
- Supports demo mode (simulated execution) and production mode (real Databricks execution)

## Local dbt Development

To work with these dbt projects locally:

```bash
# Navigate to project directory
cd dbt_projects/us_analytics_dbt

# Install dbt-databricks adapter
pip install dbt-core dbt-databricks

# Set environment variables
export DATABRICKS_US_HOST='your-workspace.databricks.com'
export DATABRICKS_US_TOKEN='your-token'

# Compile models (check for errors)
dbt compile

# Run models
dbt run

# Test models (if you add tests)
dbt test
```

## Connection Configuration

Each dbt project uses environment variables for Databricks connection:
- **US**: `DATABRICKS_US_HOST`, `DATABRICKS_US_TOKEN`
- **EU**: `DATABRICKS_EU_HOST`, `DATABRICKS_EU_TOKEN`

In demo mode (`DAGSTER_DEMO_MODE=true`), these are mocked and dbt execution is simulated.

## Adding New Models

To add new dbt models:

1. Create SQL file in appropriate directory (`models/silver/` or `models/gold/`)
2. Reference upstream sources: `{{ source('bronze', 'table_name') }}`
3. Reference other dbt models: `{{ ref('model_name') }}`
4. Models will automatically appear as Dagster assets
5. Run `uv run dg check defs` to validate

## Source Declarations

To properly connect dbt models to existing Dagster assets, each dbt project needs source declarations. These are implicitly defined through the SQL references:
- `{{ source('bronze', 'raw_customer_data_us') }}` creates dependency on the `raw_customer_data_us` Dagster asset
- `{{ ref('customer_metrics') }}` creates dependency on the `customer_metrics` dbt model

## Demo Mode

When running in demo mode:
- dbt CLI execution is simulated
- Models are marked as materialized without running SQL
- Shows complete lineage without requiring real Databricks workspaces
- Perfect for demonstrations and local development
