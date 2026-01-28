"""
Custom Databricks components with demo mode support.

These components properly subclass the official dagster-databricks components
and add a demo_mode flag for local testing without Databricks infrastructure.

When demo_mode=false, they provide full official component functionality.
When demo_mode=true, they simulate execution for local development.
"""

from .databricks_workspace_component import CustomDatabricksWorkspaceComponent
from .databricks_asset_bundle_component import CustomDatabricksAssetBundleComponent

__all__ = [
    "CustomDatabricksWorkspaceComponent",
    "CustomDatabricksAssetBundleComponent",
]
