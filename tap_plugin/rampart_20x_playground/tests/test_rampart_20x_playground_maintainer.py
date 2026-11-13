"""The maintainer dev box, read as files (`req-rampart-20x-playground-codespaces-10` to `-13`).

These tests read JSON, YAML text and shell text only. That the box accepts an ssh connection is checked in a real Codespace; see the spec's Known gaps."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
DEVCONTAINER = REPO / ".devcontainer"
MAINTAINER = DEVCONTAINER / "maintainer"


def _maintainer() -> dict:
    return json.loads((MAINTAINER / "devcontainer.json").read_text(encoding="utf-8"))


def _visitor() -> dict:
    return json.loads((DEVCONTAINER / "devcontainer.json").read_text(encoding="utf-8"))


def _service_block(compose: str, name: str) -> str:
    match = re.search(rf"^  {name}:\n((?:    .*\n|\n)+)", compose, flags=re.M)
    assert match, f"no {name} service"
    return match.group(1)


@pytest.mark.spec("req-rampart-20x-playground-codespaces-10")
def test_the_visitor_configuration_gains_nothing() -> None:
    visitor = _visitor()
    assert "features" not in visitor
    assert visitor["service"] == "web"
    web = _service_block((DEVCONTAINER / "docker-compose.yml").read_text(encoding="utf-8"), "web")
    assert "docker.sock" not in web
    assert not (DEVCONTAINER / "docker-compose.yml").read_text(encoding="utf-8").count("sshd")


@pytest.mark.spec("req-rampart-20x-playground-codespaces-11")
def test_the_maintainer_configuration_is_separate_and_stacks_the_overlay() -> None:
    cfg = _maintainer()
    assert cfg["dockerComposeFile"] == ["../docker-compose.yml", "docker-compose.yml"]
    assert cfg["service"] == "devbox"
    assert {"devbox", "web", "db"} <= set(cfg["runServices"])
    assert cfg["workspaceFolder"] == "/workspace"
    assert "8000" in cfg["portsAttributes"] and "visibility" not in cfg["portsAttributes"]["8000"]


@pytest.mark.spec("req-rampart-20x-playground-codespaces-12")
def test_everything_beside_the_socket_is_pinned_by_digest() -> None:
    cfg = _maintainer()
    assert any(f.startswith("ghcr.io/devcontainers/features/sshd@sha256:") for f in cfg["features"])
    assert all(re.fullmatch(r"[^@:]+/[^@:]+@sha256:[0-9a-f]{64}", f) for f in cfg["features"]), cfg["features"]
    overlay = (MAINTAINER / "docker-compose.yml").read_text(encoding="utf-8")
    images = re.findall(r"^\s+image:\s*(\S+)", overlay, flags=re.M)
    assert images and all(re.fullmatch(r"\S+@sha256:[0-9a-f]{64}", i) for i in images), images


@pytest.mark.spec("req-rampart-20x-playground-codespaces-13")
def test_the_box_mounts_the_checkout_and_the_socket_and_boots_web_from_inside() -> None:
    devbox = _service_block((MAINTAINER / "docker-compose.yml").read_text(encoding="utf-8"), "devbox")
    assert "..:/workspace" in devbox and "/var/run/docker.sock:/var/run/docker.sock" in devbox
    assert "sleep infinity" in devbox
    script = (MAINTAINER / "post-start.sh").read_text(encoding="utf-8")
    assert "docker exec" in script and "manage.py boot" in script and "/run/tap-codespace.env" in script
    assert _maintainer()["postStartCommand"].endswith("/.devcontainer/maintainer/post-start.sh")
