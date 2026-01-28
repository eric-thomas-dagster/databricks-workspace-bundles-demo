#!/bin/bash

# Reset and Start Script - Clean start for databricks-workspace-bundles-demo

echo "Resetting dbt state..."
rm -rf src/databricks_workspace_bundles_demo/defs/.local_defs_state

echo "Setting environment variables..."
export DAGSTER_DEMO_MODE=true
export DATABRICKS_US_HOST='https://us.databricks.com'
export DATABRICKS_US_TOKEN='demo-token-us'
export DATABRICKS_EU_HOST='https://eu.databricks.com'
export DATABRICKS_EU_TOKEN='demo-token-eu'
export DATABRICKS_GLOBAL_HOST='https://global.databricks.com'
export DATABRICKS_GLOBAL_TOKEN='demo-token-global'

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
    echo "✗ Validation failed. Please check the errors above."
    exit 1
fi
