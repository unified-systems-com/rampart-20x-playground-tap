/**
 * landing — the nested layout behind /playground (req-rampart-20x-playground-govcloud-view).
 *
 * Configuration of the tap_viz runtime and data reads only; no geometry of its own
 * (req-rampart-20x-playground-nongoals). Containment comes only from edges aws_core declares:
 *
 *   - organization ⊃ account      ENROLLS_ACCOUNT (organization → account)
 *   - account ⊃ its members       BELONGS_TO_ACCOUNT (resource → account)
 *   - VPC ⊃ its subnets           PARTITIONED_INTO_SUBNET (VPC → subnet)
 *   - VPC ⊃ its internet gateway  ATTACHED_TO_VPC (gateway → VPC)
 *   - subnet ⊃ what runs in it    RESIDES_IN_SUBNET (resource → subnet)
 *   - cluster ⊃ its services      RUNS_SERVICE (cluster → service)
 *
 * Order comes from typed fields and tags on the nodes: a subnet's `availability_zone` picks its column
 * in the VPC and its `layout:order` tag (public 0, private 1, isolated 2) its place in the column.
 * Every other edge in the scene is a line.
 */

import {projectNested} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";

const T = {
    organization: "aws_core__aws_organization",
    account: "aws_core__aws_account",
    vpc: "aws_core__aws_vpc",
    subnet: "aws_core__aws_subnet",
    igw: "aws_core__aws_internet_gateway",
    cluster: "aws_core__aws_ecs_cluster",
};
const E = {
    enrolls: "ENROLLS_ACCOUNT__aws_core",
    belongs: "BELONGS_TO_ACCOUNT__aws_core",
    partitioned: "PARTITIONED_INTO_SUBNET__aws_core",
    attachedToVpc: "ATTACHED_TO_VPC__aws_core",
    residesInSubnet: "RESIDES_IN_SUBNET__aws_core",
    runsService: "RUNS_SERVICE__aws_core",
};
const CONTAINERS = [T.organization, T.account, T.vpc, T.subnet, T.cluster];
//: Column for what a VPC holds directly, left of its zone columns.
const VPC_LEVEL_STAGE = -1;

const LEAF = {width: 200, height: 54};
const SUBNET = {width: 230, height: 90};
const CONTAINER = {width: 220, height: 110};

export async function execute(context) {
    const {cy, trigger_reason} = context;
    const chrome = applyStandardChrome(cy);
    const labelInset = parentLabelInset({...chrome, inset: 16});
    const pad = {top: 14 + labelInset, right: 24, bottom: 24, left: 24};

    const types = [...new Set(cy.nodes().map((n) => n.data("entity_type")).filter(Boolean))];
    const baseSizes = Object.fromEntries(types.map((t) => [t, t === T.subnet ? SUBNET : CONTAINERS.includes(t) ? CONTAINER : LEAF]));
    _stampVpcColumns(cy);

    const result = await projectNested(cy, {
        relationships: [
            {name: "org-enrolls", gryphon: `(parent:${T.organization})-[:${E.enrolls}]->(child)`},
            {name: "account-holds", gryphon: `(parent:${T.account})<-[:${E.belongs}]-(child)`},
            {name: "vpc-holds-subnets", gryphon: `(parent:${T.vpc})-[:${E.partitioned}]->(child)`},
            {name: "vpc-holds-gateway", gryphon: `(parent:${T.vpc})<-[:${E.attachedToVpc}]-(child)`},
            {name: "subnet-holds", gryphon: `(parent:${T.subnet})<-[:${E.residesInSubnet}]-(child)`},
            {name: "cluster-holds", gryphon: `(parent:${T.cluster})-[:${E.runsService}]->(child)`},
        ],
        baseSizes,
        padding: 24,
        paddings: Object.fromEntries(CONTAINERS.map((t) => [t, pad])),
        innerLayout: {name: "flow", gap: 28, sort: "label"},
        innerLayouts: {
            [T.organization]: {name: "flow", gap: 24, sort: "area-desc", aspect: 0.6},
            [T.account]: {name: "flow", gap: 28, sort: "area-desc", aspect: 1.6},
            [T.vpc]: {name: "ranked", sort: "order", columnGap: 16, rowGap: 12},
            [T.subnet]: {name: "flow", gap: 8, sort: "label"},
        },
    });

    // An empty container is still a box, not a leaf.
    cy.nodes(CONTAINERS.map((t) => `[entity_type = "${t}"]`).join(", ")).forEach((n) => {
        if (!cy.nodes().some((c) => c.data("_viewport_parent") === n.id())) n.addClass("tap-viewport-parent");
    });
    placeParentLabels(cy, {
        anchor: "upper-left", inset: 16,
        parentFontSize: chrome.parentFontSize, parentFontWeight: chrome.parentFontWeight,
    });
    if (trigger_reason === "initial_load") cy.fit(cy.nodes(":visible"), 40);
    return {warnings: result.warnings || []};
}

function _edgeType(e) {
    return e.data("edge_type") || e.data("label") || "";
}

/**
 * Stamp the `ranked` columns inside each VPC: one column per availability zone of its subnets (zones in
 * name order), the subnet tiers in `layout:order` within it; what the VPC holds directly stands in a
 * column to their left.
 */
function _stampVpcColumns(cy) {
    const subnetsOf = new Map();
    cy.edges().forEach((e) => {
        if (_edgeType(e) !== E.partitioned) return;
        if (!subnetsOf.has(e.source().id())) subnetsOf.set(e.source().id(), []);
        subnetsOf.get(e.source().id()).push(e.target());
    });
    subnetsOf.forEach((subnets) => {
        const zone = (s) => (s.data("fields") || {}).availability_zone || "";
        const zones = [...new Set(subnets.map(zone))].sort((a, b) => a.localeCompare(b));
        subnets.forEach((s) => {
            const tier = Number((s.data("tags") || {})["layout:order"]);
            s.data({_stage: zones.indexOf(zone(s)), _order: Number.isFinite(tier) ? tier : 99});
        });
    });
    cy.edges().forEach((e) => {
        if (_edgeType(e) === E.attachedToVpc) e.source().data({_stage: VPC_LEVEL_STAGE, _order: 0});
    });
}
