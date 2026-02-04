# Databricks Asset Bundle Configurations

This directory contains Databricks Asset Bundle configurations demonstrating **consolidated bundle patterns** with resource includes and multi-region deployment.

## Bundle Architecture

### Consolidated Pattern with Resource Includes

This demo showcases the **include pattern** for Databricks Asset Bundles, where task definitions are separated into reusable resource files:

```
databricks_bundles/
├── common_regional_etl.yml          # Shared ETL bundle (US + EU)
├── databricks_us_regional.yml       # US-specific compliance
├── databricks_eu_regional.yml       # EU-specific compliance
└── resources/                       # Task definitions (included files)
    ├── etl_jobs.yml                 # Shared ETL tasks
    ├── us_regional_jobs.yml         # US compliance tasks
    └── eu_regional_jobs.yml         # EU compliance tasks
```

### Why Use the Include Pattern?

**Problem**: Dagster's `DatabricksConfig` parser **only reads tasks from included files**, not from tasks defined inline in the main bundle YAML.

**Solution**: Separate task definitions into `resources/*.yml` files and include them:

```yaml
# common_regional_etl.yml
bundle:
  name: regional_data_etl

include:
  - resources/etl_jobs.yml  # Tasks loaded from here

targets:
  us:
    workspace:
      host: ${DATABRICKS_US_HOST}
  eu:
    workspace:
      host: ${DATABRICKS_EU_HOST}
```

## Bundle Descriptions

### 1. `common_regional_etl.yml` - Shared ETL Pattern

**Purpose**: Single bundle shared by both US and EU regions with identical ETL tasks.

**Includes**: `resources/etl_jobs.yml`

**Tasks** (from included file):
- `extract_customers` - Extracts customer data from regional CRM/ERP
- `extract_sales` - Extracts sales orders from regional systems
- `extract_products` - Extracts product catalog from regional PIM
- `extract_financials` - Extracts financial transactions

**Used By**:
- `asset_bundle_etl_us` component (points to US workspace)
- `asset_bundle_etl_eu` component (points to EU workspace)

**Key Pattern**: Components specify different workspaces and unique `op.name` values:

```yaml
# asset_bundle_etl_us/defs.yaml
attributes:
  databricks_config_path: "{{ project_root }}/databricks_bundles/common_regional_etl.yml"

  op:
    name: "etl_us"  # Unique per region

  workspace:
    host: "{{ env.DATABRICKS_US_HOST }}"  # Determines deployment target
```

### 2. `databricks_us_regional.yml` - US-Specific Compliance

**Purpose**: US-only regulatory and compliance workflows (SOX, GAAP, state tax).

**Includes**: `resources/us_regional_jobs.yml`

**Tasks** (from included file):
- `sox_compliance_check` - SOX compliance validation
- `gaap_financial_reporting` - GAAP financial reporting
- `state_tax_aggregation` - US state tax calculations

**Used By**: `asset_bundle_regional_us` component

### 3. `databricks_eu_regional.yml` - EU-Specific Compliance

**Purpose**: EU-only regulatory and compliance workflows (GDPR, IFRS, VAT).

**Includes**: `resources/eu_regional_jobs.yml`

**Tasks** (from included file):
- `gdpr_compliance_check` - GDPR compliance validation
- `ifrs_financial_reporting` - IFRS financial reporting
- `vat_tax_aggregation` - EU VAT tax calculations

**Used By**: `asset_bundle_regional_eu` component

## Component Configuration Pattern

### Multiple Components, Same Bundle

**Key Technique**: Multiple Dagster components can reference the **same bundle file** while targeting different workspaces:

