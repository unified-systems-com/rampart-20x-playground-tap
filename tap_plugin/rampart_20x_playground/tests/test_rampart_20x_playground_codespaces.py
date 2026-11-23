"""The Codespaces launch, read as files (`req-rampart-20x-playground-codespaces-*`).

These tests read JSON, TOML and text only. That a Codespace comes up is checked by running the compose file; see the spec's Known gaps."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess  # nosec B404
import tomllib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO = PACKAGE_ROOT.parents[1]
DEVCONTAINER = REPO / ".devcontainer"
RECORD = PACKAGE_ROOT / "boot" / "codespace.boot.json"


def _record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _demo() -> dict:
    return json.loads((PACKAGE_ROOT / "boot" / "demo.boot.json").read_text(encoding="utf-8"))


def _devcontainer() -> dict:
    return json.loads((DEVCONTAINER / "devcontainer.json").read_text(encoding="utf-8"))


def _compose() -> str:
    return (DEVCONTAINER / "docker-compose.yml").read_text(encoding="utf-8")


def _deploy() -> str:
    return (REPO / "deploy" / "compose.yml").read_text(encoding="utf-8")


def _images(compose: str) -> list[str]:
    return re.findall(r"^\s+image:\s*(\S+)", compose, flags=re.M)


VISITOR_IDENTITY = "sh /opt/playground/codespace-identity.sh /run/tap-codespace-identity.env"


@pytest.mark.spec("req-rampart-20x-playground-codespaces-1")
@pytest.mark.parametrize("read", [_compose, _deploy], ids=["codespace", "deploy"])
def test_published_images_only(read) -> None:
    compose = read()
    images = _images(compose)
    # Immutable: a digest and nothing else (a tag is movable, and tag@digest does not parse in Codespaces).
    assert len(images) == 2, images
    assert re.fullmatch(r"ghcr\.io/unified-systems-com/tap-db@sha256:[0-9a-f]{64}", images[0]), images
    assert re.fullmatch(r"ghcr\.io/unified-systems-com/rampart-20x-playground-web@sha256:[0-9a-f]{64}", images[1]), images
    assert not re.search(r"^\s+build:", compose, flags=re.M)
    assert not re.search(r"-\s*\.\.?/?:/app\b|:/app\s*$", compose, flags=re.M)  # no checkout mounted over /app
    # A product image refuses to start under a mount over the environment it ships.
    assert not re.search(r":/app/(\.venv|tap-product)\b", compose)


@pytest.mark.spec("req-rampart-20x-playground-codespaces-1")
def test_both_compose_files_pin_the_same_images() -> None:
    assert _images(_compose()) == _images(_deploy())


@pytest.mark.spec("req-rampart-20x-playground-codespaces-2")
def test_the_record_ships_with_its_digest_and_is_baked_and_selected() -> None:
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    entry = next(r for r in manifest["boot"]["records"] if r["name"] == "codespace")
    digest = hashlib.sha256(json.dumps(_record(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert entry["sha256"] == digest
    # The product image carries the record; a mount over it would run a record the image was not built for.
    publish = (REPO / ".github" / "workflows" / "publish-image.yml").read_text(encoding="utf-8")
    assert re.search(r"^\s+record: tap_plugin/rampart_20x_playground/boot/codespace\.boot\.json$", publish, flags=re.M)
    assert re.search(r"^\s+profile: codespace$", publish, flags=re.M)
    compose, deploy = _compose(), _deploy()
    assert "codespace.boot.json" not in compose and "codespace.boot.json" not in deploy
    assert re.search(r"TAP_CODESPACE_BOOT_PROFILE:\s*codespace\b", compose) and re.search(r"TAP_BOOT_PROFILE:\s*codespace\b", compose)
    assert re.search(r"TAP_BOOT_PROFILE:\s*codespace\b", deploy)


@pytest.mark.spec("req-rampart-20x-playground-codespaces-3")
def test_deploy_profile_with_owner_only_device_flow() -> None:
    record = _record()
    assert record["profile_kind"] == "deploy"
    (provider,) = record["auth"]["providers"]
    assert provider["device_flow"] is True and provider["owner_only"] is True and provider["client_id"]
    assert "client_secret" not in json.dumps(provider)
    assert record["auth"]["local_password_enabled"] is False


def _without_wait(steps: list[dict]) -> list[dict]:
    """Steps with the fields that only say how long a fire-collector step waits removed."""
    return [{k: v for k, v in s.items() if not (s["type"] == "fire-collector" and k in ("timeout_seconds", "note"))} for s in steps]


@pytest.mark.spec("req-rampart-20x-playground-codespaces-4")
def test_the_same_plugins_as_the_demo_and_no_credential() -> None:
    mine, demo = _record(), _demo()
    # The self entry is the one place the records differ: the demo record ships inside the release it
    # installs, so it cannot carry that release's commit; this record is baked into the product image from
    # this repository and does carry it (the Codespaces review, High: no mutable tag). Same repo and tag, plus the commit.
    me = "rampart_20x_playground"
    mine_self = next(p for p in mine["install"]["plugins"] if p["slug"] == me)
    demo_self = next(p for p in demo["install"]["plugins"] if p["slug"] == me)
    assert (mine_self["source"]["url"], mine_self["source"]["rev"]) == (demo_self["source"]["url"], demo_self["source"]["rev"])
    assert re.fullmatch(r"[0-9a-f]{40}", mine_self["source"]["commit"])
    assert [p for p in mine["install"]["plugins"] if p["slug"] != me] == [p for p in demo["install"]["plugins"] if p["slug"] != me]
    # The population is the demo's except for how the one fire-collector step waits (see the next test).
    assert _without_wait(mine["population"]["steps"]) == _without_wait(demo["population"]["steps"])
    assert not any("credential" in p["source"] for p in mine["install"]["plugins"])
    assert mine["web"] == demo["web"]


@pytest.mark.spec("req-rampart-20x-playground-codespaces-4")
def test_the_instance_is_named_in_the_record_not_in_the_environment() -> None:
    """The header and page title carry the record's branding name; the compose file no longer sets TAP_PRODUCT_NAME."""
    assert _record()["web"]["branding"] == {"name": "20x Playground"}
    assert _demo()["web"]["branding"] == _record()["web"]["branding"]
    assert "TAP_PRODUCT_NAME" not in _compose()


