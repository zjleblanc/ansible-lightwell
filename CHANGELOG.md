# Changelog

## 2026-09-09 — Stop configuring subordinate IDs to avoid newuidmap failure

### Fixed

- `demo.lightwell.build_app` no longer writes subordinate UID/GID ranges to
  `/etc/subuid`/`/etc/subgid` for the build user, and now actively removes
  any pre-existing entries instead. Configuring a subordinate ID range is
  exactly what makes Podman's rootless setup invoke
  `newuidmap`/`newgidmap` to build the namespace mapping; when those
  binaries lack the capabilities needed inside an AAP Execution
  Environment, that call hard-fails
  (`newuidmap: write to uid_map failed: Operation not permitted`) even
  though the VFS storage driver is otherwise in effect. With no
  subordinate ID range configured, Podman falls back to its single-ID
  rootless mapping (no `newuidmap` call at all), and the existing
  `ignore_chown_errors = "true"` + `driver = "vfs"` storage.conf settings
  already tolerate the resulting squashed ownership during layer
  extraction.

## 2026-09-09 — Fix VFS driver override causing newuidmap failure

### Fixed

- `demo.lightwell.build_app` now points the temporary build `storage.conf`
  at fresh, isolated `graphroot`/`runroot` directories instead of the
  default storage path. Previously, Podman found a pre-existing `overlay`
  storage database at the default path and silently overwrote the
  role's `driver = "vfs"` setting back to `overlay`
  (`User-selected graph driver "vfs" overwritten by graph driver
  "overlay" from database`), which then required user-namespace UID
  mapping that fails inside AAP Execution Environments
  (`newuidmap: write to uid_map failed: Operation not permitted`). With
  no pre-existing database in the isolated directories, the VFS driver
  now takes effect and namespace mapping is never attempted.

## 2026-09-09 — Report failure status instead of hanging pending on hard errors

### Fixed

- `playbooks/deploy.yml` no longer leaves the GitHub commit/PR check stuck
  in `pending` when the build or deploy/health-check/rollback sequence
  fails with an unhandled task error. The build step and the
  deploy-verify-rollback sequence are now wrapped in `block`/`rescue`
  (with `always` for the latter) so a `failure` status is always reported
  to `demo.lightwell.report_status` before the play fails, instead of the
  play aborting silently after only a `pending` status was posted.
- The build failure path re-raises after reporting so the AAP job itself
  is still marked failed, not just the GitHub check.

## 2026-09-09 — Fix newuidmap failure in nested Podman builds

### Fixed

- `demo.lightwell.build_app` now sets `driver = "vfs"` in the temporary
  storage.conf used for builds, avoiding Podman's automatic `overlay`
  driver selection, which requires `newuidmap`/`newgidmap` user-namespace
  setup that fails inside AAP Execution Environments
  (`newuidmap: write to uid_map failed: Operation not permitted`).
- The build task now also passes `--isolation chroot` directly via
  `extra_args`, rather than relying solely on the `BUILDAH_ISOLATION`
  environment variable, so isolation mode is applied consistently across
  `containers.podman` collection versions.

## 2026-08-29 — Fix nested Podman builds in AAP execution environments

### Fixed

- `demo.lightwell.build_app` now handles the common AAP Execution Environment
  failure unpacking UBI layers (`insufficient UIDs or GIDs available in user
  namespace`). The role configures subordinate ID ranges when privilege
  escalation is available, runs builds with `BUILDAH_ISOLATION=chroot`, and
  invokes Podman via a wrapper that passes `--storage-opt
  ignore_chown_errors=true`.

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
