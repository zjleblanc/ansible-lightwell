"""Lightwell Patch Pipeline Demo Flask dashboard."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml
from flask import Flask, jsonify, render_template
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

APP_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = APP_ROOT / "config" / "app_config.yaml"
REQUIREMENTS_PATH = APP_ROOT / "requirements.txt"

TRACKED_PACKAGES = ("Flask", "PyYAML", "Jinja2", "gunicorn", "Pygments")

LIGHTWELL_SUFFIX_RE = re.compile(r"\.rhlw-(?P<patch_id>\w+)$")


def load_config() -> dict[str, Any]:
    """Load the application's YAML configuration file via PyYAML."""
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def parse_lightwell_version(version: str) -> tuple[str, str | None]:
    """Split a version string into (base_version, rhlw_patch_id).

    Lightwell-remediated wheels append a `.rhlw-<id>` suffix to the
    upstream version, e.g. "6.0.2.rhlw-00001". Returns (version, None)
    when no such suffix is present.
    """
    match = LIGHTWELL_SUFFIX_RE.search(version)
    if not match:
        return version, None
    return version[: match.start()], match.group("patch_id")


def get_package_versions(tracked_deps: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Report installed versions of tracked dependencies, annotated with
    Lightwell provenance (from the version string) and role metadata from
    app_config.yaml."""
    dep_by_name = {dep["name"]: dep for dep in (tracked_deps or [])}
    versions = []
    for package_name in TRACKED_PACKAGES:
        try:
            raw_version = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            raw_version = "unknown"
        base_version, patch_id = parse_lightwell_version(raw_version)
        versions.append(
            {
                "name": package_name,
                "version": base_version,
                "is_lightwell": patch_id is not None,
                "lightwell_patch_id": patch_id,
                "role": dep_by_name.get(package_name, {}).get("role", ""),
            }
        )
    return versions


def get_requirements_snippet() -> dict[str, str]:
    """Render app/requirements.txt as syntax-highlighted HTML via Pygments."""
    source = REQUIREMENTS_PATH.read_text(encoding="utf-8")
    # No dedicated pip-requirements lexer ships with Pygments; "properties"
    # (key=value, # comments) highlights the name==version syntax closely enough.
    lexer = get_lexer_by_name("properties")
    formatter = HtmlFormatter(style="monokai", cssclass="highlight")
    return {
        "html": highlight(source, lexer, formatter),
        "css": formatter.get_style_defs(".highlight"),
    }


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["CONFIG_DATA"] = load_config()

    @app.context_processor
    def inject_github_context() -> dict[str, Any]:
        """Expose the repo and deployed commit SHA to every template."""
        return {
            "github_repo": os.environ.get("GITHUB_REPO", ""),
            "app_git_sha": os.environ.get("APP_GIT_SHA", ""),
            "github_pr_number": os.environ.get("GITHUB_PR_NUMBER", ""),
            "app_env": os.environ.get("APP_ENVIRONMENT", "prod"),
        }

    @app.get("/")
    def dashboard():
        config_data = app.config["CONFIG_DATA"]
        tracked_deps = config_data.get("dependencies", {}).get("tracked", [])
        package_versions = get_package_versions(tracked_deps)
        return render_template(
            "dashboard.html",
            service=config_data.get("service", {}),
            patch_source=config_data.get("patch_source", {}),
            package_versions=package_versions,
            lightwell_count=sum(1 for pkg in package_versions if pkg["is_lightwell"]),
            tracked_count=len(package_versions),
            patch_timeline=config_data.get("patch_timeline", []),
            requirements_snippet=get_requirements_snippet(),
            now=datetime.now(UTC),
        )

    @app.get("/healthz")
    def healthz():
        service_name = app.config["CONFIG_DATA"].get("service", {}).get("name", "unknown")
        return jsonify(
            {
                "status": "ok",
                "service": service_name,
                "timestamp": datetime.now(UTC).isoformat(),
                "packages": get_package_versions(),
            }
        )

    @app.get("/api/config")
    def api_config():
        return jsonify(app.config["CONFIG_DATA"])

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
