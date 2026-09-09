# Changelog

## 2026-09-09 — Restore ignore_chown_errors after switching to rootful builds

### Fixed

- `demo.lightwell.build_app`'s generated `storage.conf` now sets
  `ignore_chown_errors = "true"` under `[storage.options]` again. Building
  as real root (`become: true`) still fails unpacking UBI base-image
  layers with `potentially insufficient UIDs or GIDs available in user
  namespace (requested 0:5 for /usr/bin/write) ... lchown: invalid
  argument`, because the AAP Execution Environment itself runs inside a
  restricted UID/GID map that doesn't include every ID (e.g. GID 5,
  `tty`) even for the container's root user. This option was part of the
  original 2026-08-29 fix but was dropped when the `storage.conf` was
  rewritten to point at isolated `graphroot`/`runroot` directories,
  leaving VFS layer extraction to fail on any unmapped ownership instead
  of ignoring it.

## 2026-09-09 — Build, tag, and push as root to avoid setgroups failure

### Fixed

- `demo.lightwell.build_app` now builds, tags, and pushes the application
  image with `become: true` (real root) instead of rootless Podman. A
  plain `RUN pip install ...` (no secret mount, `USER 0` already in
  effect) still failed with
  `error setting supplemental groups list: operation not permitted`,
  proving the earlier fixes were addressing symptoms of a deeper problem:
  Buildah's `chroot` isolation calls `setgroups()` unconditionally before
  every `RUN` instruction, and the kernel automatically denies that
  syscall in any unprivileged user namespace lacking a real subordinate
  UID/GID mapping -- exactly the single-ID rootless fallback this role
  intentionally forces (see the "Stop configuring subordinate IDs" entry
  below) to dodge the earlier `newuidmap` failure. This is a known
  Buildah bug fixed upstream in 1.45.0
  (<https://github.com/containers/buildah/pull/6961>), not available in
  this Execution Environment. Real root has no user-namespace restriction
  and genuine `CAP_SETGID`, so `setgroups()` succeeds.
- The now-removed subordinate-ID cleanup and `XDG_RUNTIME_DIR` setup
  (both rootless-only concerns) were dropped from `build_app` as dead
  code once builds run as root.
- The "tag" and "push" tasks now also set `CONTAINERS_STORAGE_CONF` to
  the same isolated `storage.conf` as the build task and run with
  `become: true`, fixing a latent bug where they previously read Podman's
  default (rootless) storage and would never have found an image built
  into the isolated root-owned graphroot.

## 2026-09-09 — Drop Podman build secret to avoid setgroups failure

### Fixed

- The application `Containerfile` no longer authenticates via
  `--mount=type=secret,id=netrc`; `demo.lightwell.build_app` now writes
  the `.netrc` directly into the build context (`{{ app_source_dir
  }}/.netrc`) and the Containerfile removes it within the same `RUN` that
  installs dependencies. The secret-mount path triggers the same
  `setgroups()` call that nested Podman inside an AAP Execution
  Environment cannot satisfy, independent of the `USER 0` change below --
  builds still failed with
  `error setting supplemental groups list: operation not permitted` at
  the `pip install` step even after that fix. Credentials still never
  reach the pushed image because the builder stage that holds them is
  discarded by the multi-stage build; `build_app`'s `always` block
  removes the on-disk `.netrc` regardless of build outcome.
- `extra_args` for the `podman_image` build task dropped the
  `--secret id=netrc,src=...` flag, keeping only `--isolation chroot`.

## 2026-09-09 — Build application image as root to avoid setgroups failure

### Fixed

- The application `Containerfile`'s builder stage now runs as `USER 0`
  instead of the base image's default non-root user. Buildah's `chroot`
  isolation still calls `setgroups()` to set the supplemental groups of
  the image's default user before running the `RUN` instruction, and
  that call fails inside an AAP Execution Environment's nested Podman
  (`error setting supplemental groups list: operation not permitted`).
  Root has no supplemental groups to set, so the call is skipped. The
  final stage still runs as `USER 1001`, so runtime behavior is
  unchanged; only the `COPY --from=builder` source path moved from
  `/opt/app-root/src/.local` to `/root/.local`, since `pip install --user`
  now installs into root's home directory.

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
