package com.lightwell.demo;

import java.time.Instant;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import com.lightwell.demo.model.PackageVersion;

@RestController
public class HealthController {

    private final AppConfigService appConfigService;
    private final PackageVersionService packageVersionService;

    public HealthController(AppConfigService appConfigService, PackageVersionService packageVersionService) {
        this.appConfigService = appConfigService;
        this.packageVersionService = packageVersionService;
    }

    @GetMapping(value = "/healthz", produces = MediaType.APPLICATION_JSON_VALUE)
    public String healthz() {
        String serviceName = appConfigService.getConfig().service().name();
        List<PackageVersion> packages = packageVersionService.getPackageVersions(List.of());

        JSONArray packagesJson = new JSONArray();
        for (PackageVersion pkg : packages) {
            packagesJson.put(new JSONObject()
                    .put("name", pkg.name())
                    .put("version", pkg.version())
                    .put("is_lightwell", pkg.lightwell())
                    .put("lightwell_patch_id", pkg.lightwellPatchId())
                    .put("role", pkg.role()));
        }

        return new JSONObject()
                .put("status", "ok")
                .put("service", serviceName)
                .put("timestamp", Instant.now().toString())
                .put("packages", packagesJson)
                .toString();
    }
}
