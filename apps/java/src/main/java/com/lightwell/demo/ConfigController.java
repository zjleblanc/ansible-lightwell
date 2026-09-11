package com.lightwell.demo;

import org.json.JSONObject;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ConfigController {

    private final AppConfigService appConfigService;

    public ConfigController(AppConfigService appConfigService) {
        this.appConfigService = appConfigService;
    }

    @GetMapping(value = "/api/config", produces = MediaType.APPLICATION_JSON_VALUE)
    public String apiConfig() {
        return new JSONObject(appConfigService.getRawConfig()).toString();
    }
}
