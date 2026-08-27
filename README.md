# Lightwell + Ansible Patch Pipeline Demo

A hands-on demo of a fully automated Python dependency patch pipeline:

**Red Hat & IBM [Lightwell Network](https://www.redhat.com/en/lightwell)**
supplies remediated (`.rhlw`-patched) Python packages, **Renovate** watches
for and proposes those patches as pull requests, and **Ansible Automation
Platform (AAP)** builds, tests, promotes, and -- if something goes wrong --
rolls back the application. GitHub events are routed through a single
**Event-Driven Ansible (EDA) Event Stream** rather than per-job-template
webhooks, and status is reported back to GitHub using a token minted from
a GitHub App installation instead of a static personal access token.

## Why this exists

Enterprises running long-lived, pinned versions of open source libraries
need a way to consume security patches without waiting on (or being
forced into) a disruptive major-version upgrade. Lightwell Network
delivers exactly that: backported, signed patches for the versions you
already run. This repo demonstrates how to wire that patch feed into a
real, auditable deployment pipeline instead of installing patches by hand.

## Architecture

```mermaid
flowchart TD
    RenovateBot["Renovate Bot"] -->|"Scans app/requirements.txt against\nLightwell Remediated index"| DetectPatch["Detects new .rhlw patch\n(e.g. PyYAML 6.0.2.rhlw-00001)"]
    DetectPatch -->|"Creates PR"| GitHubPR["GitHub Pull Request"]
    GitHubPR -->|"Webhook (pull_request event)"| EventStream["EDA Event Stream\n(GitHub Event Stream credential)"]
    EventStream --> Rulebook["Rulebook Activation\nrulebooks/lightwell_webhook.yml"]
    Rulebook -->|"run_job_template"| AAP_Test["AAP Job Template:\nLightwell - Build & Test"]
    AAP_Test --> UnifiedDeploy["Unified Playbook:\nplaybooks/deploy.yml"]
    UnifiedDeploy --> BuildImg["Build Container Image\n(Podman)"]
    BuildImg --> DeployTest["Deploy to Test\n(Podman on RHEL)"]
    DeployTest --> HealthTest["Health Check\n(Test Environment)"]
    HealthTest -->|"Pass"| ApprovePR["report_status role posts to PR:\nChecks Pass (GitHub App token)"]
    HealthTest -->|"Fail"| FailPR["report_status role posts to PR:\nChecks Fail (GitHub App token)"]
    ApprovePR -->|"Reviewer approves & merges"| MergeMain["Merge to main"]
    MergeMain -->|"Webhook (push event)"| EventStream
    Rulebook -->|"run_job_template"| AAP_Prod["AAP Job Template:\nLightwell - Deploy Prod"]
    AAP_Prod --> UnifiedDeploy
    UnifiedDeploy --> DeployProd["Deploy to Prod\n(Podman on RHEL)"]
    DeployProd --> HealthProd["Health Check\n(Prod Environment)"]
    HealthProd -->|"Pass"| Done["Deployment Complete"]
    HealthProd -->|"Fail"| Rollback["Automatic Rollback to\nPrevious Version"]
```

## Repository layout

```
ansible-lightwell/
├── app/                    # Demo Flask application (PyYAML + Jinja2)
│   ├── app.py
│   ├── requirements.txt    # Points at the Lightwell Remediated index
│   ├── templates/          # Jinja2 dashboard templates
│   ├── config/             # YAML config loaded by PyYAML
│   ├── static/             # Lightwell-themed CSS
│   ├── tests/              # pytest suite
│   └── Containerfile
├── playbooks/
│   ├── deploy.yml          # Unified build & deploy (build on test, rollback on prod)
│   └── rollback.yml        # Standalone/manual rollback
├── collections/
│   ├── requirements.yml    # Third-party collections (containers.podman, ansible.eda, etc.)
│   └── ansible_collections/demo/lightwell/   # Our own demo.lightwell collection
│       ├── galaxy.yml
│       └── roles/
│           ├── build_app/     # Build & push the container image via Podman
│           ├── deploy_app/    # Deploy the container via Podman + systemd
│           ├── health_check/  # Poll /healthz with retries
│           ├── rollback/      # Restore the previous image
│           └── report_status/ # Post commit status back to GitHub via a GitHub App token
├── eda/
│   ├── README.md           # How the rulebook routes GitHub events
│   └── rulebooks/lightwell_webhook.yml   # Routes PR/push events to job templates
├── inventory/               # test/prod host groups and vars
├── renovate.json           # Renovate config targeting the Lightwell index
├── docs/aap-setup.md       # Full AAP configuration walkthrough
└── .pre-commit-config.yaml, .ansible-lint, .yamllint.yml, .gitleaks.toml, ruff.toml
```

## The demo application

A small Flask dashboard that uses both target libraries in a way that's
visible in the UI, not just in `requirements.txt`:

- **PyYAML** loads `app/config/app_config.yaml` -- service metadata,
  feature flags, and a patch timeline -- at startup.
- **Jinja2** (via Flask) renders the dashboard itself, including a live
  table of installed dependency versions. Any version carrying the
  Lightwell `.rhlw-0000X` suffix is called out with a "Lightwell Patched"
  badge, so a Renovate-driven version bump becomes visually obvious.

Run it locally:

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py
# visit http://localhost:8080
```

Run the tests:

```bash
cd app
pytest
```

## Path-based filtering: only deploy when `app/` changes

Not every commit or PR needs a build. A change to `README.md` or
`renovate.json` shouldn't burn CI minutes building and deploying the
application. Both the push (prod) and pull-request (test) code paths are
filtered the same way, entirely inside [`playbooks/deploy.yml`](playbooks/deploy.yml):

### Push events (production deploys)

The first `pre_task` block in the deploy play calls the GitHub
[Commits API](https://docs.github.com/en/rest/commits/commits#get-a-commit)
for `app_git_sha` (the pushed commit) to get its list of changed files, and
ends the play early -- posting a "Skipped" success status back to the
commit -- when nothing in `app/` was modified.

### Pull-request events (test builds)

GitHub `pull_request` webhook payloads don't include a list of changed
files (only an integer count), so this can't be checked from the event
payload alone. The first task block in the build play calls the GitHub
[Pull Request Files API](https://docs.github.com/en/rest/pulls/pulls#list-pull-requests-files)
to get the changed file list, and ends the play early (posting a "Skipped"
success status back to the PR) when nothing in `app/` was modified.

### Why filtering lives in the playbook, not the EDA rulebook

An earlier version filtered push events at the EDA layer with a custom
`demo.lightwell.path_filter` event filter plugin, so unwanted pushes never
launched an AAP job at all. That plugin lived in this project's own
collection -- but Decision Environments don't mount local collections, so
it was never actually available to the Rulebook Activation in a real AAP
deployment, only in local `ansible-rulebook` testing. It's been removed,
and [`rulebooks/lightwell_webhook.yml`](rulebooks/lightwell_webhook.yml)
no longer filters by path at all; every matching `pull_request`/`push`
event launches a job template, and that job template's playbook decides
whether to actually build/deploy.

### Alternatives considered

| Approach | Pros | Cons |
| --- | --- | --- |
| **EDA event filter plugin** (previous push approach) | Cheapest: no AAP job is launched at all. | Requires a custom collection plugin, which Decision Environments don't mount in practice; doesn't work for PR events either, since the payload lacks file paths. |
| **GitHub Actions `paths:` filter → `repository_dispatch`** | GitHub-native path filtering; bullet-proof. | Adds a second trigger layer and couples the pipeline to Actions. |
| **Early `meta: end_play` in the playbook** (current approach, both cases) | Works regardless of payload content; needs no plugin support from the Decision Environment; can post an explanatory status back to GitHub. | A job is still launched (albeit short-lived); the GitHub API call adds ~1 s. |

The chosen approach trades a small amount of AAP job overhead for a
filtering mechanism that only depends on the playbook's own GitHub API
calls -- no reliance on plugins the Decision Environment may not have.

## The patch pipeline, end to end

1. **Renovate** (configured in [`renovate.json`](renovate.json)) scans
   `app/requirements.txt` against the Lightwell Remediated repository
   (`packages.redhat.com/lightwell/python/remediated/simple`) as well as
   PyPI. When a new `.rhlw` patch is published for PyYAML or Jinja2, it
   opens a pull request bumping the pinned version.
2. The PR's `pull_request` webhook lands on a single **EDA Event Stream**,
   which forwards it to the `Lightwell Patch Pipeline Router` rulebook
   activation ([`rulebooks/lightwell_webhook.yml`](rulebooks/lightwell_webhook.yml)).
   The rulebook matches the `opened`/`synchronize`/`reopened` condition and
   launches AAP's **Lightwell - Build & Test** job template, which runs
   [`playbooks/deploy.yml`](playbooks/deploy.yml) with `app_environment: test`:
   build the image from the PR branch, deploy it to `test` via Podman, and run
   a strict health check against `/healthz`.
3. The playbook's `demo.lightwell.report_status` role posts the result
   back to the PR as a GitHub commit status, authenticating with a token
   minted on demand from a GitHub App installation (via the
   `GitHub App Installation Access Token Lookup` credential) -- no static
   PAT is stored in AAP.
4. Branch protection on `main` requires that check to pass and requires at
   least one approving review before the PR can merge.
5. Merging to `main` sends a `push` webhook to the same Event Stream; the
   rulebook matches the `refs/heads/main` condition and launches AAP's
   **Lightwell - Deploy Prod** job template, which runs
   [`playbooks/deploy.yml`](playbooks/deploy.yml) with `app_environment: prod`:
   deploy the same tested image to `prod` and health-check it again.
6. If the prod health check fails, the playbook automatically invokes the
   `demo.lightwell.rollback` role, which restores the previously running image and
   re-verifies health -- no manual intervention required for the common
   case. Either way, `demo.lightwell.report_status` posts the final result
   back to the commit.

Full AAP resource setup (credentials, project, inventory, job templates,
the GitHub App, Event Stream, and rulebook activation) is documented step
by step in [`docs/aap-setup.md`](docs/aap-setup.md).

## Lightwell Network configuration

`app/requirements.txt` adds the Lightwell Remediated repository as an
extra index:

```
--extra-index-url https://packages.redhat.com/lightwell/python/remediated/simple
```

Authentication uses a Lightwell Network service account (format
`<account-id>|<service-account-name>` plus a token). **These credentials
are never committed to this repository.** They are injected at build time
as a Podman build secret (see [`app/Containerfile`](app/Containerfile) and
[`demo.lightwell.build_app`](collections/ansible_collections/demo/lightwell/roles/build_app))
and supplied to Renovate and AAP as secrets/credentials -- see
[`renovate.json`](renovate.json)'s `hostRules` and
[`docs/aap-setup.md`](docs/aap-setup.md) section 1a.

### Where the Lightwell service account credentials must live

The same username/token pair is needed in exactly three places, and
nowhere else:

| Location | Purpose | Never do this |
| --- | --- | --- |
| **AAP credential** of type `Lightwell Network` (custom credential type, [`docs/aap-setup.md`](docs/aap-setup.md) section 1a) | Injected into the `build_app` role run as `lightwell_username` / `lightwell_password` extra vars, written to a short-lived `.netrc` used only for the Podman build, then deleted. | Do not put these values in `group_vars`, role `defaults/`, or any extra-vars file checked into git. |
| **GitHub repository secrets** `LIGHTWELL_USERNAME` and `LIGHTWELL_TOKEN` | Referenced by [`renovate.json`](renovate.json)'s `hostRules` (`{{ secrets.LIGHTWELL_USERNAME }}` / `{{ secrets.LIGHTWELL_TOKEN }}`) so Renovate can query the Lightwell Remediated index for new patches. | Do not paste the raw values into `renovate.json` or any onboarding config committed to the repo. |
| **Local developer machine**, `~/.netrc`, only if running `pip install` against the Lightwell Remediated index outside of a container build | Lets `pip` on your workstation resolve `.rhlw` packages directly for local testing. | Do not commit your `~/.netrc`, and never copy it into the repo working directory (`.gitignore` already excludes any stray `.netrc`). |

`.gitleaks.toml` includes custom rules that specifically detect the
Lightwell username format (`<id>|<name>`), Lightwell JWT tokens, and
`.netrc` credential blocks, so an accidental commit of any of the above is
caught by the pre-commit hook before it ever reaches git history.

## Code quality: linting and pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com/) to enforce the same
checks locally that a real enterprise pipeline would run in CI:

| Tool | Purpose |
| --- | --- |
| [gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning, including custom rules for Lightwell service account tokens and `.netrc` blocks ([`.gitleaks.toml`](.gitleaks.toml)) |
| [ansible-lint](https://ansible.readthedocs.io/projects/lint/) | Enforces the `production` rule profile across all playbooks and roles ([`.ansible-lint`](.ansible-lint)) |
| [yamllint](https://yamllint.readthedocs.io/) | YAML style consistency ([`.yamllint.yml`](.yamllint.yml)) |
| [ruff](https://docs.astral.sh/ruff/) | Python linting + formatting for the Flask app ([`ruff.toml`](ruff.toml)) |

Set up once per clone:

```bash
pip install pre-commit
pre-commit install
```

Run against the whole repo at any time:

```bash
pre-commit run --all-files
```

## Prerequisites for a full live run

- A GitHub repository with webhooks enabled and branch protection
  configured on `main`.
- A GitHub App installed on the repository (commit-status write access)
  for AAP to authenticate as when posting status checks -- see
  [`docs/aap-setup.md`](docs/aap-setup.md) section 1b.
- An AAP instance (2.5+) with Event-Driven Ansible enabled and reachable
  from GitHub -- see [`docs/aap-setup.md`](docs/aap-setup.md).
- Two Podman-capable RHEL hosts (or host groups), one for `test` and one
  for `prod`.
- A container registry both AAP and the target hosts can reach (default:
  `quay.io/lightwell-demo`).
- A Lightwell Network service account.
