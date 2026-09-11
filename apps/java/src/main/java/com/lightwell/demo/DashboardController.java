package com.lightwell.demo;

import java.time.ZoneOffset;
import java.time.ZonedDateTime;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import com.lightwell.demo.model.AppConfig;
import com.lightwell.demo.model.PackageVersion;

@Controller
public class DashboardController {

    private final AppConfigService appConfigService;
    private final PackageVersionService packageVersionService;
    private final PomSnippetService pomSnippetService;

    public DashboardController(
            AppConfigService appConfigService,
            PackageVersionService packageVersionService,
            PomSnippetService pomSnippetService) {
        this.appConfigService = appConfigService;
        this.packageVersionService = packageVersionService;
        this.pomSnippetService = pomSnippetService;
    }

    @GetMapping("/")
    public String dashboard(Model model) {
        AppConfig config = appConfigService.getConfig();
        java.util.List<PackageVersion> packageVersions =
                packageVersionService.getPackageVersions(config.trackedDependencies());
        long lightwellCount = packageVersions.stream().filter(PackageVersion::lightwell).count();

        model.addAttribute("service", config.service());
        model.addAttribute("patchSource", config.patchSource());
        model.addAttribute("packageVersions", packageVersions);
        model.addAttribute("lightwellCount", lightwellCount);
        model.addAttribute("trackedCount", packageVersions.size());
        model.addAttribute("patchTimeline", config.patchTimeline());
        model.addAttribute("pomSnippet", pomSnippetService.readPomXml());
        model.addAttribute("now", ZonedDateTime.now(ZoneOffset.UTC));
        return "dashboard";
    }
}
