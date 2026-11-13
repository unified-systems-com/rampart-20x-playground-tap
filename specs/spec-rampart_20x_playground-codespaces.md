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

`.devcontainer/devcontainer.json` is compose-native: it attaches to the `web` service of `.devcontainer/docker-compose.yml`, which runs `tap-db` and `tap-web` from `ghcr.io/unified-systems-com` (anonymous pull; pinned by digest to tap v0.3.3) and mounts one file from this repository over `/app/boot/codespace.boot.json`. The entrypoint of the published image does the rest when `CODESPACES=true`: it derives the forwarded origin, the trusted-proxy header, a `SECRET_KEY` and the instance owner (the account that opened the Codespace, by numeric id, with role `tap_admin`), selects the profile named by `TAP_CODESPACE_BOOT_PROFILE`, migrates, runs `manage.py boot` and serves.

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

- **The images are pinned by digest to tap v0.3.3.** v0.3.1 and v0.3.2 never published (the release CVE gate failed on `tap-web`); v0.3.3 did, on 2026-11-12. Refresh both digests together (`docker buildx imagetools inspect`) when moving to a newer tap release.
- **Host files are world-writable, and one is sourced.** `initializeCommand` makes `.codespace-secret-key` and `tap-codespace.env` mode 666 because the host user cannot chown them to the image's uid, and `postStartCommand` sources `tap-codespace.env`, the same file the entrypoint writes and sources. In a Codespace the VM is single-user, so this adds no reach; a local Dev Containers launch on a shared machine would inherit the exposure. Accepted, recorded here.
- **`population.on_failure` is `continue` for the whole record.** The boot engine has only a profile-level policy (`tap_boot/profile.py`), so the one expected first-boot failure (the collector preflight) cannot be exempted alone. Scoping it needs a per-step policy in tap's boot engine, which is a core feature, not a Codespaces one.
- **The first boot logs a failed collector preflight and a "Codespace boot orchestration FAILED" warning.** It is the expected skip above; the second boot clears it. A change to tap's entrypoint (start the workers before boot, or run boot after the server is up) would remove both the warning and the second boot.
- **The device-flow provider's self-test reports `secret` and `client_credentials` failed**, as it does for tap's own Codespace profile; the provider is declared non-critical.
- **Not run in a real Codespace.** Everything was run locally with the Codespaces environment variables set by hand (a made-up codespace name and domain, the real GitHub API for the owner lookup). The forwarded HTTPS origin, port privacy, the device-flow sign-in, machine size and cold-start time are untested.

- **Why the maintainer box carries the `node` Feature.** The Codespaces agent reaches a container port that is not published on the host (here sshd's 2222) by running a bare `node` inside the container. The Debian base image has none, so `gh codespace ssh` timed out in the banner exchange while sshd was listening, and a stop and start did not help (10 of 10 attempts failed). Probed directly: a tunnel to remote port 2222 returned `exec: "node": executable file not found in $PATH`. With the `node` Feature pinned by digest, the first ssh attempt worked. This is the observed cause on this repository's overlay; it was not checked against tap's own dev box, whose identical overlay worked on 2026-09-22 (tap#778).
- **A plain `gh codespace ssh -- <command>` carries no GitHub credential**; run the command through a login shell, `bash -lc '<command>'`, to get the Codespace's `GITHUB_TOKEN` and the git credential helper. The token is the Codespace's own, scoped to this repository; what an agent should hold is tap#942's open design question.

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
| req-rampart-20x-playground-codespaces-9 | Works In A Real Codespace | In Development | A Codespace opened by someone other than the maintainer comes up, signs them in as owner, and shows `/playground` with data. | The one-click claim. Run once on 2026-11-12 by the maintainer from `main` at f3017427: it came up, the device-flow sign-in worked, and the playground pages loaded. Still open: a run by someone else, and the click-to-page time. |
| req-rampart-20x-playground-codespaces-10 | The Visitor Configuration Gains Nothing | In Development | `.devcontainer/devcontainer.json` declares no features, its service is `web`, and `web` mounts no Docker socket and runs no sshd. | The maintainer box is a separate configuration. |
| req-rampart-20x-playground-codespaces-11 | The Maintainer Box Is A Separate Configuration | In Development | `.devcontainer/maintainer/devcontainer.json` stacks `docker-compose.yml` then its own overlay, attaches to a `devbox` service beside `web` and `db`, and does not make port 8000 public. | Chosen at creation (`devcontainer_path`), never the default. |
| req-rampart-20x-playground-codespaces-12 | Everything Beside The Socket Is Pinned By Digest | In Development | The four Features (sshd, docker-outside-of-docker, github-cli, node) and the devbox base image are referenced by `@sha256:` digest only. | Digest only: a `tag@digest` reference does not parse in Codespaces. |
| req-rampart-20x-playground-codespaces-13 | The Box Reaches The Running Instance | In Development | `devbox` mounts this checkout at `/workspace` and the Docker socket, and its `postStartCommand` runs the second `manage.py boot` in `web` with `docker exec`. | So an agent or person can edit, commit, push and pull here, and query the instance. Run 2026-11-13 on a fresh Codespace: `gh codespace ssh` answered 4 s after it was Available with no restart; a login shell (`bash -lc`) had the Codespace's GitHub credential, and a plain ssh command did not. |
