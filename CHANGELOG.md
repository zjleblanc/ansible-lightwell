# Changelog

## 2026-08-27 — Add ansible.cfg for local collection resolution

### Added

- `ansible.cfg` setting `collections_path` to `./collections:~/.ansible/collections:/usr/share/ansible/collections`
  so `demo.lightwell.*` roles/plugins resolve for local tooling
  (`ansible-lint`, `ansible-playbook`, `ansible-rulebook`). The two default
  entries are kept alongside the local path (rather than replaced) so this
  file doesn't shadow whatever collections an AAP Execution/Decision
  Environment bakes in when it mounts the project directory and picks up
  this same `ansible.cfg`.

## 2026-08-27 — Move path filtering into the deploy playbook

### Changed

- Path filtering for both push (prod) and pull-request (test) events now
  happens entirely in `playbooks/deploy.yml` via GitHub API calls (Commits
  API for pushes, Pull Request Files API for PRs), each ending the play
  early when no `app/` files changed.
- `rulebooks/lightwell_webhook.yml` no longer filters events by path; it
  launches a job template for every matching `pull_request`/`push` event
  and lets the playbook decide whether to build/deploy.
- `README.md` and `rulebooks/README.md` updated to document the decision
  and drop the "hybrid filtering" alternatives table entry for the EDA
  filter plugin.

### Removed

- EDA event filter plugin `demo.lightwell.path_filter`. Decision
  Environments don't mount local collections, so the plugin was never
  actually available to a Rulebook Activation outside of local
  `ansible-rulebook` testing.

## 2026-08-27 — Implement path-based filtering for GitHub events

### Added

- EDA event filter plugin `demo.lightwell.path_filter` to flag events containing changes in specified paths.
- Early path-check logic in `playbooks/deploy.yml` to query the GitHub PR files API and skip builds for non-app changes.

### Changed

- `rulebooks/lightwell_webhook.yml` now filters `pull_request` and `push` events to only trigger when files in `app/` are modified.
- `README.md` and `rulebooks/README.md` updated to document the hybrid filtering strategy and alternatives considered.

### Fixed

- Rulebook condition syntax to use `is defined` / `is not defined` instead of unsupported Jinja filters.
- Corrected collection path for EDA event filter plugin to `extensions/eda/plugins/event_filter/` to ensure discovery by `ansible-rulebook`.
- Moved `ansible_collections` to the repository root for better discovery by AAP EDA activations.

## 2026-08-26 — Add Event-Driven Ansible integration and status reporting

### Added

- Event-Driven Ansible (EDA) rulebook (`rulebooks/lightwell_webhook.yml`) to route GitHub `pull_request` and `push` events to the appropriate job templates.
- Local Ansible collection role `demo.lightwell.report_status` to post `pending`, `success`, and `failure` commit statuses back to GitHub using a GitHub App installation token.
- Cursor rules in `.cursor/rules/` for persisting AAP integration patterns and comment style standards.
- Documentation in `docs/aap-setup.md` for simplified event routing using HMAC and the GitHub App installation token lookup credential.

### Changed

- `playbooks/deploy_test.yml` and `playbooks/deploy_prod.yml` to report status back to GitHub at start and completion.
- `README.md` and `docs/aap-setup.md` to reflect the EDA-based architecture and GitHub App authentication flow.

## 2026-08-26 — Scaffold the Lightwell Ansible patch pipeline demo

### Added

- Flask demo application (`app/`) with a Lightwell-themed dashboard that
  loads configuration via PyYAML and renders via Jinja2, a `/healthz`
  endpoint, a pytest suite, and a multi-stage `Containerfile` that
  authenticates to the Lightwell Network remediated repository at build
  time via a Podman build secret.
- Ansible roles (`build_app`, `deploy_app`, `health_check`, `rollback`)
  and playbooks (`deploy_test.yml`, `deploy_prod.yml`, `rollback.yml`)
  implementing build, deploy, health-check, and automatic-rollback across
  `test` and `prod` Podman inventories.
- `renovate.json` configured to watch for Lightwell Remediated `.rhlw`
  patches to PyYAML and Jinja2 alongside PyPI.
- `docs/aap-setup.md` documenting the Ansible Automation Platform
  credentials, project, inventory, job templates, and GitHub webhook
  wiring needed to run the pipeline end to end.
- Enterprise linting and pre-commit tooling: gitleaks (with custom rules
  for Lightwell credential formats), ansible-lint (`production` profile),
  yamllint, and ruff, plus a `.gitignore` for secrets and local caches.
- Top-level `README.md` describing the architecture and end-to-end patch
  flow from Renovate PR to prod rollout.
