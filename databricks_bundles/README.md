# Databricks Asset Bundle Configurations

This directory contains Databricks Asset Bundle (`databricks.yml`) configuration files for the demo.

## Bundle Files

### `databricks_us_etl.yml`
US regional ETL bundle that deploys data ingestion pipelines to the US Databricks workspace.

**Targets**: `us.databricks.com`
**Tasks**:
- `extract_us_customers` - Extracts customer data from Salesforce US, NetSuite US
- `extract_us_sales` - Extracts sales orders from ERP US, E-commerce Platform US
- `extract_us_products` - Extracts product catalog from PIM System US
- `extract_us_financials` - Extracts financial transactions from NetSuite US

**Dagster Component**: `asset_bundle_etl_us/defs.yaml`

### `databricks_eu_etl.yml`
EU regional ETL bundle that deploys data ingestion pipelines to the EU Databricks workspace.

**Targets**: `eu.databricks.com`
**Tasks**:
- `extract_eu_customers` - Extracts customer data from Salesforce EU, SAP ECC
- `extract_eu_sales` - Extracts sales orders from SAP ECC, E-commerce Platform EU
- `extract_eu_products` - Extracts product catalog from PIM System EU
- `extract_eu_financials` - Extracts financial transactions from SAP FI/CO

**Dagster Component**: `asset_bundle_etl_eu/defs.yaml`

## Organization

For projects with many asset bundles, this directory structure keeps bundle configurations organized and separate from the Dagster code. You can further organize by:

```
databricks_bundles/
├── regional/
│   ├── us_etl.yml
│   ├── eu_etl.yml
│   └── apac_etl.yml
├── departmental/
│   ├── analytics.yml
│   ├── finance.yml
│   └── marketing.yml
└── shared/
    └── data_quality.yml
```

## Deploying Bundles

These bundles can be deployed to Databricks using the Databricks CLI:

```bash
# Deploy US ETL bundle
databricks bundle deploy -t us -c databricks_bundles/databricks_us_etl.yml

# Deploy EU ETL bundle
databricks bundle deploy -t eu -c databricks_bundles/databricks_eu_etl.yml
```

Or managed automatically by Dagster through the `CustomDatabricksAssetBundleComponent`.
