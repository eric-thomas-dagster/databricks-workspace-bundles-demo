# dbt Projects

This directory contains a **consolidated dbt project** demonstrating multi-region deployment patterns with shared SQL logic.

## Structure

```
dbt_projects/
└── common_analytics_dbt/         # Shared dbt project (US + EU)
    ├── dbt_project.yml           # Project configuration
    ├── profiles.yml              # Multi-target configuration (us/eu)
    ├── models/
    │   ├── sources.yml           # All regional sources (US + EU)
    │   ├── silver/
    │   │   └── customer_metrics.sql        # Customer aggregations
    │   └── gold/
    │       └── customer_cohorts.sql        # Cohort analysis
    └── README.md
```

## Consolidated Project Pattern

### Why Consolidate?

**Problem**: Separate `us_analytics_dbt` and `eu_analytics_dbt` projects had identical SQL logic, violating DRY principles.

**Solution**: Single `common_analytics_dbt` project with **multi-target configuration**:

```yaml
# profiles.yml
common_analytics_dbt:
  target: "{{ env_var('DBT_TARGET', 'us') }}"
  outputs:
    us:
      type: databricks
      host: "{{ env_var('DATABRICKS_US_HOST') }}"
      token: "{{ env_var('DATABRICKS_US_TOKEN') }}"
      schema: us_analytics
    eu:
      type: databricks
      host: "{{ env_var('DATABRICKS_EU_HOST') }}"
      token: "{{ env_var('DATABRICKS_EU_TOKEN') }}"
      schema: eu_analytics
```

### Dynamic Region Selection in SQL

Models use `{{ target.name }}` to dynamically reference region-specific sources:

```sql
-- models/silver/customer_metrics.sql
{% set region = target.name %}

SELECT
    c.customer_id,
    c.customer_name,
    COUNT(DISTINCT s.order_id) as total_orders
FROM {{ source('dagster', 'raw_customer_data_' ~ region) }} c
LEFT JOIN {{ source('dagster', 'raw_sales_orders_' ~ region) }} s
    ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.customer_name
```

This single SQL file works for both US and EU by substituting the `region` variable.

## Dagster Component Configuration

### Multiple Components, Same Project

Two Dagster components reference the **same dbt project** but specify different targets:

```yaml
# defs/dbt_us_common/defs.yaml
type: CustomDbtProjectComponent
attributes:
  project:
    project_dir: "{{ project_root }}/dbt_projects/common_analytics_dbt"
    target: "us"  # Uses US target

  op:
    name: "dbt_us_common"  # Unique op name

  select: "tag:us"  # Load only US-tagged models (sources auto-included)

  translation:
    key: "{% if node.resource_type == 'source' %}raw/us/{{ node.name | replace('raw_', '') | replace('_us', '') }}{% elif 'cohort' in node.name %}gold/us/{{ node.name }}{% else %}silver/us/{{ node.name }}{% endif %}"
    group_name: us_dbt_analytics_common

# defs/dbt_eu_common/defs.yaml
type: CustomDbtProjectComponent
attributes:
  project:
    project_dir: "{{ project_root }}/dbt_projects/common_analytics_dbt"
    target: "eu"  # Uses EU target

  op:
    name: "dbt_eu_common"  # Different op name

  select: "tag:eu"  # Load only EU-tagged models (sources auto-included)

  translation:
    key: "{% if node.resource_type == 'source' %}raw/eu/{{ node.name | replace('raw_', '') | replace('_eu', '') }}{% elif 'cohort' in node.name %}gold/eu/{{ node.name }}{% else %}silver/eu/{{ node.name }}{% endif %}"
    group_name: eu_dbt_analytics_common
```

### Critical Configuration Patterns

#### 1. State Key Uniqueness

**Custom Implementation** (in `CustomDbtProjectComponent`):

```python
@property
def defs_state_config(self) -> DefsStateConfig:
    """Uses dbt target to create unique state keys."""
    discriminator = self._project_manager.defs_state_discriminator

    # Add dbt target to discriminator
    target = self._project_manager.args.target
    if target:
        discriminator = f"{discriminator},{target}"

    return DefsStateConfig(
        key=f"DbtProjectComponent[{discriminator}]",
        # ...
    )
```

**Result**: Prevents "DuplicateDefsStateKeyWarning":
- Before: `DbtProjectComponent[common_analytics_dbt]` (collision!)
- After: `DbtProjectComponent[common_analytics_dbt,us]` and `DbtProjectComponent[common_analytics_dbt,eu]` ✅

#### 2. Unique Op Names

Each component MUST specify unique `op.name`:

```yaml
op:
  name: "dbt_us_common"  # US component
  # vs
  name: "dbt_eu_common"  # EU component
```