```yaml
# US Component
type: CustomDatabricksAssetBundleComponent
attributes:
  databricks_config_path: "{{ project_root }}/databricks_bundles/common_regional_etl.yml"
  op:
    name: "etl_us"  # Unique op name prevents collisions
  workspace:
    host: "{{ env.DATABRICKS_US_HOST }}"  # US deployment

# EU Component (same bundle, different workspace!)
type: CustomDatabricksAssetBundleComponent
attributes:
  databricks_config_path: "{{ project_root }}/databricks_bundles/common_regional_etl.yml"
  op:
    name: "etl_eu"  # Different op name
  workspace:
    host: "{{ env.DATABRICKS_EU_HOST }}"  # EU deployment
```

### Critical Op Naming Pattern

**⚠️ Important**: Each component MUST have a unique `op.name` to avoid execution collisions:

```yaml
op:
  name: "etl_us"  # US component
  # vs
  name: "etl_eu"  # EU component
```

This ensures unique op names like:
- `etl_us_extract_customers_multi_asset_...`
- `etl_eu_extract_customers_multi_asset_...`

**Note**: The op naming fix that uses `op.name` as a **prefix** (not full replacement) is implemented in `CustomDatabricksAssetBundleComponent` but **not yet released** in official `dagster-databricks` (as of 0.28.12).

## Scaling to Additional Regions

Adding APAC region:

1. **No bundle changes needed!** The `common_regional_etl.yml` already supports any region.

2. **Create APAC component**:
   ```yaml
   # asset_bundle_etl_apac/defs.yaml
   attributes:
     databricks_config_path: "{{ project_root }}/databricks_bundles/common_regional_etl.yml"
     op:
       name: "etl_apac"  # Unique name
     workspace:
       host: "{{ env.DATABRICKS_APAC_HOST }}"
   ```

3. **Create APAC-specific compliance** (if needed):
   ```yaml
   # databricks_bundles/databricks_apac_regional.yml
   include:
     - resources/apac_regional_jobs.yml
   ```

## Resource File Organization

Resource files contain the actual job and task definitions:

```yaml
# resources/etl_jobs.yml
resources:
  jobs:
    regional_data_extract:
      name: "Regional Data Extract"
      tasks:
        - task_key: extract_customers
          notebook_task:
            notebook_path: /Workspace/etl/extract_customers
          new_cluster:
            spark_version: "13.3.x-scala2.12"
            node_type_id: "i3.xlarge"
            num_workers: 2
        # ... more tasks
```

**Benefits**:
- ✅ **DRY Principle**: Task definitions defined once, used by multiple regions
- ✅ **Maintainability**: Update one file to affect all regions
- ✅ **Dagster Requirement**: Parser only reads included files
- ✅ **Modularity**: Organize tasks by domain (ETL, compliance, analytics)

## Deploying Bundles

### Via Databricks CLI

```bash
# Deploy shared ETL to US workspace
databricks bundle deploy -t us -c databricks_bundles/common_regional_etl.yml

# Deploy shared ETL to EU workspace
databricks bundle deploy -t eu -c databricks_bundles/common_regional_etl.yml

# Deploy US-specific regional bundle
databricks bundle deploy -t prod -c databricks_bundles/databricks_us_regional.yml

# Deploy EU-specific regional bundle
databricks bundle deploy -t prod -c databricks_bundles/databricks_eu_regional.yml
```

### Via Dagster (Automatic)

Dagster's `CustomDatabricksAssetBundleComponent` automatically manages bundle deployment based on the workspace configuration in each component.

## Demo Mode

All bundles work in demo mode (`DAGSTER_DEMO_MODE=true`) without requiring real Databricks credentials or workspaces.

```bash
export DAGSTER_DEMO_MODE=true
dagster dev
```

## Benefits of This Pattern

✅ **DRY Principle**: Shared bundles eliminate duplication
✅ **Scalable**: Add regions without modifying existing bundles
✅ **Flexible**: Mix shared and region-specific bundles
✅ **Maintainable**: Single source of truth for common tasks
✅ **Collision-Free**: Unique op names via component configuration
✅ **Standard Pattern**: Follows Databricks Asset Bundle best practices
