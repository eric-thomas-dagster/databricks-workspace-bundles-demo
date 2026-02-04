"""
Custom dbt Component with Databricks and demo mode support.

Extends DbtProjectComponent to add demo mode execution, allowing the demo
to run without actual Databricks credentials or dbt CLI execution.
"""

import os
from typing import Any, Iterator

from dagster import AssetExecutionContext, MaterializeResult, Definitions
from dagster.components.utils.defs_state import DefsStateConfig
from dagster_dbt import DbtProjectComponent
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType


class CustomDbtProjectComponent(DbtProjectComponent):
    """
    Custom dbt component that extends the official DbtProjectComponent with demo mode support.

    When DAGSTER_DEMO_MODE=true, simulates dbt execution without requiring:
    - Real Databricks credentials
    - dbt CLI installation
    - Actual SQL execution

    When DAGSTER_DEMO_MODE=false, uses the standard DbtProjectComponent behavior.

    Automatically enriches all dbt assets with databricks_workspace_host metadata
    by detecting the workspace from asset group names (us_dbt_analytics -> DATABRICKS_US_HOST).

    Supports multiple components sharing the same dbt project by using the dbt target
    to create unique state keys (e.g., DbtProjectComponent[common_analytics_dbt,us]).
    """

    @property
    def defs_state_config(self) -> DefsStateConfig:
        """
        Override to include dbt target in the discriminator for unique state keys.

        When multiple components share the same dbt project but target different
        workspaces/regions, the dbt target name ensures each has a unique state key.

        Following engineering's guidance: extend the discriminator with the target,
        formatted as: DbtProjectComponent[common_analytics_dbt,us]
        """
        # Get the base discriminator (project directory)
        discriminator = self._project_manager.defs_state_discriminator

        # Add the dbt target to make it unique
        # This works because each component specifies target: "us" or target: "eu"
        if hasattr(self._project_manager, 'args') and hasattr(self._project_manager.args, 'target'):
            target = self._project_manager.args.target
            if target:
                discriminator = f"{discriminator},{target}"

        return DefsStateConfig(
            key=f"DbtProjectComponent[{discriminator}]",
            management_type=DefsStateManagementType.LOCAL_FILESYSTEM,
            refresh_if_dev=self.prepare_if_dev,
        )

    def build_defs(self, context: Any) -> Definitions:
        """
        Override to enrich dbt asset specs with workspace metadata after they're built.

        This approach adds metadata to existing specs rather than trying to customize
        the translator, which is simpler and more reliable.
        """
        # Get definitions from parent class
        defs = super().build_defs(context)

        # Get workspace host from project path
        workspace_host = self._get_workspace_host_from_project_path()

        # Enrich asset specs with workspace metadata if we found a valid host
        if workspace_host != "unknown" and defs.assets:
            from dagster import AssetsDefinition

            enriched_assets = []
            for asset_def in defs.assets:
                if isinstance(asset_def, AssetsDefinition) and hasattr(asset_def, 'specs'):
                    # Build new metadata_by_key with workspace host added
                    new_metadata_by_key = {}
                    for spec in asset_def.specs:
                        # Merge workspace host into existing metadata
                        new_metadata = {**(spec.metadata or {})}
                        new_metadata["databricks_workspace_host"] = workspace_host
                        new_metadata_by_key[spec.key] = new_metadata

                    # Use with_attributes to create new asset def with enriched metadata
                    enriched_asset = asset_def.with_attributes(
                        metadata_by_key=new_metadata_by_key
                    )
                    enriched_assets.append(enriched_asset)
                else:
                    # Keep non-AssetsDefinition assets as is
                    enriched_assets.append(asset_def)

            return Definitions(
                assets=enriched_assets,
                resources=defs.resources,
            )

        return defs

    @property
    def demo_mode(self) -> bool:
        """Check if demo mode is enabled via environment variable."""
        return os.getenv("DAGSTER_DEMO_MODE", "false").lower() == "true"

    def _get_workspace_host_from_project_path(self) -> str:
        """
        Get workspace host from dbt target or project path.

        For common projects, uses the dbt target (us/eu) to determine workspace.
        For separate projects, detects from project path patterns.
        """
        # If using dbt target (common project), use it to determine workspace
        if hasattr(self, '_project_manager') and hasattr(self._project_manager, 'args'):
            target = getattr(self._project_manager.args, 'target', None)
            if target:
                if target.lower() == "eu":
                    return os.getenv("DATABRICKS_EU_HOST", "https://eu.databricks.com")
                elif target.lower() == "us":
                    return os.getenv("DATABRICKS_US_HOST", "https://us.databricks.com")

        # Otherwise fall back to project path detection
        project_path = str(self.project) if self.project else ""

        # Map project paths to environment variables
        # Check for EU first since "us" appears in words like "customer"
        if "eu_analytics" in project_path.lower():
            return os.getenv("DATABRICKS_EU_HOST", "https://eu.databricks.com")
        elif "us_analytics" in project_path.lower():
            return os.getenv("DATABRICKS_US_HOST", "https://us.databricks.com")

        return "unknown"


    def execute(
        self,
        context: AssetExecutionContext,
        dbt: Any,
    ) -> Iterator[MaterializeResult]:
        """
        Override execute to add demo mode simulation.

        In demo mode:
        - Logs that dbt execution is being simulated
        - Yields MaterializeResult for each selected asset in topological order
        - Adds demo_mode metadata

        In production mode:
        - Calls parent class execute() for real dbt execution via Databricks

        Note: databricks_workspace_host metadata is added in build_defs(), not here.
        """
        # Get workspace host for logging
        workspace_host = self._get_workspace_host_from_project_path()

        if self.demo_mode:
            context.log.info("[DEMO MODE] Simulating dbt execution")
            context.log.info(f"dbt project: {self.project}")
            context.log.info(f"Databricks workspace: {workspace_host}")
            context.log.info("In production, dbt would run on Databricks cluster")

            # Sort selected assets in topological order (silver before gold)
            # Simple heuristic: sort by layer (silver < gold) then by name
            selected_keys = sorted(
                context.selected_asset_keys,
                key=lambda k: (
                    0 if 'silver' in k.path else 1,  # silver first, then gold
                    k.path[-1]  # then alphabetically by name
                )
            )

            # Simulate execution for each selected asset in order
            for asset_key in selected_keys:
                model_name = asset_key.path[-1]
                layer = asset_key.path[0] if len(asset_key.path) > 0 else "unknown"
                context.log.info(f"[DEMO MODE] Simulating dbt model: {layer}/{model_name}")

                yield MaterializeResult(
                    asset_key=asset_key,
                    metadata={
                        "demo_mode": True,
                        "dbt_model": model_name,
                        "dbt_project": str(self.project),
                        "layer": layer,
                        "rows_affected": 1000,  # Mock row count
                        "execution_time_seconds": 2.5,  # Mock execution time
                        # Note: databricks_workspace_host is already in the asset spec
                    }
                )
        else:
            # Real execution: use parent class implementation
            # This would execute dbt via PipesDatabricksClient on Databricks
            context.log.info("Executing dbt on Databricks")
            context.log.info(f"Databricks workspace: {workspace_host}")
            # Note: databricks_workspace_host is already in the asset spec
            yield from super().execute(context, dbt)
