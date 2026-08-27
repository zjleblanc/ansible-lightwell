# demo.lightwell.rollback

Restores the previously running container image for the Lightwell demo
application, using the image reference recorded by `deploy_app` at
`app_previous_image_file`. Re-runs the `health_check` role (non-strict)
against the restored version so the outcome of the rollback itself is
known.

## Required variables

| Variable | Description |
| --- | --- |
| `app_environment` | `test` or `prod`; used for log messages. |

## Common variables (see `defaults/main.yml`)

| Variable | Default | Description |
| --- | --- | --- |
| `app_container_name` | `lightwell-patch-demo-app` | Name of the container to roll back. |
| `app_host_port` | `8080` | Host port mapped to the container's port 8080. |
| `app_previous_image_file` | `/opt/lightwell-demo/previous_image.txt` | Path written by `deploy_app` containing the last known-good image reference. |

## Behavior

1. Reads and decodes the previous image reference. Fails loudly if none is
   recorded (there is nothing to roll back to).
2. Stops the current (unhealthy) container.
3. Starts a new container from the previous image on the same port.
4. Re-runs `demo.lightwell.health_check` (with `health_check_strict: false`)
   and reports whether the rollback itself resulted in a healthy service.
