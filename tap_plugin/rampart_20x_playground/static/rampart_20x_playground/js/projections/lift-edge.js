/**
 * lift-edge: the edge lift of the Overview's account elevation (Overview Wave 4).
 *
 * PLAYGROUND EXCEPTION (standing exception, George 2026-10-19; exit: fold into tap_viz when the concepts settle).
 * Written to the API the tap_viz runtime should get, a `lift_edge` section the layout configures, so moving it
 * there is a move, not a rewrite: a list of containment-style relationships shaped exactly like `projectNested`'s
 * (`{name, gryphon}`), which say which node is contained by which. An edge that ends on a contained node is
 * re-pointed onto the outermost node that holds it, and the re-pointed copies are deduplicated.
 *
 * Follows applyStack's edge collapse: the lifted edges are synthetic edges added beside the originals, the originals
 * are hidden with the elevation-hidden class, and destroy() removes the synthetic edges and restores the originals.
 *
 * What the lift reads is DATA (the relationships), never a type, name or id.
 */

import {resolveNesting, ELEVATION_HIDDEN_CLASS, HIDDEN_CONTAINMENT_CLASS} from "/static/tap_viz/js/runtime/nested-projection.js";

export const LIFTED_EDGE_CLASS = "tap-lifted-edge";

/**
 * The nodes the relationships contain, with the outermost node that holds each.
 *
 * @param {cytoscape.Core} cy
 * @param {Array<{name: string, gryphon: string}>} relationships
 * @returns {{outermost: Map<string, string>, warnings: Array}}
 */
export function containedNodes(cy, relationships) {
    const {parentByChildId, warnings} = resolveNesting(cy, relationships);
    const outermost = new Map();
    Object.keys(parentByChildId).forEach((childId) => {
        let top = childId;
        const seen = new Set();
        while (parentByChildId[top] && !seen.has(top)) {
            seen.add(top);
            top = parentByChildId[top];
        }
        outermost.set(childId, top);
    });
    return {outermost, warnings};
}

/**
 * Lift the edges that end on a contained node onto the outermost node that holds it.
 *
 * @param {cytoscape.Core} cy
 * @param {Object} config
 * @param {Array<{name: string, gryphon: string}>} config.relationships The `lift_edge` section.
 * @returns {{destroy: Function, count: number, contained: cytoscape.Collection}}
 *   count: how many lifted edges now stand; contained: the nodes the relationships contain (the interior).
 */
export function liftEdge(cy, config) {
    const {outermost} = containedNodes(cy, config.relationships || []);
    const lifted = [];
    const originals = [];
    const seen = new Set();
    const topOf = (id) => outermost.get(id) || id;
    cy.edges().forEach((edge) => {
        if (edge.hasClass(LIFTED_EDGE_CLASS) || edge.hasClass(HIDDEN_CONTAINMENT_CLASS)) return;
        const from = edge.source().id();
        const to = edge.target().id();
        if (!outermost.has(from) && !outermost.has(to)) return;
        originals.push(edge);
        const source = topOf(from);
        const target = topOf(to);
        // An edge inside the lifted node (container to program, program to program) is not re-pointed: it ends in it.
        if (source === target) return;
        const type = edge.data("edge_type") || edge.data("label") || "";
        const key = `${source}|${target}|${type}`;
        if (seen.has(key)) return;
        seen.add(key);
        lifted.push({
            group: "edges",
            data: {...edge.data(), id: `lift:${key}`, source, target, _lifted_from: edge.id()},
            classes: LIFTED_EDGE_CLASS,
        });
    });
    originals.forEach((edge) => edge.addClass(ELEVATION_HIDDEN_CLASS));
    const added = lifted.length ? cy.add(lifted) : cy.collection();
    return {
        count: lifted.length,
        contained: cy.nodes().filter((n) => outermost.has(n.id())),
        destroy() {
            added.remove();
            originals.forEach((edge) => edge.removeClass(ELEVATION_HIDDEN_CLASS));
        },
    };
}
