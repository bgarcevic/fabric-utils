# fabric-utils (demo)

Demo repository for a **dbt notebook pattern in Microsoft Fabric** plus **Azure DevOps CI/CD templates** for validating dbt changes and deploying Fabric workspace items.

> Note: This repo contains example values in code (workspace names, URLs, etc.). The documentation below stays **public-safe** and uses placeholders.

## What’s included

- Fabric workspace item sources under [`fabric-workspaces/`](fabric-workspaces:1)
  - Demo notebook: [`fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py`](fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py:1)
- Azure DevOps pipelines and deployment script under [`.devops/`](.devops:1)
  - PR validation: [`.devops/dbt-ci-validation.yml`](.devops/dbt-ci-validation.yml:1)
  - Releases: [`.devops/release-staging.yml`](.devops/release-staging.yml:1), [`.devops/release-production.yml`](.devops/release-production.yml:1)
  - Fabric deploy helper: [`.devops/deploy-fabric-resources.py`](.devops/deploy-fabric-resources.py:1)
- Environment-specific replacement config (for Fabric item publishing): [`parameter.yml`](parameter.yml:1)

## How the notebook works

The notebook in [`notebook-content.py`](fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py:1) demonstrates a common “orchestrate dbt from Fabric” approach:

1. Installs dbt adapter (`dbt-fabric`) (see the `pip install` cell in [`notebook-content.py`](fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py:39)).
2. Retrieves runtime secrets using your preferred mechanism (the demo uses `notebookutils.credentials.getSecret(...)`).
3. Clones a git repo at a chosen ref (`git_tag`) (see clone logic in [`notebook-content.py`](fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py:84)).
4. Runs dbt steps via the Python CLI runner (`deps`, `debug`, `build`) (see [`_run_dbt_step()`](fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py:158)).
5. Generates **static dbt docs** and copies artifacts (docs, `manifest.json`, `run_results.json`) to the lakehouse file system (see docs + copy in [`notebook-content.py`](fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py:199)).

## CI/CD templates

### Pull request validation (dbt CI)

[`.devops/dbt-ci-validation.yml`](.devops/dbt-ci-validation.yml:1) is a PR-oriented pipeline that:

- Detects changed dbt model SQL files.
- Installs Python dependencies using `uv`.
- Ensures dbt connectivity/syntax (`dbt debug`, `dbt deps`, `dbt parse`).
- Runs `sqlfluff lint` against the changed files.

### Fabric releases (staging + production)

- [`.devops/release-staging.yml`](.devops/release-staging.yml:1) deploys on updates to `main` (path-filtered to `fabric-workspaces/*`).
- [`.devops/release-production.yml`](.devops/release-production.yml:1) deploys on tags matching `v*`.

Both call [`.devops/deploy-fabric-resources.py`](.devops/deploy-fabric-resources.py:1), which uses the `fabric-cicd` library to publish workspace items (see [`publish_all_items()`](.devops/deploy-fabric-resources.py:13)).

## Environment replacement (`parameter.yml`)

[`parameter.yml`](parameter.yml:1) defines find/replace rules applied during publishing to make the same Fabric item sources deployable across environments.

In this demo it includes:

- Regex replacements for Fabric notebook metadata IDs (default lakehouse + workspace IDs) (see rules in [`parameter.yml`](parameter.yml:6)).
- An environment-specific switch for `is_prod` (see [`parameter.yml`](parameter.yml:31)).
- A regex replacement for `git_tag` so STG/PROD can deploy from an environment-provided ref (see [`parameter.yml`](parameter.yml:38)).

## Quickstart (template-level)

1. **Fabric notebook**
   - Import/open [`fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py`](fabric-workspaces/data-and-analytics/dbt.Notebook/notebook-content.py:1) in Fabric.
   - Replace the demo secret retrieval + repo clone pieces with your own approach (Managed Identity, Key Vault, or workspace secrets).

2. **Azure DevOps**
   - Create a pipeline from [`.devops/dbt-ci-validation.yml`](.devops/dbt-ci-validation.yml:1) for PR validation.
   - Create release pipelines from [`.devops/release-staging.yml`](.devops/release-staging.yml:1) and [`.devops/release-production.yml`](.devops/release-production.yml:1).
   - Configure an Azure service connection suitable for Fabric deployments (used by the `AzureCLI@2` steps).
   - Update workspace names and repository directories in the YAML parameters to match your repo.

## Repo layout

```
.
├── .devops/                         # Azure DevOps pipeline templates + deploy script
├── fabric-workspaces/               # Fabric workspace item sources (Notebook, etc.)
├── parameter.yml                    # Environment replacement rules for publishing
└── LICENSE
```

## License

MIT — see [`LICENSE`](LICENSE:1).

