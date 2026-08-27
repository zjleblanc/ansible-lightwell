"""EDA event filter — flag events that contain changes in specified paths.

For GitHub push events, inspects each commit's added/modified/removed file
lists.  For pull_request events (which lack file lists in the payload), the
flag defaults to true so downstream rules can decide independently.
"""

import logging
from typing import Any

DOCUMENTATION = r"""
name: path_filter
short_description: Flag events whose changed files match path prefixes
description:
  - Adds a boolean key to the event indicating whether any changed file
    matches the configured path prefixes.
  - Works with GitHub push payloads (inspects commits[].added/modified/removed).
  - For event types that lack file-change data (e.g. pull_request), the flag
    defaults to true so the event is not incorrectly suppressed.
options:
  paths:
    description: List of path prefixes to match against changed files.
    type: list
    elements: str
    required: true
  assign_to:
    description: >-
      Dot-separated key path where the boolean result is stored on the event.
    type: str
    default: has_path_changes
"""

LOGGER = logging.getLogger("demo.lightwell.path_filter")


def main(event: dict[str, Any], paths: list[str], assign_to: str = "has_path_changes") -> dict[str, Any]:
    payload = event.get("payload", {})
    commits = payload.get("commits")

    if commits is None:
        LOGGER.debug("No commits array in payload; defaulting %s to true", assign_to)
        event[assign_to] = True
        return event

    for commit in commits:
        for change_type in ("added", "modified", "removed"):
            for filepath in commit.get(change_type, []):
                if any(filepath.startswith(prefix) for prefix in paths):
                    event[assign_to] = True
                    return event

    event[assign_to] = False
    return event
