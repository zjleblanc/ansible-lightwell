# Lightwell Patch Pipeline Demo App

A small Flask dashboard used to demo the Lightwell + Ansible patch pipeline.
It exercises both target libraries in a way that's visible in the UI, not
just in `requirements.txt`:

- **PyYAML** loads `config/app_config.yaml` -- service metadata, feature
  flags, and a patch timeline -- at startup.
- **Jinja2** (via Flask) renders the dashboard, including a live table of
  installed dependency versions. Any version carrying the Lightwell
  `.rhlw-0000X` suffix is called out with a "Lightwell Patched" badge, so a
  Renovate-driven version bump becomes visually obvious.
- **Pygments** syntax-highlights `requirements.txt` for display on the
  dashboard.

See the root [README.md](../README.md) for the full patch pipeline story
(Renovate, EDA, AAP) and [docs/aap-setup.md](../docs/aap-setup.md) for AAP
resource setup.

## Directory layout

```
app/
├── app.py                  # Flask application (routes + helpers)
├── Containerfile           # Multi-stage UBI9/Python 3.12 image
├── requirements.txt        # Runtime deps (Lightwell index primary, PyPI fallback)
├── requirements-dev.txt    # Runtime deps + pytest
├── pytest.ini              # pytest config
├── config/
│   └── app_config.yaml     # Service metadata, features, patch timeline
├── templates/
│   ├── base.html           # Layout, nav, footer
│   └── dashboard.html      # Dashboard content
├── static/
│   └── style.css           # Dark Lightwell-themed CSS
└── tests/
    └── test_app.py         # Route tests
```

## Routes

| Method | Path           | Response                                                    |
| ------ | -------------- | ------------------------------------------------------------ |
| `GET`  | `/`            | HTML dashboard                                                |
| `GET`  | `/healthz`     | JSON health status: `{status, service, timestamp, packages}` |
| `GET`  | `/api/config`  | Full YAML config as JSON                                      |

## Local development

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py
# visit http://localhost:8080
```

The port defaults to `8080` and can be overridden with the `PORT`
environment variable.

`requirements.txt` sets the Lightwell Remediated repository as the primary
package index, with PyPI as a fallback. If you need to resolve `.rhlw`
packages locally (outside of a container build), authenticate via
`~/.netrc` with your Lightwell Network service account credentials. Never
commit that file -- see the root README's
[credential locations table](../README.md#where-the-lightwell-service-account-credentials-must-live)
for where these secrets are allowed to live.

## Running tests

```bash
cd app
pytest
```

`pytest.ini` points `pytest` at the `tests/` directory and adds `app/` to
`pythonpath`. The suite covers the dashboard returning 200, `/healthz`
reporting `ok`, and `/api/config` returning service metadata.

## Container build

[`Containerfile`](Containerfile) builds a multi-stage image from
`registry.access.redhat.com/ubi9/python-312:latest`:

- The builder stage installs dependencies with `pip install --user`,
  authenticating against the Lightwell index via a BuildKit `netrc` build
  secret (`--mount=type=secret,id=netrc`) so credentials never land in an
  image layer.
- The runtime stage copies the installed packages and app code, runs as
  non-root `USER 1001`, exposes port `8080`, and serves via
  `gunicorn --bind 0.0.0.0:8080 --workers 2 app:app`.
- A `HEALTHCHECK` polls `/healthz` every 30s.

This image is built and deployed by the Ansible collection roles
(`demo.lightwell.build_app` / `demo.lightwell.deploy_app`), not by a
Makefile or compose file in this repo.
