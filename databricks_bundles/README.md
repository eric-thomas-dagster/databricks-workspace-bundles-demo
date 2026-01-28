# Databricks Asset Bundle Configurations

This directory contains Databricks Asset Bundle (`databricks.yml`) configuration files for the demo, demonstrating both **consistent ETL patterns** (same structure across regions) and **region-specific bundles** (custom compliance features).

## Bundle Architecture

This demo showcases two bundle patterns:

### 1. Consistent ETL Pattern (Standardized Across Regions)
**`databricks_us_etl.yml`** and **`databricks_eu_etl.yml`** - Regional ETL bundles following the same pattern

These bundles follow identical structure and task naming, demonstrating:
- Standardized ETL patterns across regions
- Consistent task structure and naming conventions
- Regional deployment with unique bundle names (avoids naming collisions)

**Common Tasks** (same across both regions):
- `extract_customers` - Extracts customer data from regional CRM/ERP systems
- `extract_sales` - Extracts sales orders from regional systems
- `extract_products` - Extracts product catalog from regional PIM
- `extract_financials` - Extracts financial transactions from regional systems

**Key Difference**: Each bundle has a unique name (`us_data_etl` vs `eu_data_etl`) and job name to avoid Dagster naming collisions.

### 2. Region-Specific Bundle Pattern (Custom Requirements)
Region-specific bundles for compliance, regulatory, or business-specific needs.

#### **`databricks_us_regional.yml`** - US-specific compliance features
US-only regulatory and compliance requirements (SOX, GAAP, state tax).

**Deployed to**: US workspace via `asset_bundle_regional_us/defs.yaml`

**Tasks**:
- `sox_compliance_check` - SOX compliance validation
- `gaap_financial_reporting` - GAAP financial reporting
- `state_tax_aggregation` - US state tax calculations

#### **`databricks_eu_regional.yml`** - EU-specific compliance features
EU-only regulatory and compliance requirements (GDPR, IFRS, VAT).

**Deployed to**: EU workspace via `asset_bundle_regional_eu/defs.yaml`

**Tasks**:
- `gdpr_compliance_check` - GDPR compliance validation
- `ifrs_financial_reporting` - IFRS financial reporting
- `vat_tax_aggregation` - EU VAT tax calculations

## Architecture Benefits

### Consistent ETL Pattern (`databricks_us_etl.yml`, `databricks_eu_etl.yml`)
- ✅ **Standardization**: Same structure and task naming across regions
- ✅ **Consistency**: Identical ETL logic and conventions
- ✅ **No Naming Collisions**: Unique bundle/job names per region
- ✅ **Easy to Replicate**: Copy pattern to new regions

### Region-Specific Bundles
- ✅ **Flexibility**: Custom features per region
- ✅ **Compliance**: Region-specific regulatory requirements
- ✅ **Isolation**: Regional features don't affect other regions
- ✅ **Scalability**: Add new regions without modifying shared bundle

## File Organization

```
databricks_bundles/
├── databricks_us_etl.yml           # US ETL (follows standard pattern)
├── databricks_eu_etl.yml           # EU ETL (follows standard pattern)
├── databricks_us_regional.yml      # US-specific compliance
└── databricks_eu_regional.yml      # EU-specific compliance
```

For larger projects, you could organize as:

```
databricks_bundles/
├── shared/
│   ├── etl.yml                     # Common ETL across all regions
│   ├── data_quality.yml            # Shared data quality checks
│   └── monitoring.yml              # Common monitoring
├── regional/
│   ├── us/
│   │   ├── compliance.yml          # US compliance
│   │   └── regional_analytics.yml  # US-specific analytics
│   ├── eu/
│   │   ├── compliance.yml          # EU compliance (GDPR)
│   │   └── regional_analytics.yml  # EU-specific analytics
│   └── apac/
│       └── compliance.yml          # APAC compliance
└── departmental/
    ├── finance.yml                 # Finance-specific workflows
    └── marketing.yml               # Marketing-specific workflows
```

## Deploying Bundles

### Via Databricks CLI

```bash
# Deploy US ETL bundle
databricks bundle deploy -t prod -c databricks_bundles/databricks_us_etl.yml

# Deploy EU ETL bundle
databricks bundle deploy -t prod -c databricks_bundles/databricks_eu_etl.yml

# Deploy US-specific regional bundle
databricks bundle deploy -t prod -c databricks_bundles/databricks_us_regional.yml

# Deploy EU-specific regional bundle
databricks bundle deploy -t prod -c databricks_bundles/databricks_eu_regional.yml
```

### Via Dagster (Automatic)

Dagster's `CustomDatabricksAssetBundleComponent` automatically manages bundle deployment:

```yaml
# Example: asset_bundle_etl_us/defs.yaml
attributes:
  databricks_config_path: "{{ project_root }}/databricks_bundles/databricks_us_etl.yml"
  workspace:
    host: "{{ env.DATABRICKS_US_HOST }}"
```

## Demo Mode

All bundles work in demo mode (`DAGSTER_DEMO_MODE=true`) without requiring real Databricks credentials or workspaces.
