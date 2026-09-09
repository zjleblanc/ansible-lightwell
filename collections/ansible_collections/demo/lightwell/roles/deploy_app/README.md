# demo.lightwell.deploy_app

Deploys the Lightwell demo application container via Podman on the target
host, using `podman_generate_systemd` so the container survives reboots.
Before deploying, it records the currently running image reference to
`app_previous_image_file` so the `rollback` role can restore it later.

## Required variables

| Variable | Description |
| --- | --- |
| `app_environment` | `test` or `prod`; used for logging and health check behavior. |

## Common variables (see `defaults/main.yml`)

| Variable | Default | Description |
| --- | --- | --- |
| `app_container_name` | `lightwell-patch-demo-app-{{ app_environment }}` | Name of the running container. Suffixed with the environment so `test` and `prod` can be deployed to, and coexist on, the same host. |
| `app_host_port` | `8080` if `test`, `8081` otherwise | Host port mapped to the container's port 8080. Derived from `app_environment` so `test` and `prod` can run side-by-side on the same host without colliding. |
| `app_previous_image_file` | `/opt/lightwell-demo/{{ app_environment }}/previous_image.txt` | Where the previous image reference is persisted for rollback, namespaced by environment. |
| `manage_systemd_unit` | `true` | Whether to generate and enable a systemd unit for the container. |
| `app_image_registry` | `quay.io/zleblanc` | Registry/namespace the image was pushed to by `build_app`. Mirrored here so this role doesn't depend on `group_vars` being applied. |
| `app_image_name` | `lightwell-patch-demo-app` | Image repository name. |
| `app_image_tag` | `{{ app_git_sha \| default('dev') }}` | Tag to deploy (typically the git commit SHA built by `build_app`). |

## Optional variables

| Variable | Description |
| --- | --- |
| `registry_auth_file` | Path to a podman/docker `auth.json`-format file with credentials for pulling from a private registry. |
