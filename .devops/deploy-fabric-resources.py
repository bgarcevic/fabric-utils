# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fabric-cicd==0.1.32",
#   "azure-identity",
# ]
# ///
import argparse
import os
import sys

from azure.identity import ClientSecretCredential
from fabric_cicd import (
    FabricWorkspace,
    append_feature_flag,
    change_log_level,
    publish_all_items,
)

# Force unbuffered output like `python -u`
sys.stdout.reconfigure(line_buffering=True, write_through=True)
sys.stderr.reconfigure(line_buffering=True, write_through=True)

# Enable debugging if defined in Azure DevOps pipeline
if os.getenv("SYSTEM_DEBUG", "false").lower() == "true":
    change_log_level("DEBUG")

# Accept parsed arguments
parser = argparse.ArgumentParser(description="Process Azure Pipeline arguments.")
parser.add_argument("--workspace_id", type=str)
parser.add_argument("--workspace_name", type=str)
parser.add_argument("--environment", type=str)
parser.add_argument("--repository_directory", type=str)
parser.add_argument("--items_in_scope", type=str)
parser.add_argument("--client_id", type=str)
parser.add_argument("--client_secret", type=str)
parser.add_argument("--tenant_id", type=str)
args = parser.parse_args()

# Feature flags
#
# Shortcuts are often environment-specific and can fail to (re)publish in PROD if they already exist
# or point to restricted/unavailable targets. Gate shortcut publishing by environment.
if (args.environment or "").upper() in {"DEV", "STG"}:
    append_feature_flag("enable_shortcut_publish")

append_feature_flag("enable_environment_variable_replacement")

# Validate workspace arguments
if not (args.workspace_id or args.workspace_name):
    parser.error("Either --workspace_id or --workspace_name must be provided.")

# Validate SPN arguments - if any are provided, all must be provided
spn_args = [args.client_id, args.client_secret, args.tenant_id]
if any(spn_args) and not all(spn_args):
    parser.error(
        "All SPN credential arguments (client_id, client_secret, tenant_id) must be provided together."
    )

# Initialize credential
token_credential = None
if all(spn_args):
    token_credential = ClientSecretCredential(
        client_id=args.client_id,
        client_secret=args.client_secret,
        tenant_id=args.tenant_id,
    )

# Initialize the FabricWorkspace object with the required parameters
workspace_kwargs = {
    "workspace_id": args.workspace_id,
    "workspace_name": args.workspace_name,
    "environment": args.environment,
    "repository_directory": args.repository_directory,
    "token_credential": token_credential,
}

# Add item_type_in_scope if provided
if args.items_in_scope:
    workspace_kwargs["item_type_in_scope"] = args.items_in_scope.split(",")

target_workspace = FabricWorkspace(**workspace_kwargs)

publish_all_items(target_workspace)
