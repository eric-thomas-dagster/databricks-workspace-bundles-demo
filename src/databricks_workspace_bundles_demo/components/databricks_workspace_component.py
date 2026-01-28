"""
Custom Databricks Workspace Component with demo mode support.

Properly subclasses the official DatabricksWorkspaceComponent from dagster-databricks
and adds demo mode support via DAGSTER_DEMO_MODE environment variable.
"""

import os
import hashlib
from typing import Any

from dagster_databricks import DatabricksWorkspaceComponent
from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    Definitions,
    MaterializeResult,
    multi_asset,
)


class CustomDatabricksWorkspaceComponent(DatabricksWorkspaceComponent):
    """
    Custom Databricks Workspace Component with demo mode support.

    Extends the official DatabricksWorkspaceComponent to add demo mode support.
    When DAGSTER_DEMO_MODE=true, simulates job execution without calling Databricks APIs.
    When DAGSTER_DEMO_MODE=false or unset, uses the official component's full functionality.

    This follows the same pattern as customizing the dbt component - we subclass
    the official component and override only what we need to change.

    Example YAML configuration:
        type: databricks_workspace_bundles_demo.components.CustomDatabricksWorkspaceComponent
        attributes:
          workspace:
            host: "{{ env.DATABRICKS_HOST }}"
            token: "{{ env.DATABRICKS_TOKEN }}"
          databricks_filter:
            job_name_pattern: "analytics_.*"
          assets_by_task_key:
            my_task:
              - key: customer_360_view
                owners: ["team@company.com"]

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

        In demo mode, we skip job discovery entirely and build assets directly
        from the YAML-defined assets_by_task_key.
        """
        if not self.demo_mode:
            # Real mode: use the official implementation which discovers jobs
            return super().build_defs(context)

        # Demo mode: create custom assets without calling Databricks APIs
        # Use the assets_by_task_key from YAML which are already AssetSpec objects
        specs_by_task = self.assets_by_task_key or {}
        all_specs = [spec for specs in specs_by_task.values() for spec in specs]

        # Generate a unique name for this workspace based on workspace host
        # Use a hash of the workspace host to ensure uniqueness
        workspace_host = self.workspace.host if self.workspace else "unknown"
        workspace_hash = hashlib.md5(workspace_host.encode()).hexdigest()[:8]
        workspace_name = f"workspace_{workspace_hash}"

        @multi_asset(
            name=f"databricks_workspace_{workspace_name}_demo",
            specs=all_specs,
            can_subset=True,
        )
        def _demo_execution_fn(context: AssetExecutionContext):
            context.log.info(
                f"[DEMO MODE] Simulating Databricks workspace job execution"
            )
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
                            "databricks_task_key": task_key,
                            "simulated_status": "SUCCESS",
                        },
                    )

        return Definitions(assets=[_demo_execution_fn])

    def _create_job_asset_def(
        self, job: Any, specs: list[Any], task_key_map: dict
    ) -> AssetsDefinition:
        """
        Override to add demo mode support to job execution.

        This is the minimal override needed - we only change execution behavior
        when demo_mode is enabled. Otherwise, we delegate to the official implementation.
        """
        if not self.demo_mode:
            # Real mode: use the official implementation
            return super()._create_job_asset_def(job, specs, task_key_map)

        # Demo mode: create custom multi-asset with simulated execution
        asset_name = f"databricks_job_{job.job_id}"

        @multi_asset(name=asset_name, specs=specs, can_subset=True)
        def _demo_execution_fn(context: AssetExecutionContext):
            context.log.info(
                f"[DEMO MODE] Simulating Databricks job execution for job {job.job_id}"
            )
            context.log.info(f"[DEMO MODE] Job name: {job.name}")
            context.log.info(f"[DEMO MODE] Selected assets: {context.selected_asset_keys}")

            for spec in specs:
                if spec.key in context.selected_asset_keys:
                    task_key = task_key_map.get(spec.key, "unknown")
                    context.log.info(f"[DEMO MODE] Executing task: {task_key}")

                    yield MaterializeResult(
                        asset_key=spec.key,
                        metadata={
                            "demo_mode": True,
                            "databricks_job_id": job.job_id,
                            "databricks_job_name": job.name,
                            "databricks_task_key": task_key,
                            "simulated_status": "SUCCESS",
                        },
                    )

        return _demo_execution_fn
