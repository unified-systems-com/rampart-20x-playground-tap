"""The Codespaces launch, read as files (`req-rampart-20x-playground-codespaces-*`).

These tests read JSON, TOML and text only. That a Codespace comes up is checked by running the compose file; see the spec's Known gaps."""

from __future__ import annotations

import hashlib
import json
import re
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


@pytest.mark.spec("req-rampart-20x-playground-codespaces-1")
def test_published_images_only() -> None:
    compose = _compose()
    images = re.findall(r"^\s+image:\s*(\S+)", compose, flags=re.M)
    assert images and all(i.startswith("ghcr.io/unified-systems-com/tap-") for i in images)
    # Immutable: a digest and nothing else (a tag is movable, and tag@digest does not parse in Codespaces).
    assert all(re.fullmatch(r"ghcr\.io/unified-systems-com/tap-(web|db)@sha256:[0-9a-f]{64}", i) for i in images), images
    assert not re.search(r"^\s+build:", compose, flags=re.M)
    assert not re.search(r"-\s*\.\.?/?:/app\b|:/app\s*$", compose, flags=re.M)  # no checkout mounted over /app


@pytest.mark.spec("req-rampart-20x-playground-codespaces-2")
def test_the_record_ships_with_its_digest_and_is_mounted_and_selected() -> None:
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    entry = next(r for r in manifest["boot"]["records"] if r["name"] == "codespace")
    digest = hashlib.sha256(json.dumps(_record(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert entry["sha256"] == digest
    compose = _compose()
    assert "../tap_plugin/rampart_20x_playground/boot/codespace.boot.json:/app/boot/codespace.boot.json:ro" in compose
    assert (DEVCONTAINER / ".." / "tap_plugin" / "rampart_20x_playground" / "boot" / "codespace.boot.json").resolve().is_file()
    assert re.search(r"TAP_CODESPACE_BOOT_PROFILE:\s*codespace\b", compose) and re.search(r"TAP_BOOT_PROFILE:\s*codespace\b", compose)


@pytest.mark.spec("req-rampart-20x-playground-codespaces-3")
def test_deploy_profile_with_owner_only_device_flow() -> None:
    record = _record()
    assert record["profile_kind"] == "deploy"
    (provider,) = record["auth"]["providers"]
    assert provider["device_flow"] is True and provider["owner_only"] is True and provider["client_id"]
    assert "client_secret" not in json.dumps(provider)
    assert record["auth"]["local_password_enabled"] is False


@pytest.mark.spec("req-rampart-20x-playground-codespaces-4")
def test_the_same_plugins_as_the_demo_and_no_credential() -> None:
    mine, demo = _record(), _demo()
    # The self entry is the one place the records differ: the demo record ships inside the release it
    # installs, so it cannot carry that release's commit; this record is mounted from the workspace and
    # does carry it (the Codespaces review, High: no mutable tag). Same repo and tag, plus the commit.
    me = "rampart_20x_playground"
    mine_self = next(p for p in mine["install"]["plugins"] if p["slug"] == me)
    demo_self = next(p for p in demo["install"]["plugins"] if p["slug"] == me)
    assert (mine_self["source"]["url"], mine_self["source"]["rev"]) == (demo_self["source"]["url"], demo_self["source"]["rev"])
    assert re.fullmatch(r"[0-9a-f]{40}", mine_self["source"]["commit"])
    assert [p for p in mine["install"]["plugins"] if p["slug"] != me] == [p for p in demo["install"]["plugins"] if p["slug"] != me]
    assert mine["population"]["steps"] == demo["population"]["steps"]
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
    for name in (".env", ".codespace-secret-key", "tap-codespace.env"):
        assert f"/.devcontainer/{name}" in ignore


@pytest.mark.spec("req-rampart-20x-playground-codespaces-6")
def test_the_writable_paths_the_entrypoint_needs_are_provided() -> None:
    compose, init = _compose(), _devcontainer()["initializeCommand"]
    assert "./.codespace-secret-key:/app/.codespace-secret-key" in compose and ".codespace-secret-key" in init
    assert "./tap-codespace.env:/run/tap-codespace.env" in compose and "tap-codespace.env" in init
    assert re.search(r"/app/logs:[^\n]*uid=65532", compose)
    assert re.search(r"TAP_BOOT_INSTALL__SNAPSHOT_BEFORE_MIGRATE:\s*\"false\"", compose)
    for var in ("CODESPACES", "CODESPACE_NAME", "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "GITHUB_USER", "GITHUB_API_URL"):
        assert f"{var}:" in compose


@pytest.mark.spec("req-rampart-20x-playground-codespaces-7")
def test_the_collector_fires_after_the_server_is_up() -> None:
    assert _record()["population"]["on_failure"] == "continue"
    post = _devcontainer()["postStartCommand"]
    assert "healthz" in post and ". /run/tap-codespace.env" in post and post.rstrip().endswith("manage.py boot")


@pytest.mark.spec("req-rampart-20x-playground-codespaces-8")
def test_the_port_is_forwarded_and_stays_private() -> None:
    dev = _devcontainer()
    assert dev["service"] == "web" and dev["overrideCommand"] is False and dev["forwardPorts"] == [8000]
    assert dev["portsAttributes"]["8000"]["onAutoForward"] == "openBrowser"
    assert "visibility" not in json.dumps(dev).lower() and "public" not in json.dumps(dev["portsAttributes"]).lower()