This prevents op execution collisions when both components run.

#### 3. Selective Source Loading

**Use `select` (not `exclude`)** for region-specific filtering:

```yaml
select: "tag:us"  # US component (whitelist approach)
# vs
select: "tag:eu"  # EU component
```

**Why tag-based selection?**
- dbt automatically includes required sources when resolving model dependencies
- Scales better when adding regions (no need to exclude multiple regions)
- More explicit and safer than wildcards
- Easier to understand which models are included
- Avoids dbt selection syntax warnings about unmatched source patterns

## dbt Models

### Silver Layer - customer_metrics

**Purpose**: Aggregates customer data from bronze layer

**Dependencies**:
- `raw_customer_data_{region}` (US or EU)
- `raw_sales_orders_{region}` (US or EU)

**Calculations**:
- Total orders per customer
- Total revenue per customer
- First and last order dates
- Customer registration date

**Materialization**: Incremental (efficient for large datasets)

**Region Handling**: Uses `{{ target.name }}` to dynamically reference the correct bronze tables

### Gold Layer - customer_cohorts

**Purpose**: Customer segmentation and cohort analysis

**Dependencies**: `customer_metrics` (silver dbt model)

**Segments**:
- High Value: >$10,000 lifetime value
- Medium Value: $5,000-$10,000 lifetime value
- Low Value: <$5,000 lifetime value

**Materialization**: Table (full refresh for analysis)

**Region Handling**: Inherits region from upstream `customer_metrics` model

## Source Declarations

All regional sources are declared in `models/sources.yml`:

```yaml
sources:
  - name: dagster
    tables:
      # US Sources
      - name: raw_customer_data_us
        meta:
          dagster:
            asset_key: ["raw", "us", "customer_data"]

      - name: raw_sales_orders_us
        meta:
          dagster:
            asset_key: ["raw", "us", "sales_orders"]

      # EU Sources
      - name: raw_customer_data_eu
        meta:
          dagster:
            asset_key: ["raw", "eu", "customer_data"]

      - name: raw_sales_orders_eu
        meta:
          dagster:
            asset_key: ["raw", "eu", "sales_orders"]
```

The `select` parameter in each component filters which models are loaded. dbt automatically includes required sources when resolving model dependencies, so explicit source selection is not needed.

## Local dbt Development

To work with the dbt project locally:

```bash
# Navigate to project directory
cd dbt_projects/common_analytics_dbt

# Install dbt-databricks adapter
pip install dbt-core dbt-databricks

# Set environment variables for US target
export DATABRICKS_US_HOST='your-workspace.databricks.com'
export DATABRICKS_US_TOKEN='your-token'
export DBT_TARGET='us'

# Compile models (check for errors)
dbt compile

# Run models for US
dbt run --target us

# Run models for EU
export DATABRICKS_EU_HOST='eu-workspace.databricks.com'
export DATABRICKS_EU_TOKEN='eu-token'
dbt run --target eu

# Test models (if you add tests)
dbt test
```

## Adding New Regions (e.g., APAC)

To add APAC region:

1. **Add APAC target to `profiles.yml`**:
   ```yaml
   outputs:
     apac:
       type: databricks
       host: "{{ env_var('DATABRICKS_APAC_HOST') }}"
       token: "{{ env_var('DATABRICKS_APAC_TOKEN') }}"
       schema: apac_analytics
   ```

2. **Add APAC sources to `models/sources.yml`**:
   ```yaml
   - name: raw_customer_data_apac
   - name: raw_sales_orders_apac
   ```

3. **Create APAC component** (`defs/dbt_apac_common/defs.yaml`):
   ```yaml
   attributes:
     project:
       project_dir: "{{ project_root }}/dbt_projects/common_analytics_dbt"
       target: "apac"
     op:
       name: "dbt_apac_common"
     select: "tag:apac"
   ```

**No changes needed** to existing models or US/EU configurations! ✅

## Demo Mode

When running in demo mode (`DAGSTER_DEMO_MODE=true`):
- dbt CLI execution is simulated
- Models are marked as materialized without running SQL
- Shows complete lineage without requiring real Databricks workspaces
- Perfect for demonstrations and local development

```bash
export DAGSTER_DEMO_MODE=true
dagster dev
```

## Benefits of This Pattern

✅ **DRY Principle**: SQL logic defined once, used for all regions
✅ **Scalable**: Add regions without modifying models
✅ **Maintainable**: Single source of truth for transformations
✅ **Collision-Free**: Unique state keys and op names
✅ **Selective Loading**: Each component loads only its region's data
✅ **Native dbt Pattern**: Uses standard multi-target configuration
