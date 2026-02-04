"""
Custom Databricks Asset Bundle Component with demo mode support.

Properly subclasses the official DatabricksAssetBundleComponent from dagster-databricks
and adds demo mode support via DAGSTER_DEMO_MODE environment variable.

Also includes fix for op naming to support multiple components with the same bundle
by using op.name as a prefix rather than the full name.
"""

import os
from typing import Any

from dagster_databricks import DatabricksAssetBundleComponent
from dagster_databricks.utils import snake_case
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
        Override to add demo mode support AND fix op naming issue.

        The fix uses op.name as a PREFIX rather than the full name, ensuring
        unique op names when multiple tasks exist or multiple components use
        the same bundle. This matches the internal Dagster fix.

        In demo mode: simulates execution without calling Databricks.
        In production mode: uses fixed op naming with real execution.
        """
        # Check if there are any tasks - if not, return empty definitions
        # This can happen if the databricks config has no tasks defined yet
        try:
            asset_specs_by_task_key = self.asset_specs_by_task_key
            if not asset_specs_by_task_key:
                return Definitions()
        except Exception:
            # If accessing asset_specs_by_task_key fails, return empty definitions
            return Definitions()

        # Get component path for unique naming
        component_defs_path_as_python_str = snake_case(
            str(os.path.relpath(context.component_path.file_path, start=context.project_root))
        )

        databricks_assets = []

        # Iterate through tasks and create multi-assets with fixed naming
        for task_key, asset_specs in asset_specs_by_task_key.items():
            # FIXED: Use op.name as PREFIX, not full name
            op_prefix = self.op.name if self.op and self.op.name else "databricks"

            if self.demo_mode:
                # Demo mode: simulated execution
                @multi_asset(
                    name=f"{op_prefix}_{task_key}_multi_asset_{component_defs_path_as_python_str}",
                    specs=asset_specs,
                    can_subset=False,
                    op_tags=self.op.tags if self.op else None,
                    description=self.op.description if self.op else None,
                    pool=self.op.pool if self.op else None,
                    backfill_policy=self.op.backfill_policy if self.op else None,
                )
                def _demo_databricks_task_multi_asset(context: AssetExecutionContext):
                    """Multi-asset that simulates Databricks job execution in demo mode."""
                    context.log.info("[DEMO MODE] Simulating Databricks Asset Bundle execution")
                    context.log.info(f"[DEMO MODE] Task: {task_key}")
                    context.log.info(f"[DEMO MODE] Config: {self.databricks_config_path}")
                    context.log.info(f"[DEMO MODE] Selected assets: {context.selected_asset_keys}")

                    for spec in asset_specs:
                        if spec.key in context.selected_asset_keys:
                            yield MaterializeResult(
                                asset_key=spec.key,
                                metadata={
                                    "demo_mode": True,
                                    "databricks_task_key": task_key,
                                    "databricks_config_path": str(self.databricks_config_path),
                                    "simulated_status": "SUCCESS",
                                },
                            )

                databricks_assets.append(_demo_databricks_task_multi_asset)
            else:
                # Production mode: real execution with fixed naming
                @multi_asset(
                    name=f"{op_prefix}_{task_key}_multi_asset_{component_defs_path_as_python_str}",
                    specs=asset_specs,
                    can_subset=False,
                    op_tags=self.op.tags if self.op else None,
                    description=self.op.description if self.op else None,
                    pool=self.op.pool if self.op else None,
                    backfill_policy=self.op.backfill_policy if self.op else None,
                )
                def _databricks_task_multi_asset(
                    context: AssetExecutionContext,
                    databricks: Any,
                ):
                    """Multi-asset that runs multiple assets of a task as a single Databricks job."""
                    yield from databricks.submit_and_poll(
                        component=self,
                        context=context,
                    )

                databricks_assets.append(_databricks_task_multi_asset)

        # Don't include resources here - they're managed by the workspace component
        # to avoid conflicts when multiple bundle components share resources
        return Definitions(assets=databricks_assets)
