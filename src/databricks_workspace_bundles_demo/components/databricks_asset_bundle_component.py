"""
Custom Databricks Asset Bundle Component with demo mode support.

Properly subclasses the official DatabricksAssetBundleComponent from dagster-databricks
and adds demo mode support via DAGSTER_DEMO_MODE environment variable.
"""

import os
from typing import Any

from dagster_databricks import DatabricksAssetBundleComponent
from dagster import (
    AssetExecutionContext,
    Definitions,
    MaterializeResult,
    multi_asset,
)


class CustomDatabricksAssetBundleComponent(DatabricksAssetBundleComponent):
    """
    Custom Databricks Asset Bundle Component with demo mode support.

    Extends the official DatabricksAssetBundleComponent to add demo mode support.
    When DAGSTER_DEMO_MODE=true, simulates bundle execution without calling Databricks.
    When DAGSTER_DEMO_MODE=false or unset, uses the official component's full functionality.

    This follows the same pattern as customizing the dbt component - we subclass
    the official component and override only what we need to change.

    Example YAML configuration:
        type: databricks_workspace_bundles_demo.components.CustomDatabricksAssetBundleComponent
        attributes:
          databricks_config_path: "{{ project_root }}/databricks.yml"
          workspace:
            host: "{{ env.DATABRICKS_HOST }}"
            token: "{{ env.DATABRICKS_TOKEN }}"
          compute_config:
            is_serverless: true
          assets_by_task_key:
            extract_customer_data:
              - key: raw_customer_data
                kinds: [raw, bronze, parquet]

    Environment Variables:
        DAGSTER_DEMO_MODE: Set to "true" to enable demo mode simulation
    """

    @property
    def demo_mode(self) -> bool:
        """Check if demo mode is enabled via environment variable."""
        return os.getenv("DAGSTER_DEMO_MODE", "false").lower() == "true"

    def build_defs(self, context: Any) -> Definitions:
        """
        Override to add demo mode support.

        This is the minimal override needed - we only change execution behavior
        when demo_mode is enabled. Otherwise, we delegate to the official implementation.
        """
        if not self.demo_mode:
            # Real mode: use the official implementation
            return super().build_defs(context)

        # Demo mode: create custom assets with simulated execution
        # Use the assets_by_task_key which are already AssetSpec objects from YAML
        specs_by_task = self.assets_by_task_key or {}
        all_specs = [spec for specs in specs_by_task.values() for spec in specs]

        # Extract bundle name from the databricks config file path
        # e.g., databricks_analytics.yml -> analytics
        import re
        config_filename = self.databricks_config_path.name if self.databricks_config_path else "unknown"
        match = re.search(r'databricks_?(.+)\.yml', config_filename)
        bundle_name = match.group(1) if match else "bundle"

        @multi_asset(
            name=f"databricks_bundle_{bundle_name}_demo",
            specs=all_specs,
            can_subset=True,
        )
        def _demo_execution_fn(context: AssetExecutionContext):
            context.log.info(
                f"[DEMO MODE] Simulating Databricks Asset Bundle execution"
            )
            context.log.info(f"[DEMO MODE] Bundle: {bundle_name}")
            context.log.info(f"[DEMO MODE] Config: {self.databricks_config_path}")
            context.log.info(f"[DEMO MODE] Selected assets: {context.selected_asset_keys}")

            # Find which tasks need to run based on selected assets
            tasks_to_run = set()
            for task_key, specs in specs_by_task.items():
                if any(spec.key in context.selected_asset_keys for spec in specs):
                    tasks_to_run.add(task_key)

            context.log.info(f"[DEMO MODE] Tasks to execute: {tasks_to_run}")

            for spec in all_specs:
                if spec.key in context.selected_asset_keys:
                    # Find which task this asset belongs to
                    task_key = next(
                        (tk for tk, specs in specs_by_task.items() if spec in specs),
                        "unknown"
                    )

                    yield MaterializeResult(
                        asset_key=spec.key,
                        metadata={
                            "demo_mode": True,
                            "databricks_bundle": bundle_name,
                            "databricks_task_key": task_key,
                            "databricks_config_path": str(self.databricks_config_path),
                            "simulated_status": "SUCCESS",
                        },
                    )

        return Definitions(assets=[_demo_execution_fn])
