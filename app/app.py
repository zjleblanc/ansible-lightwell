"""Lightwell Patch Pipeline Demo Flask dashboard."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml
from flask import Flask, jsonify, render_template

APP_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = APP_ROOT / "config" / "app_config.yaml"

TRACKED_PACKAGES = ("Flask", "PyYAML", "Jinja2", "gunicorn")


def load_config() -> dict[str, Any]:
    """Load the application's YAML configuration file via PyYAML."""
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def get_package_versions() -> list[dict[str, Any]]:
    """Report installed versions of tracked dependencies."""
    versions = []
    for package_name in TRACKED_PACKAGES:
        try:
            version = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            version = "unknown"
        versions.append(
            {
                "name": package_name,
                "version": version,
                "is_patched": ".rhlw" in version,
            }
        )
    return versions


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["CONFIG_DATA"] = load_config()

    @app.get("/")
    def dashboard():
        config_data = app.config["CONFIG_DATA"]
        return render_template(
            "dashboard.html",
            service=config_data.get("service", {}),
            features=config_data.get("features", {}),
            dependencies=config_data.get("dependencies", {}).get("tracked", []),
            patch_timeline=config_data.get("patch_timeline", []),
            package_versions=get_package_versions(),
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
