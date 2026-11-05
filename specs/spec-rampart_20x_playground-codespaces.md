# Rampart 20x Playground Codespaces Specification

**A GitHub Codespace launched from this repository runs the playground from the published TAP images and this repository's own boot record, with no tap checkout, so anyone with a GitHub account can open a running copy. The repository holds the whole launch: a devcontainer, a compose file and one boot record.**

This is an extension of `spec-rampart_20x_playground-v0.md`. It adds files at the repository root (`.devcontainer/`) and one boot record; it adds no bundle, page or code. Ruled by George, 2026-11-05: the launch lives in the plugin's own repository, so any plugin author can do the same for their own boot record, and nothing about a launcher lives in the tap repository.

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-codespaces | [One-Click Launch](#one-click-launch) | In Development | The devcontainer, the compose file and the `codespace` boot record. |

### One-Click Launch
----
RID: `req-rampart-20x-playground-codespaces`

Status: `In Development`

#### Implementation

`.devcontainer/devcontainer.json` is compose-native: it attaches to the `web` service of `.devcontainer/docker-compose.yml`, which runs `tap-db` and `tap-web` from `ghcr.io/unified-systems-com` (anonymous pull; the tag is `${TAP_IMAGE_TAG:-latest}`) and mounts one file from this repository over `/app/boot/codespace.boot.json`. The entrypoint of the published image does the rest when `CODESPACES=true`: it derives the forwarded origin, the trusted-proxy header, a `SECRET_KEY` and the instance owner (the account that opened the Codespace, by numeric id, with role `tap_admin`), selects the profile named by `TAP_CODESPACE_BOOT_PROFILE`, migrates, runs `manage.py boot` and serves.

The `codespace` record (`tap_plugin/rampart_20x_playground/boot/codespace.boot.json`) is the demo record's plugins and population with two changes: `profile_kind` is `deploy`, not `dev_local`, because the instance is served on a forwarded hostname and the dev passkey replay does not apply; and sign-in is the GitHub device flow that tap's own `codespace_demo` profile uses (a public client id, no secret, `owner_only`), so only the account that opened the Codespace can sign in. Its population sets `on_failure` `continue` for the reason below.

What the published image needs that a checkout supplied, and how each is met without changing tap:

| Need | Why | How |
| --- | --- | --- |
| A writable `/app/.codespace-secret-key` and `/run/tap-codespace.env` | The entrypoint writes both; `/app` and `/run` are root-owned in the image and the container user is not root | `initializeCommand` creates both files, mode 666, in `.devcontainer/` on the Codespace host, and the compose file mounts them; both are gitignored |
| A generated database password and search-role password | The deploy gate refuses the development defaults when `DEBUG` is off; no secret may ship | `initializeCommand` writes `openssl rand` values to `.devcontainer/.env` once, and compose requires them |
| A writable `/app/logs` | The boot record is written there | a `tmpfs` mount owned by the image user |
| No pre-migrate snapshot | The snapshot directory is under the root-owned `/app`, and a new database has nothing to keep | `TAP_BOOT_INSTALL__SNAPSHOT_BEFORE_MIGRATE=false` |
| The collector step after the server is up | The entrypoint runs `manage.py boot` before it starts the job workers, so a `fire-collector` step cannot run in that first boot (its preflight fails); with `on_failure` `continue` the first boot seeds everything else and skips that step | `postStartCommand` waits for the server, loads the derived environment from `/run/tap-codespace.env` and runs `manage.py boot` again, which is idempotent and fires `vdr_max` |

#### Known gaps

- **The image tag is `latest`.** TAP's `0.3.1` and `0.3.2` images were never published (the release CVE gate failed on `tap-web`), and the playground needs core 0.3.1 or later, so no tagged image fits. Set `TAP_IMAGE_TAG` to a tag once one exists.
- **The first boot logs a failed collector preflight and a "Codespace boot orchestration FAILED" warning.** It is the expected skip above; the second boot clears it. A change to tap's entrypoint (start the workers before boot, or run boot after the server is up) would remove both the warning and the second boot.
- **The device-flow provider's self-test reports `secret` and `client_credentials` failed**, as it does for tap's own Codespace profile; the provider is declared non-critical.
- **Not run in a real Codespace.** Everything was run locally with the Codespaces environment variables set by hand (a made-up codespace name and domain, the real GitHub API for the owner lookup). The forwarded HTTPS origin, port privacy, the device-flow sign-in, machine size and cold-start time are untested.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-codespaces-1 | Published Images Only | In Development | The compose file runs `tap-web` and `tap-db` from `ghcr.io/unified-systems-com`, has no `build` and mounts no tap source. | |
| req-rampart-20x-playground-codespaces-2 | The Record Ships And Is Selected | In Development | The `codespace` record is in `[[boot.records]]` with its digest, the compose file mounts it from the repository, and `TAP_CODESPACE_BOOT_PROFILE` names it. | |
| req-rampart-20x-playground-codespaces-3 | Owner-Only Device Flow, Deploy Profile | In Development | The record's `profile_kind` is `deploy`, its one provider is a device-flow GitHub provider with `owner_only` and a public client id, and local passwords are off. | `req-tap-serving-codespace-7`. |
| req-rampart-20x-playground-codespaces-4 | The Same Plugins As The Demo | In Development | The record's installs equal the demo record's, entry for entry, and no source carries a credential. | One plugin set to maintain. |
| req-rampart-20x-playground-codespaces-5 | No Secret Ships | In Development | No password or key is written in the compose file or the devcontainer; the two passwords are generated into a gitignored file at first start and compose refuses to start without them. | `req-tap-serving-codespace-4`. |
| req-rampart-20x-playground-codespaces-6 | The Image's Writable Paths Are Provided | In Development | The files and directories the entrypoint writes (`/app/.codespace-secret-key`, `/run/tap-codespace.env`, `/app/logs`) are provided by mounts the launch creates, and the snapshot is off. | |
| req-rampart-20x-playground-codespaces-7 | The Collector Fires After Start | In Development | The record's population is `continue`, and the devcontainer's `postStartCommand` waits for the server, loads `/run/tap-codespace.env` and runs `manage.py boot`. | |
| req-rampart-20x-playground-codespaces-8 | The Port Stays Private | In Development | The devcontainer forwards port 8000 and opens it, and sets no public visibility. | The maintainer spec forbids public visibility for a devbox. |
| req-rampart-20x-playground-codespaces-9 | Works In A Real Codespace | Backlog | A Codespace opened by someone other than the maintainer comes up, signs them in as owner, and shows `/playground` with data. | The one-click claim; needs a human test. |