@pytest.mark.spec("req-rampart-20x-playground-codespaces-5")
def test_no_secret_ships() -> None:
    compose = _compose()
    assert not re.search(r"PASSWORD:\s*[\"']?(tap|password|changeme|dev)[\"']?\s*$", compose, flags=re.M | re.I)
    assert "${POSTGRES_PASSWORD:?" in compose and "${TAP_SEARCH_READONLY_PASSWORD:?" in compose
    init = _devcontainer()["initializeCommand"]
    assert "openssl rand" in init and ".env" in init
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    for name in (".env", ".codespace-secret-key", "tap-codespace.env", "codespace-identity.env"):
        assert f"/.devcontainer/{name}" in ignore


@pytest.mark.spec("req-rampart-20x-playground-codespaces-6")
def test_the_writable_paths_the_entrypoint_needs_are_provided() -> None:
    compose, init = _compose(), _devcontainer()["initializeCommand"]
    assert "./.codespace-secret-key:/app/.codespace-secret-key" in compose and ".codespace-secret-key" in init
    assert "./tap-codespace.env:/run/tap-codespace.env" in compose and "tap-codespace.env" in init
    # World-writable, not owned by uid: rootless Podman refuses a tmpfs `uid=`.
    assert re.search(r"/app/logs:[^\n]*mode=1777", compose) and not re.search(r"/app/logs:[^\n]*uid=", compose)
    assert re.search(r"TAP_BOOT_INSTALL__SNAPSHOT_BEFORE_MIGRATE:\s*\"false\"", compose)
    # A new Codespace builds its empty database from the models instead of replaying every migration.
    assert re.search(r"TAP_BOOT_INSTALL__SCHEMA_FROM_MODELS:\s*\"true\"", compose)
    for var in ("CODESPACES", "CODESPACE_NAME", "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "GITHUB_USER", "GITHUB_API_URL"):
        assert f"{var}:" in compose


@pytest.mark.spec("req-rampart-20x-playground-codespaces-7")
def test_the_collector_runs_when_the_workers_start_and_nothing_boots_twice() -> None:
    assert _record()["population"]["on_failure"] == "continue"
    # The first boot queues the job; the workers claim it once they start. No second `manage.py boot`: the one
    # postStartCommand writes the identity file and nothing else (req-rampart-20x-playground-codespaces-15).
    assert _devcontainer()["postStartCommand"] == VISITOR_IDENTITY
    assert "manage.py" not in (DEVCONTAINER / "codespace-identity.sh").read_text(encoding="utf-8")


@pytest.mark.spec("req-rampart-20x-playground-codespaces-8")
def test_the_port_is_forwarded_and_stays_private() -> None:
    dev = _devcontainer()
    assert dev["service"] == "web" and dev["overrideCommand"] is False and dev["forwardPorts"] == [8000]
    assert dev["portsAttributes"]["8000"]["onAutoForward"] == "openBrowser"
    assert "visibility" not in json.dumps(dev).lower() and "public" not in json.dumps(dev["portsAttributes"]).lower()


@pytest.mark.spec("req-rampart-20x-playground-codespaces-7")
def test_the_collector_step_is_the_demo_records_and_runs_in_the_first_boot() -> None:
    """tap starts the job workers before the Codespace boot, so the step needs no shortened wait and the preflight stays on."""
    pop = _record()["population"]
    assert "collector_preflight" not in pop and "collector_preflight" not in _demo()["population"]
    step = next(s for s in pop["steps"] if s["type"] == "fire-collector")
    assert "timeout_seconds" not in step
    assert pop["on_failure"] == "continue"


@pytest.mark.spec("req-rampart-20x-playground-codespaces-3")
def test_the_login_uses_the_playgrounds_own_oauth_app_not_the_git_serious_demos() -> None:
    """GitHub names the app on the consent screen and the device page, so the playground must not borrow git-serious-demo's."""
    provider = _record()["auth"]["providers"][0]
    assert provider["client_id"] == "Ov23ctxWGaTmdJUM6ItQ"
    assert provider["client_id"] != "Ov23li7DZ17aqmEpyHSL"  # tap's own git-serious Codespace demo app


@pytest.mark.spec("req-rampart-20x-playground-codespaces-14")
def test_the_visitor_is_told_where_the_site_is() -> None:
    """The editor opens first and is not the playground, so it opens on a page that says so and its terminal prints the address."""
    dev, compose = _devcontainer(), _compose()
    # The editor opens on a folder holding one page, not on /app (tap's own code and README in the image).
    assert dev["workspaceFolder"] == "/welcome" and "./welcome:/welcome:ro" in compose
    assert dev["customizations"]["vscode"]["settings"]["workbench.startupEditor"] == "readme"
    assert [p.name for p in (DEVCONTAINER / "welcome").iterdir()] == ["README.md"]
    welcome = (DEVCONTAINER / "welcome" / "README.md").read_text(encoding="utf-8")
    assert "not the playground" in welcome and "The 20x Playground is ready:" in welcome and "Ports" in welcome
    # The terminal runs a mounted script (a short command line, since the terminal echoes it) that waits and prints the link.
    assert dev["postAttachCommand"] == "sh /opt/playground/site-ready.sh"
    assert "./site-ready.sh:/opt/playground/site-ready.sh:ro" in compose
    script = (DEVCONTAINER / "site-ready.sh").read_text(encoding="utf-8")
    assert "http://127.0.0.1:8000/" in script  # waits for the site itself, inside the container
    assert "The 20x Playground is ready: https://$CODESPACE_NAME-8000.$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN" in script
    assert "manage.py" not in script  # a message, not a second boot (req-rampart-20x-playground-codespaces-7)
    maintainer = json.loads((DEVCONTAINER / "maintainer" / "devcontainer.json").read_text(encoding="utf-8"))
    assert "postAttachCommand" not in maintainer and maintainer["workspaceFolder"] == "/workspace"
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    try_it = readme.split("## Try it", 1)[1].split("\n## ", 1)[0]
    assert "not the playground" in try_it and "The 20x Playground is ready:" in try_it and "Ports panel" in try_it


def _write_identity(tmp_path: Path, shared: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    """Run codespace-identity.sh against a stand-in for Codespaces' shared env file."""
    src = tmp_path / "shared.env"
    src.write_text(shared, encoding="utf-8")
    script = tmp_path / "codespace-identity.sh"
    body = (DEVCONTAINER / "codespace-identity.sh").read_text(encoding="utf-8")
    assert body.count("/workspaces/.codespaces/shared/.env") == 1
    script.write_text(body.replace("/workspaces/.codespaces/shared/.env", str(src)), encoding="utf-8")
    dst = tmp_path / "identity.env"
    dst.write_text("", encoding="utf-8")
    run = subprocess.run(["sh", str(script), str(dst)], capture_output=True, text=True, timeout=30, check=False)  # noqa: S603, S607
    return run, dst


@pytest.mark.spec("req-rampart-20x-playground-codespaces-15")
def test_a_prebuilt_codespace_is_named_at_start(tmp_path: Path) -> None:
    compose, dev = _compose(), _devcontainer()
    assert "./codespace-identity.env:/run/tap-codespace-identity.env" in compose
    assert "TAP_CODESPACE_IDENTITY: /run/tap-codespace-identity.env" in compose
    assert "./codespace-identity.sh:/opt/playground/codespace-identity.sh:ro" in compose
    assert dev["postStartCommand"] == VISITOR_IDENTITY and "codespace-identity.env" in dev["initializeCommand"]
    # The shared file is never mounted: it carries the Codespace's tokens.
    assert ".codespaces" not in compose
    run, dst = _write_identity(
        tmp_path,
        'GITHUB_TOKEN=ghu_secret\nCODESPACE_NAME="cs-abc"\nGITHUB_CODESPACES_PORT_FORWARDING_DOMAIN=app.github.dev\n'
        "GITHUB_USER=octocat\nGITHUB_CODESPACE_TOKEN=cs_secret\n",
    )
    assert run.returncode == 0, run.stderr
    assert dst.read_text(encoding="utf-8") == (
        "CODESPACE_NAME=cs-abc\nGITHUB_CODESPACES_PORT_FORWARDING_DOMAIN=app.github.dev\nGITHUB_USER=octocat\n"
    )


@pytest.mark.spec("req-rampart-20x-playground-codespaces-17")
def test_the_playground_runs_locally_from_one_file() -> None:
    deploy = _deploy()
    # The initializer mints this installation's identity into a named volume; the file carries only a bootstrap password.
    assert re.search(r"^\s+TAP_INSTALLATION_DIR: /var/lib/tap/installation$", deploy, flags=re.M)
    assert re.search(r"^\s+- installation:/var/lib/tap/installation$", deploy, flags=re.M)
    assert re.search(r"^  installation: \{\}$", deploy, flags=re.M)
    passwords = set(re.findall(r"(?:PASSWORD: |tap:)([^@\s]+)", deploy))
    assert passwords == {"bootstrap-replaced-at-first-start"}, passwords
    assert "SECRET_KEY" not in deploy and "TAP_GRID_ID" not in deploy
    # Loopback only (rootless Podman publishes on every interface otherwise), and the origin is that address.
    (port,) = re.findall(r"^\s+- \"(.+:8000)\"$", deploy, flags=re.M)
    assert port == "127.0.0.1:${PORT:-8000}:8000"
    assert re.search(r"^\s+TAP_BASE_URL: http://localhost:\$\{PORT:-8000\}$", deploy, flags=re.M)
    assert re.search(r"/app/logs:[^\n]*mode=1777", deploy) and "uid=" not in deploy
    assert "CODESPACE" not in deploy  # not a Codespace: the initializer's road, not the derivation
