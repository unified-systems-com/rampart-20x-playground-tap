"""The Days To December 7 countdown panel type and the last-scan Search (`req-rampart-20x-playground-page-reporting-10`, `-7`).

The panel type is tested without a browser: its schema, its registration, its template (rendered with a standalone Django
Engine, autoescape on), the shipped static file and the way it is served. What the script draws in a browser is not
tested here; the script's date function is exercised by node in the run notes, not by this suite."""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import jsonschema
import pytest
from django.template import Context, Engine
from tap_plugin.rampart_20x_playground.panels import countdown

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift" / "reporting-page.grift.json"
TEMPLATE = PACKAGE_ROOT / "templates" / "rampart_20x_playground" / "panels" / "countdown.html"
SCRIPT = PACKAGE_ROOT / "static" / "rampart_20x_playground" / "js" / "countdown.js"
ENGINE = Engine(dirs=[str(PACKAGE_ROOT / "templates")])
TYPE = countdown.RampartCountdownPanelType
GOOD = {"label": "Days To December 7", "target_date": "2026-12-07"}


def _bundle() -> dict:
    return json.loads(GRIFT.read_text(encoding="utf-8"))["batches"][0]


def render(config: dict[str, Any]) -> str:
    panel = SimpleNamespace(config={"hide_header": True, **config}, name="P")
    context = TYPE.get_view_context(panel, None)  # type: ignore[arg-type]
    return ENGINE.get_template(TYPE.view).render(Context({**context, "panel": panel}))


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-10")
class TestPanelType:
    def test_the_type_declares_its_view_and_one_external_script(self) -> None:
        assert TYPE.slug == "rampart_countdown" and TYPE.view == "rampart_20x_playground/panels/countdown.html"
        assert TYPE.js == ["rampart_20x_playground/js/countdown.js"]
        assert TYPE.css == ["compliance_core/css/report.css"]  # the report's own look, so it reads as one more section
        assert TEMPLATE.is_file() and SCRIPT.is_file()

    def test_the_type_registers_in_ready(self) -> None:
        apps = (PACKAGE_ROOT / "apps.py").read_text(encoding="utf-8")
        assert "panel_type_registry.register(RampartCountdownPanelType.slug, RampartCountdownPanelType)" in apps
        assert apps.index("super().ready()") < apps.index("panel_type_registry.register")
        from tap_web.registry import panel_type_registry

        registered = [cls for scope in panel_type_registry.all().values() for cls in scope.values()]
        assert TYPE in registered
        assert [c for c in registered if getattr(c, "view", None) == TYPE.view] == [TYPE]  # the view resolves to this type alone

    def test_the_script_is_found_by_the_static_finders(self) -> None:
        from django.contrib.staticfiles import finders

        found = finders.find(TYPE.js[0])
        assert found and Path(found).resolve() == SCRIPT.resolve()

    def test_the_config_schema_is_described_and_refuses_unknown_keys(self) -> None:
        schema = countdown.COUNTDOWN_PANEL_CONFIG_SCHEMA
        assert schema["description"] and schema["additionalProperties"] is False
        assert all(p["description"] for p in schema["properties"].values())
        assert set(schema["required"]) == {"label", "target_date"}
        jsonschema.validate({**GOOD, "heading": "Timeline", "hide_header": True}, schema)
        for bad in ({**GOOD, "colour": "red"}, {**GOOD, "script": "alert(1)"}, {"label": "x"}, {"target_date": "2026-12-07"},
                    {**GOOD, "target_date": "December 7"}, {**GOOD, "target_date": "2026-12-07T00:00:00Z"},
                    {**GOOD, "label": ""}, {**GOOD, "hide_header": "yes"}):
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(bad, schema)

    def test_a_date_that_is_not_on_the_calendar_is_a_bad_config(self) -> None:
        assert countdown.validate_config(GOOD) is None
        assert countdown.validate_config({**GOOD, "target_date": "2026-02-31"})
        assert "Panel config invalid" in render({**GOOD, "target_date": "2026-02-31"})
        assert "Panel config invalid" in render({**GOOD, "unknown": 1})

    def test_without_script_the_panel_shows_the_target_date(self) -> None:
        html = render(GOOD)
        assert re.search(r'<span class="rpt-value" data-rampart-countdown="2026-12-07">2026-12-07</span>', html)
        assert "Days To December 7" in html and "Timeline" in html  # the label and the default heading

    def test_the_template_has_no_inline_script_or_handler(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")
        assert "<script" not in text.lower() and not re.search(r"\son[a-z]+\s*=", text, re.IGNORECASE)
        assert "javascript:" not in text.lower() and "|safe" not in text and "mark_safe" not in text
        # the page loads the type's js as <script src="{% static ... %}"> (tap_web/page.html), so no panel markup carries script
        assert "<script" not in render(GOOD).lower()

    def test_text_in_config_is_escaped_not_run(self) -> None:
        html = render({**GOOD, "label": "<script>alert(1)</script>", "heading": '"><img src=x onerror=alert(1)>'})
        assert "<script" not in html.lower() and "<img" not in html.lower()
        assert "&lt;script&gt;" in html

    def test_the_script_is_a_plain_external_file(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function", "fetch(",
                       "XMLHttpRequest", "WebSocket", "import(", "http://", "https://"):
            assert banned not in text, banned
        assert "data-rampart-countdown" in text and "textContent" in text and "htmx:afterSettle" in text
        assert "2026" not in text  # the date is the panel's config, never the script's

    def test_no_header_is_weakened_by_this_plugin(self) -> None:
        """The platform sets no Content-Security-Policy of its own and the plugin adds no middleware or setting; the script
        is served the way every panel script is, as an external static file."""
        for path in PACKAGE_ROOT.rglob("*.py"):
            if "tests" in path.parts:
                continue
            source = path.read_text(encoding="utf-8")
            assert "Content-Security-Policy" not in source and "MIDDLEWARE" not in source, path


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-10")
def test_the_timeline_panel_is_wired_into_the_page_with_the_ruled_date() -> None:
    bundle = _bundle()
    (panel,) = [n for n in bundle["nodes"] if n["entity"]["entity_type"] == "panel" and n["node"]["slug"] == "playground-reporting-timeline"]
    assert panel["node"]["view"] == TYPE.view
    assert panel["node"]["config"] == {"heading": "Timeline", "label": "Days To December 7", "target_date": "2026-12-07", "hide_header": True}
    assert countdown.validate_config(panel["node"]["config"]) is None
    # no Search computes it: the countdown panel has no USES_SEARCH edge
    assert not [e for e in bundle["edges"] if e["edge"]["edge_type"] == "USES_SEARCH"
                and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]]
    assert not [n for n in bundle["nodes"] if n["entity"]["entity_type"] == "search" and "2026-12-07" in json.dumps(n["node"])]
    assert uuid.UUID(panel["entity"]["entity_id"]).version == 7


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-7")
@pytest.mark.django_db(transaction=True, databases=["default", "search_readonly"])
def test_the_last_refresh_search_returns_the_newest_scan_run_time() -> None:
    """Imports the bundle's own Search node beside scan runs and runs it: with none the row is null (unobserved, never 0);
    with several the newest `observed_at` wins, and a run that states no time does not count."""
    from tap_grid.grift import grift_import
    from tap_grid.models import Search
    from tap_grid.search import execute_search

    (search,) = [n for n in _bundle()["nodes"] if n["node"].get("name") == "playground — report last refresh"]

    def run_node(key: str, observed: str | None) -> dict[str, Any]:
        return {
            "entity": {"entity_id": str(uuid.uuid7()), "entity_type": "compliance_core__compliance_scan_run", "name": key, "dimensions": {}},
            "node": {"source": "test", "run_key": key, "observed_at": observed},
        }

    def run() -> Any:
        row = Search.objects.get(entity_id=search["entity"]["entity_id"])
        result = execute_search(row, None, layer="extended")
        envelope = result["results"] if "results" in result else result
        (only,) = envelope["rows"]
        return only["last_vulnerability_scan"]

    def load(*nodes: dict[str, Any]) -> None:
        batch = {"batch_entity": {"entity_id": str(uuid.uuid7()), "entity_type": "batch", "name": "t", "dimensions": {}},
                 "batch_node": {"source": "t", "name": "t", "description": "t"}, "nodes": [search, *nodes], "edges": []}
        result = grift_import({"metadata": {"grift_version": "0"}, "_reserved": {}, "batches": [batch]})
        assert result.success, [e.message for e in result.errors]

    load()
    assert run() is None
    load(run_node("a", "2026-10-12T00:00:00Z"), run_node("b", "2026-10-19T17:33:47Z"), run_node("c", None))
    assert datetime.fromisoformat(str(run()).replace("Z", "+00:00")).astimezone(UTC) == datetime(2026, 10, 19, 17, 33, 47, tzinfo=UTC)
