package com.lightwell.demo.model;

/**
 * Installed version of a tracked dependency, annotated with Lightwell
 * provenance (parsed from the version string) and role metadata from
 * app_config.yaml.
 */
public record PackageVersion(
        String name,
        String version,
        boolean lightwell,
        String lightwellPatchId,
        String role) {
}
