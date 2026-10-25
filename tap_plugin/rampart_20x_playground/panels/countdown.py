"""rampart_countdown: the whole days remaining until a fixed date, counted in the browser
(``req-rampart-20x-playground-page-reporting-10``).

The panel reads only its own config, runs no Search and writes no markup. The server renders the target date as the
panel's value, so the panel is correct with no script; ``rampart_20x_playground/js/countdown.js``, an external static file
named in ``js`` below (never inline), replaces that value with the whole days left. The look comes from compliance_core's
report stylesheet, so the panel reads as one more section of the report panel above it.

This module imports no Django, so the schema and the date handling are testable without it.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any, ClassVar

import jsonschema

if TYPE_CHECKING:
    from django.http import HttpRequest

    from tap_web.models import Panel

DEFAULT_HEADING = "Timeline"

COUNTDOWN_PANEL_CONFIG_SCHEMA: dict[str, Any] = {
    "description": (
        "Config of a rampart_countdown panel: a heading, a label and a target date. The panel shows the date as plain "
        "text and a script replaces it with the whole days left until that date. Config holds text only, never HTML."
    ),
    "type": "object",
    "additionalProperties": False,
    "required": ["label", "target_date"],
    "properties": {
        "heading": {
            "description": "The section heading shown above the line. Default Timeline.",
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
        },
        "label": {
            "description": "The line's label, for example Days To December 7.",
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
        },
        "target_date": {
            "description": "The date counted down to, as YYYY-MM-DD. The count is whole days from now to 00:00 UTC of this date.",
            "type": "string",
            "pattern": r"^\d{4}-\d{2}-\d{2}\Z",
        },
        "hide_header": {
            "description": "True hides the panel header bar.",
            "type": "boolean",
        },
    },
}


def validate_config(config: Any) -> str | None:
    """None when the config is valid, else the first problem as a short sentence."""
    try:
        jsonschema.validate(config, COUNTDOWN_PANEL_CONFIG_SCHEMA)
        date.fromisoformat(config["target_date"])  # the pattern admits 2026-02-31; the calendar does not
    except jsonschema.ValidationError as exc:
        where = "/".join(str(p) for p in exc.absolute_path)
        return f"{where}: {exc.message}" if where else exc.message
    except ValueError:
        return "target_date: not a calendar date"
    return None


class RampartCountdownPanelType:
    slug: ClassVar[str] = "rampart_countdown"
    label: ClassVar[str] = "Rampart Countdown"
    view: ClassVar[str] = "rampart_20x_playground/panels/countdown.html"
    css: ClassVar[list[str]] = ["compliance_core/css/report.css"]
    js: ClassVar[list[str]] = ["rampart_20x_playground/js/countdown.js"]
    editor_view: ClassVar[str] = ""
    config_defaults: ClassVar[dict[str, Any]] = {}
    form_class: ClassVar[Any] = None

    @classmethod
    def get_view_context(cls, panel: Panel, request: HttpRequest) -> dict[str, Any]:
        config = panel.config if isinstance(panel.config, dict) else {}
        problem = validate_config(config)
        if problem:
            return {"state": "bad_config", "detail": problem}
        return {
            "state": "ok",
            "heading": config.get("heading", DEFAULT_HEADING),
            "label": config["label"],
            "target_date": config["target_date"],
        }
