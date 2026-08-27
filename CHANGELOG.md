# Changelog

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
