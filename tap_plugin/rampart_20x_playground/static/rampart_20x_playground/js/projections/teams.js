/**
 * teams: the nested layout behind the graph on the Teams page (req-rampart-20x-playground-teams-viz).
 *
 * Configuration of the tap_viz runtime and data reads only; no geometry of its own
 * (req-rampart-20x-playground-nongoals). Containment comes only from the one edge identity_core declares for it:
 *
 *   - team ⊃ its people        BELONGS_TO_TEAM (human → team)
 *   - team ⊃ its child teams   BELONGS_TO_TEAM (team → parent team)
 *
 * Both are single-hop nesting patterns (spec-viz-nesting.md); the runtime stamps the containment, hides those
 * edges and sizes the boxes. A leader is read from the LEADS_TEAM edges in the scene: the human at the source of
 * one takes the leader colours, as node data (`fill_color`, `border_color`, `label_color`), and the edge itself is
 * hidden, because the leader is already inside the team they lead. The palette is chosen for the fixed #f1f0ec
 * canvas, which is the same in light and dark.
 *
 * Standard tap layout module: `export async function execute(context)` (spec-viz-layouts.md).
 */

import {projectNested, ELEVATION_HIDDEN_CLASS} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";

const T = {team: "identity_core__team", human: "identity_core__human"};
const BELONGS = "BELONGS_TO_TEAM__identity_core";
const LEADS = "LEADS_TEAM__identity_core";

// A leader: a deep teal with white text, against the cream of the other people and the teams.
const LEADER = {fill_color: "#0f5c70", border_color: "#083a47", label_color: "#ffffff"};
const PERSON = {width: 210, height: 52};
const TEAM = {width: 240, height: 120};
const PADDING = 24;
const LABEL_INSET = 12;

function _edgeType(e) {
    return e.data("edge_type") || e.data("label") || "";
}

//: Colour the source of every LEADS_TEAM edge as a leader, then hide the edge (the leader is drawn inside the team).
function _markLeaders(cy) {
    cy.edges().filter((e) => _edgeType(e) === LEADS).forEach((e) => {
        e.source().data(LEADER);
        e.addClass(ELEVATION_HIDDEN_CLASS);
    });
}

export async function execute(context) {
    const {cy, trigger_reason} = context;
    const chrome = applyStandardChrome(cy, {leafTypes: [T.human], leafMaxWidth: PERSON.width - 24});
    const inset = parentLabelInset({...chrome, inset: LABEL_INSET});

    _markLeaders(cy);
    // Boxes, not ellipses, with the team's label inside its top-left corner (a data override of the model's display hint).
    cy.nodes().forEach((n) => n.data("shape", "round-rectangle"));
    cy.nodes(`[entity_type = "${T.team}"]`).forEach((n) => n.data("label_position", "inside"));

    const result = await projectNested(cy, {
        relationships: [
            {name: "team-holds-person", gryphon: `(parent:${T.team})<-[:${BELONGS}]-(child:${T.human})`},
            {name: "team-holds-team", gryphon: `(parent:${T.team})<-[:${BELONGS}]-(child:${T.team})`},
        ],
        baseSizes: {[T.human]: PERSON, [T.team]: TEAM},
        padding: PADDING,
        paddings: {[T.team]: {top: PADDING + inset, right: PADDING, bottom: PADDING, left: PADDING}},
        innerLayout: {name: "flow", sort: "area-desc", gap: 20},
    });

    placeParentLabels(cy, {
        anchor: "upper-left", inset: LABEL_INSET,
        parentFontSize: chrome.parentFontSize, parentFontWeight: chrome.parentFontWeight,
    });
    if (trigger_reason === "initial_load") cy.fit(cy.nodes(":visible"), 40);
    return {warnings: result.warnings || []};
}
