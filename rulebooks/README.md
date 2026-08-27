# Event-Driven Ansible rulebooks

`rulebooks/lightwell_webhook.yml` is the single entry point for GitHub
events in this pipeline. Rather than each AAP job template exposing its
own native webhook receiver, GitHub sends every `pull_request` and `push`
event to one AAP **Event Stream**, which forwards matching events into a
**Rulebook Activation** running this rulebook. The rulebook inspects the
payload and launches the correct job template:

| Event | Condition | Launches |
| --- | --- | --- |
| `pull_request` (opened/synchronize/reopened) | PR is present **and** `app/` files changed | `Lightwell - Build & Test` |
| `push` to `refs/heads/main` | ref is main, not a deletion, **and** `app/` files changed | `Lightwell - Deploy Prod` |

### Path filtering

The `demo.lightwell.path_filter` event filter plugin inspects each event
before rules are evaluated. For push events, it scans
`commits[].added/modified/removed` for file paths matching the configured
prefixes (currently `app/`). Pull-request payloads don't carry file lists,
so the filter defaults to `true` — letting the event through unconditionally.

If you need to watch additional directories, add them to the `paths` list
in the source's `filters` block:

```yaml
filters:
  - demo.lightwell.path_filter:
      paths:
        - "app/"
        - "collections/"
```

Full setup instructions (creating the Event Stream, its HMAC credential,
the Decision Environment, the EDA project, and the Rulebook Activation
that binds them all together) are in
[`docs/aap-setup.md`](../docs/aap-setup.md).

## Local testing

You can exercise the rulebook's conditions locally without AAP, using
[`ansible-rulebook`](https://ansible.readthedocs.io/projects/rulebook/en/stable/):

```bash
pip install ansible-rulebook
ansible-galaxy collection install ansible.eda

ansible-rulebook \
  --rulebook rulebooks/lightwell_webhook.yml \
  --inventory inventory/hosts.yml
```

With the rulebook running, POST a sample GitHub webhook payload to
`http://localhost:5000/endpoint` to see which rule fires. Note that
`run_job_template` still needs a reachable Controller and a configured
`Red Hat Ansible Automation Platform` credential to actually launch a job
-- for pure condition testing, swap the action for `debug` locally.
