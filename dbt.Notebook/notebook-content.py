# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.11"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "8c007b20-ca24-4f08-8c54-49ae03309cd2",
# META       "default_lakehouse_name": "duos_lakehouse",
# META       "default_lakehouse_workspace_id": "9e84146a-5120-4364-a068-ab5bb73b0908",
# META       "known_lakehouses": [
# META         {
# META           "id": "8c007b20-ca24-4f08-8c54-49ae03309cd2"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# DO NOT CHANGE VARIABLE NAMES UNLESS YOU KNOW WHAT YOU ARE DOING
is_prod = False
git_tag = "main"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

!pip install dbt-fabric

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import os
import json
vault_url = 'https://duospowerbi.vault.azure.net/'

azure_devops_pat = notebookutils.credentials.getSecret(vault_url, 'AZURE-DEVOPS-PAT')
os.environ["DBT_CLIENT_SECRET"] = notebookutils.credentials.getSecret(vault_url, 'FABRIC-CLIENT-SECRET')

if is_prod:
    os.environ["DBT_TARGET"] = "prod"
else:
    os.environ["DBT_TARGET"] = "staging"

print(f"DBT_TARGET: {os.environ['DBT_TARGET']}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

NOTEBOOK_BASE_PATH = os.getcwd()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

# Clone repository using PAT
import subprocess
import shutil


def _fail(message: str, *, details: dict | None = None) -> None:
    """Fail the notebook so a Fabric Data Pipeline Notebook activity is marked as Failed."""
    if details:
        print("DETAILS:")
        print(json.dumps(details, indent=2, sort_keys=True, default=str))
    raise RuntimeError(message)

git_url = f"https://{azure_devops_pat}@dev.azure.com/duosgroup/_git/Business%20Intelligence"
repo_name = "Business%20Intelligence"

# Remove existing repository if it exists
if os.path.exists(repo_name):
    print(f"Removing existing repository '{repo_name}'...")
    shutil.rmtree(repo_name)

# Clone the repository
print(f"Cloning repository '{repo_name}'...")
result = subprocess.run(
    ['git', 'clone', '--branch', git_tag, '--depth', '1', git_url],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    stderr_safe = result.stderr.replace(azure_devops_pat, '***PAT***')
    print(stderr_safe)

if result.returncode != 0:
    _fail(
        "Git clone failed",
        details={
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": (result.stderr or "").replace(azure_devops_pat, "***PAT***"),
        },
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

# Change to the cloned repository directory
repo_path = os.path.join(NOTEBOOK_BASE_PATH, repo_name)
dbt_dir = os.path.join(repo_path, 'dbt')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

# Run dbt deps and job
from dbt.cli.main import dbtRunner

# Change to dbt directory
os.chdir(dbt_dir)

# Initialize the dbtRunner
dbt = dbtRunner()


def _run_dbt_step(step_name: str, args: list[str]):
    print(f"\nRunning {step_name}...")
    res = dbt.invoke(args)
    print(f"Success: {res.success}")
    if not res.success:
        _fail(
            f"dbt step failed: {step_name}",
            details={
                "step": step_name,
                "args": args,
                "exception": getattr(res, "exception", None),
            },
        )
    return res

deps_result = _run_dbt_step("dbt deps", ["deps"])
debug_result = _run_dbt_step("dbt debug", ["debug"])
run_result = _run_dbt_step("dbt build", ["build"])

step_summary = {
    "git_tag": git_tag,
    "dbt_target": os.environ.get("DBT_TARGET"),
    "steps": [
        {"name": "dbt deps", "success": deps_result.success},
        {"name": "dbt debug", "success": debug_result.success},
        {"name": "dbt build", "success": run_result.success},
    ],
}

# You can also run with specific arguments
# run_result = dbt.invoke(["run", "--select", "my_model"])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

# Generate static dbt docs (all-in-one HTML file)
target_dir = os.path.join(dbt_dir, 'target')
lakehouse_path = '/lakehouse/default/Files/dbt'
os.makedirs(lakehouse_path, exist_ok=True)

docs_result = _run_dbt_step("dbt docs generate --static", ["docs", "generate", "--static"])
print("✓ Static documentation generated successfully")
step_summary["steps"].append({"name": "dbt docs generate --static", "success": docs_result.success})

# The static index.html is in the 'target' folder
static_html = os.path.join(target_dir, 'static_index.html')

# Copy the single static HTML file to lakehouse
if os.path.exists(static_html):
    dst = os.path.join(lakehouse_path, 'dbt_docs.html')
    shutil.copy2(static_html, dst)
    print(f"✓ Static documentation saved to: {dst}")
else:
    _fail(
        "Static documentation file not found after successful docs generation",
        details={"expected_path": static_html, "target_dir": target_dir},
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

manifest_src = os.path.join(target_dir, "manifest.json")
run_results_src = os.path.join(target_dir, "run_results.json")

if os.path.exists(manifest_src):
    shutil.copy2(manifest_src, os.path.join(lakehouse_path, "manifest.json"))

if os.path.exists(run_results_src):
    shutil.copy2(run_results_src, os.path.join(lakehouse_path, "run_results.json"))

print(f"Saved dbt state to: {lakehouse_path}")

print("\nFINAL_STEP_SUMMARY:")
print(json.dumps(step_summary, indent=2, sort_keys=True))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
