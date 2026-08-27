# demo.lightwell.health_check

Verifies that the Lightwell demo application container is running and that
its `/healthz` endpoint returns a healthy response, retrying both checks
before giving up. Sets `health_check_passed` (boolean) so calling playbooks
can decide whether to proceed, fail, or trigger a rollback.

## Required variables

| Variable | Description |
| --- | --- |
| `app_container_name` | Name of the container to check. |
| `app_host_port` | Host port the application is bound to. |
| `app_environment` | `test` or `prod`; used only for log messages. |

## Common variables (see `defaults/main.yml`)

| Variable | Default | Description |
| --- | --- | --- |
| `health_check_container_retries` | `10` | Retries while waiting for the container to report running. |
| `health_check_container_delay` | `3` | Seconds between container status retries. |
| `health_check_http_retries` | `10` | Retries while polling `/healthz`. |
| `health_check_http_delay` | `5` | Seconds between HTTP retries. |
| `health_check_strict` | `true` | When true, fails the play immediately if the health check does not pass. Set to `false` when the caller wants to handle failure itself (e.g. to trigger a rollback). |

## Optional variables

| Variable | Description |
| --- | --- |
| `health_check_host` | Override the host used for the HTTP check (defaults to `ansible_host` or `localhost`). |
