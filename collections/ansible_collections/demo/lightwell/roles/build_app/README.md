# demo.lightwell.build_app

Builds and pushes the Lightwell demo application container image using
Podman. Authenticates to the Lightwell Network remediated repository at
build time via a Podman build secret, so no credentials are ever written
into image layers.

## Required variables

| Variable | Description |
| --- | --- |
| `lightwell_username` | Lightwell Network service account username (`<id>\|<name>`). Supply via an AAP credential or Ansible Vault. |
| `lightwell_password` | Lightwell Network service account token. Supply via an AAP credential or Ansible Vault. |

## Common variables (see `defaults/main.yml`)

| Variable | Default | Description |
| --- | --- | --- |
| `app_source_dir` | `{{ playbook_dir }}/../app` | Path to the checked-out application source. |
| `lightwell_registry_host` | `packages.redhat.com` | Lightwell Network host used in the generated `.netrc`. |
| `app_image_registry` | `quay.io/lightwell-demo` | Registry/namespace the image is pushed to. |
| `app_image_name` | `lightwell-patch-demo` | Image repository name. |
| `app_image_tag` | `{{ app_git_sha \| default('dev') }}` | Primary tag for the built image (typically the git commit SHA). |
| `app_image_push` | `true` | Whether to push the built image to the registry. |
| `app_environment` | `test` | Used to compute the `<environment>-latest` convenience tag. |

## Example

```yaml
- hosts: localhost
  connection: local
  roles:
    - role: demo.lightwell.build_app
      vars:
        app_environment: test
        app_image_tag: "{{ app_git_sha }}"
```
