#!/bin/bash
# Quick start script for running the Databricks Multi-Workspace demo in demo mode

# Set demo mode environment variables for multi-workspace architecture
export DAGSTER_DEMO_MODE=true
export DATABRICKS_US_HOST='https://us.databricks.com'
export DATABRICKS_US_TOKEN='demo-token-us'
export DATABRICKS_EU_HOST='https://eu.databricks.com'
export DATABRICKS_EU_TOKEN='demo-token-eu'
export DATABRICKS_GLOBAL_HOST='https://global.databricks.com'
export DATABRICKS_GLOBAL_TOKEN='demo-token-global'

echo "============================================================"
echo "Databricks Multi-Workspace & Asset Bundles Demo - Quick Start"
echo "============================================================"
echo ""
echo "Architecture:"
echo "  • Regional Workspaces:"
echo "    - US Workspace (ETL Bundle + Analytics + dbt)"
echo "    - EU Workspace (ETL Bundle + Analytics + dbt)"
echo "  • Global Workspace (Cross-regional aggregation)"
echo "  • 24 total assets across 3 workspaces + external systems"
echo ""
echo "Environment:"
echo "  DAGSTER_DEMO_MODE=${DAGSTER_DEMO_MODE}"
echo "  DATABRICKS_US_HOST=${DATABRICKS_US_HOST}"
echo "  DATABRICKS_EU_HOST=${DATABRICKS_EU_HOST}"
echo "  DATABRICKS_GLOBAL_HOST=${DATABRICKS_GLOBAL_HOST}"
echo ""
echo "Validating configuration..."
uv run python -c "from databricks_workspace_bundles_demo.definitions import defs; defs(); print('✓ Definitions loaded successfully')"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Validation successful!"
    echo ""
    echo "Starting Dagster..."
    echo "Open http://localhost:3000 in your browser"
    echo ""
    uv run dg dev
else
    echo ""
    echo "✗ Validation failed. Please check the errors above."
    exit 1
fi
