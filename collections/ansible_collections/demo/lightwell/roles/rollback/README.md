# demo.lightwell.rollback

Restores the previously running container image for the Lightwell demo
application, using the image reference recorded by `deploy_app` at
`app_previous_image_file`. Re-runs the `health_check` role (non-strict)
against the restored version so the outcome of the rollback itself is
known.

## Required variables

| Variable | Description |
| --- | --- |
| `app_environment` | `dev` or `prod`; used for log messages. |

## Common variables (see `defaults/main.yml`)

| Variable | Default | Description |
| --- | --- | --- |
| `app_container_name` | `lightwell-patch-demo-app` (`lightwell-patch-demo-app-dev` for `dev`) | Name of the container and Quadlet unit to roll back. |
| `app_host_port` | `8080` if `dev`, `8081` otherwise | Host port mapped to the container's port 8080, derived from `app_environment`. |
| `app_previous_image_file` | `/opt/lightwell-demo/{{ app_environment }}/previous_image.txt` | Path written by `deploy_app` containing the last known-good image reference. |
| `quadlet_dir` | `/etc/containers/systemd` | Directory the Quadlet `.container` file is rewritten in. |
| `app_service_name` | `{{ app_container_name }}` | Name of the systemd service restarted after the Quadlet unit is rewritten. |

## Behavior

1. Reads and decodes the previous image reference. Fails loudly if none is
   recorded (there is nothing to roll back to).
2. Rewrites the Quadlet `.container` unit with the previous image.
3. Reloads systemd and restarts the service so it picks up the rolled-back
   image on the same port.
4. Re-runs `demo.lightwell.health_check` (with `health_check_strict: false`)
   and reports whether the rollback itself resulted in a healthy service.
