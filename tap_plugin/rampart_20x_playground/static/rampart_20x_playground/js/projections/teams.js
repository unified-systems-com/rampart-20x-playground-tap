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
 * edges and sizes the boxes.
 *
 * Arrangement is the `ranked` natural layout (spec-viz-nested-projection.md): columns by the integer `_stage`, stacked
 * top-to-bottom by the integer `_order`. Both are stamped here from facts on the graph, never from a label:
 *
 *   - a person is stage 0, a child team is stage 1 + its rank among its sibling teams (typed `name` field), so the
 *     child teams of a team stand side by side in one row and the people of a team stack in one column;
 *   - a leader is the human at the source of a LEADS_TEAM edge: order 0, so the leader is first in the stack, at
 *     the top of the team. The LEADS_TEAM edge is hidden, because the leader is already inside the team.
 *
 * Every person is drawn as an icon-centric-solo node (icon-node.js, req-viz-icon-node-solo): the type icon and the
 * name, no card. A leader's name is set on the leader colours; a solo icon has no fill, so the colour lives on the label.
 * A team stays a box, because an icon node is terminal and would hide what the team holds. The palette is chosen for the
 * fixed #f1f0ec canvas, which is the same in light and dark.
 *
 * Standard tap layout module: `export async function execute(context)` (spec-viz-layouts.md).
 */

import {projectNested, ELEVATION_HIDDEN_CLASS} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";
import {applyIconNodes} from "/static/tap_viz/js/runtime/icon-node.js";

const T = {team: "identity_core__team", human: "identity_core__human"};
const BELONGS = "BELONGS_TO_TEAM__identity_core";
const LEADS = "LEADS_TEAM__identity_core";

// A leader's name: white on a deep teal pill, against the dark slate of the other names.
const LEADER_LABEL = {
    "color": "#ffffff", "font-weight": 700,
    "text-background-color": "#0f5c70", "text-background-opacity": 1,
    "text-background-padding": "3px", "text-background-shape": "round-rectangle",
};
const PERSON_LABEL = {"color": "#1e293b", "font-weight": 400, "text-background-opacity": 0};
const PERSON = {width: 64, height: 64};
const TEAM = {width: 240, height: 120};
const PADDING = 24;
const LABEL_INSET = 12;
const NAME_ROOM = 36; // a person's name stands below the icon, outside its box: room at the foot of the team

function _edgeType(e) {
    return e.data("edge_type") || e.data("label") || "";
}

//: The humans at the source of a LEADS_TEAM edge, with the edge hidden (the leader is drawn inside the team).
function _leaders(cy) {
    const leaders = cy.collection();
    cy.edges().filter((e) => _edgeType(e) === LEADS).forEach((e) => {
        leaders.merge(e.source());
        e.addClass(ELEVATION_HIDDEN_CLASS);
    });
    return leaders;
}

//: Stamp `_stage` and `_order` for the `ranked` layout from the BELONGS_TO_TEAM edges and the leaders.
//: A person is stage 0; a child team is stage 1 + its rank among its sibling teams by typed name, so siblings sit in a row.
function _stampRanks(cy, leaders) {
    const siblings = new Map();
    cy.edges().filter((e) => _edgeType(e) === BELONGS).forEach((e) => {
        const parent = e.target().id();
        if (!siblings.has(parent)) siblings.set(parent, cy.collection());
        siblings.set(parent, siblings.get(parent).merge(e.source()));
    });
    siblings.forEach((children) => {
        const teams = children.filter(`[entity_type = "${T.team}"]`).sort((a, b) =>
            String((a.data("fields") || {}).name || "").localeCompare(String((b.data("fields") || {}).name || "")));
        teams.forEach((n, i) => n.data({_stage: 1 + i, _order: 0}));
        children.filter(`[entity_type = "${T.human}"]`).forEach((n) =>
            n.data({_stage: 0, _order: leaders.contains(n) ? 0 : 1}));
    });
}

export async function execute(context) {
    const {cy, trigger_reason} = context;
    const chrome = applyStandardChrome(cy);
    const inset = parentLabelInset({...chrome, inset: LABEL_INSET});

    const leaders = _leaders(cy);
    _stampRanks(cy, leaders);

    // People are solo icons (the type icon and the name, no card); a team stays a box with its name inside its top edge, centred (clear of the type-icon badge in the corner).
    const people = cy.nodes(`[entity_type = "${T.human}"]`);
    applyIconNodes(cy, {members: people, width: PERSON.width, height: PERSON.height, solo: true, iconNodeId: "teams-people"});
    people.style(PERSON_LABEL);
    leaders.style(LEADER_LABEL);
    cy.nodes(`[entity_type = "${T.team}"]`).forEach((n) => {
        n.data("shape", "round-rectangle");
        n.data("label_position", "inside");
    });

    const result = await projectNested(cy, {
        relationships: [
            {name: "team-holds-person", gryphon: `(parent:${T.team})<-[:${BELONGS}]-(child:${T.human})`},
            {name: "team-holds-team", gryphon: `(parent:${T.team})<-[:${BELONGS}]-(child:${T.team})`},
        ],
        baseSizes: {[T.human]: PERSON, [T.team]: TEAM},
        padding: PADDING,
        paddings: {[T.team]: {top: PADDING + inset, right: PADDING, bottom: PADDING + NAME_ROOM, left: PADDING}},
        innerLayout: {name: "ranked", sort: "order", columnGap: 56, rowGap: 44},
    });

    placeParentLabels(cy, {
        anchor: "top-center", inset: LABEL_INSET,
        parentFontSize: chrome.parentFontSize, parentFontWeight: chrome.parentFontWeight,
    });
    if (trigger_reason === "initial_load") cy.fit(cy.nodes(":visible"), 40);
    return {warnings: result.warnings || []};
}
