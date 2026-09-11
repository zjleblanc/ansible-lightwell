package com.lightwell.demo.model;

import java.util.List;

public record AppConfig(
        ServiceInfo service,
        PatchSource patchSource,
        List<TrackedDependency> trackedDependencies,
        List<PatchTimelineEntry> patchTimeline) {
}
