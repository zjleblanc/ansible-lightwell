# demo.lightwell.deploy_app

Deploys the Lightwell demo application container via Podman on the target
host, using `podman_generate_systemd` so the container survives reboots.
Before deploying, it records the currently running image reference to
`app_previous_image_file` so the `rollback` role can restore it later.

## Required variables

| Variable | Description |
| --- | --- |
| `app_image_registry` | Registry/namespace the image was pushed to by `build_app`. |
| `app_image_name` | Image repository name. |
| `app_image_tag` | Tag to deploy (typically the git commit SHA built by `build_app`). |
| `app_environment` | `test` or `prod`; used for logging and health check behavior. |

## Common variables (see `defaults/main.yml`)

| Variable | Default | Description |
| --- | --- | --- |
| `app_container_name` | `lightwell-patch-demo` | Name of the running container. |
| `app_host_port` | `8080` | Host port mapped to the container's port 8080. |
| `app_previous_image_file` | `/opt/lightwell-demo/previous_image.txt` | Where the previous image reference is persisted for rollback. |
| `manage_systemd_unit` | `true` | Whether to generate and enable a systemd unit for the container. |

## Optional variables

| Variable | Description |
| --- | --- |
| `registry_username` / `registry_password` | Credentials for pulling from a private registry. |
