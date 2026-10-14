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
 * Order comes from tags on the nodes: a subnet's `layout:order` tag (public 0, private 1, isolated 2) is
 * its column in the VPC, after the internet gateway, so the request path reads left to right: gateway,
 * public tier (load balancer), private tier (web task, worker), isolated tier (database).
 * The subnets of one tier in several zones are copies of each other: they are drawn as one stacked
 * subnet carrying the count, with what runs in the first zone inside it (stack.js).
 * Every other edge in the scene is a line.
 *
 * The internet gateway, the load balancer, the database, the people and their computers, and GitHub are shown
 * as icon nodes (icon-node.js): the type icon is the card and the name sits below it, so each says "this
 * thing is here" without drawing what is inside it. Icon nodes are terminal, so a computer's local account
 * and GitHub's accounts, repository, workflow, runs and packages are not drawn.
 */

import {projectNested, ELEVATION_HIDDEN_CLASS} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";
import {applyStack, STACK_COLLAPSED_CLASS} from "/static/tap_viz/js/runtime/stack.js";
import {applyIconNodes} from "/static/tap_viz/js/runtime/icon-node.js";

const T = {
    organization: "aws_core__aws_organization",
    account: "aws_core__aws_account",
    vpc: "aws_core__aws_vpc",
    subnet: "aws_core__aws_subnet",
    igw: "aws_core__aws_internet_gateway",
    alb: "aws_core__aws_alb",
    rds: "aws_core__aws_rds_instance",
    lambda: "aws_core__aws_lambda",
    bucket: "aws_core__aws_s3_bucket",
    secret: "aws_core__aws_secrets_manager_secret",
    cluster: "aws_core__aws_ecs_cluster",
    human: "identity_core__human",
    host: "computing_core__host",
    platform: "github_core__github_platform",
    ghAccount: "github_core__github_account",
    repo: "github_core__github_repository",
    workflow: "github_core__github_workflow",
    package: "github_core__github_package",
};
const E = {
    enrolls: "ENROLLS_ACCOUNT__aws_core",
    belongs: "BELONGS_TO_ACCOUNT__aws_core",
    partitioned: "PARTITIONED_INTO_SUBNET__aws_core",
    attachedToVpc: "ATTACHED_TO_VPC__aws_core",
    residesInSubnet: "RESIDES_IN_SUBNET__aws_core",
    runsService: "RUNS_SERVICE__aws_core",
    definesOsUser: "DEFINES_OS_USER__computing_core",
    hostsAccount: "HOSTS_ACCOUNT__github_core",
    ownsRepo: "OWNS_REPO__github_core",
    definesWorkflow: "DEFINES_WORKFLOW__github_core",
    executesWorkflow: "EXECUTES_WORKFLOW__github_core",
    publishesPackage: "PUBLISHES_PACKAGE__github_core",
    publishesVersion: "PUBLISHES_PACKAGE_VERSION__github_core",
};
const CONTAINERS = [T.organization, T.account, T.vpc, T.subnet, T.cluster, T.host, T.platform, T.ghAccount, T.repo, T.workflow, T.package];
//: Top-level columns, left to right, by the `actor` and `device` dimension values on a person or a computer.
//: Everything else with a `layout:column` tag (the organization, GitHub) takes the tag. The row reads
//: customer, the product account's machinery, GitHub, developer.
const ACTOR_COLUMN = {customer: 0, administrator: 1, developer: 3};
//: Shown as icon nodes: the type icon is the card, the name is below it.
const ICON_TYPES = [T.igw, T.alb, T.rds, T.lambda, T.bucket, T.secret, T.human, T.host, T.platform];
const ICON = {width: 84, height: 84};
//: Place in the column: the person, then their computer.
const KIND_ORDER = {[T.human]: 1, [T.host]: 2};

const LEAF = {width: 200, height: 54};
const SUBNET = {width: 230, height: 90};
const CONTAINER = {width: 220, height: 110};

export async function execute(context) {
    const {cy, trigger_reason} = context;
    const chrome = applyStandardChrome(cy);
    const labelInset = parentLabelInset({...chrome, inset: 16});
    //: The bottom edge leaves room for the name under an icon node, which is drawn outside its card.
    const pad = {top: 14 + labelInset, right: 24, bottom: 40, left: 24};

    const types = [...new Set(cy.nodes().map((n) => n.data("entity_type")).filter(Boolean))];
    const baseSizes = Object.fromEntries(types.map((t) => [t, t === T.subnet ? SUBNET : CONTAINERS.includes(t) ? CONTAINER : LEAF]));
    const piles = _collapseZoneCopies(cy);
    applyIconNodes(cy, {
        members: cy.nodes().filter((n) => ICON_TYPES.includes(n.data("entity_type")) && !n.hasClass(ELEVATION_HIDDEN_CLASS)),
        ...ICON, iconNodeId: "landing",
    });
    _stampVpcColumns(cy);
    _stampRootColumns(cy);

    const result = await projectNested(cy, {
        relationships: [
            {name: "org-enrolls", gryphon: `(parent:${T.organization})-[:${E.enrolls}]->(child)`},
            {name: "account-holds", gryphon: `(parent:${T.account})<-[:${E.belongs}]-(child)`},
            {name: "vpc-holds-subnets", gryphon: `(parent:${T.vpc})-[:${E.partitioned}]->(child)`},
            {name: "vpc-holds-gateway", gryphon: `(parent:${T.vpc})<-[:${E.attachedToVpc}]-(child)`},
            {name: "subnet-holds", gryphon: `(parent:${T.subnet})<-[:${E.residesInSubnet}]-(child)`},
            {name: "cluster-holds", gryphon: `(parent:${T.cluster})-[:${E.runsService}]->(child)`},
            {name: "host-holds", gryphon: `(parent:${T.host})-[:${E.definesOsUser}]->(child)`},
            {name: "platform-holds", gryphon: `(parent:${T.platform})-[:${E.hostsAccount}]->(child)`},
            {name: "github-account-holds-repo", gryphon: `(parent:${T.ghAccount})-[:${E.ownsRepo}]->(child)`},
            {name: "repo-holds-workflow", gryphon: `(parent:${T.repo})-[:${E.definesWorkflow}]->(child)`},
            {name: "workflow-holds-run", gryphon: `(parent:${T.workflow})<-[:${E.executesWorkflow}]-(child)`},
            {name: "github-account-holds-package", gryphon: `(parent:${T.ghAccount})-[:${E.publishesPackage}]->(child)`},
            {name: "package-holds-version", gryphon: `(parent:${T.package})-[:${E.publishesVersion}]->(child)`},
        ],
        baseSizes,
        padding: 24,
        paddings: Object.fromEntries(CONTAINERS.map((t) => [t, pad])),
        innerLayout: {name: "ranked", sort: "order", columnGap: 90, rowGap: 28},
        innerLayouts: {
            [T.cluster]: {name: "flow", gap: 28, sort: "label"},
            [T.host]: {name: "flow", gap: 12, sort: "label"},
            [T.platform]: {name: "flow", gap: 20, sort: "label"},
            [T.ghAccount]: {name: "flow", gap: 20, sort: "label"},
            [T.repo]: {name: "flow", gap: 12, sort: "label"},
            [T.workflow]: {name: "flow", gap: 12, sort: "label"},
            [T.package]: {name: "flow", gap: 12, sort: "label"},
            [T.organization]: {name: "flow", gap: 24, sort: "area-desc", aspect: 0.6},
            [T.account]: {name: "flow", gap: 28, sort: "area-desc", aspect: 1.6},
            [T.vpc]: {name: "ranked", sort: "order", columnGap: 16, rowGap: 12},
            [T.subnet]: {name: "flow", gap: 8, sort: "label"},
        },
    });

    piles.forEach((pile) => {
        applyStack(cy, pile);
        // The runtime draws a pile's cards below every nesting layer; lift them to just under their own box
        // so they show inside the VPC.
        const z = Number(pile.representative.style("z-index")) || 0;
        cy.nodes(`[_stack_id = "${pile.stackId}"][_is_stack_card]`).forEach((card) => card.style("z-index", z - card.data("_stack_depth")));
    });

    // An empty container is still a box, not a leaf.
    cy.nodes(CONTAINERS.map((t) => `[entity_type = "${t}"]`).join(", ")).forEach((n) => {
        if (n.data("_is_icon_node")) return;
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
 * The subnets of one VPC that share a tier (the same `layout:order` tag) are zone copies of each other.
 * Collapse all but the first (by label) and what resides in them before nesting, so the box is sized for
 * one; return the stack options to apply once the scene is positioned.
 */
function _collapseZoneCopies(cy) {
    const byTier = new Map();
    cy.edges().forEach((e) => {
        if (_edgeType(e) !== E.partitioned) return;
        const subnet = e.target();
        const key = e.source().id() + "|" + ((subnet.data("tags") || {})["layout:order"] ?? "");
        if (!byTier.has(key)) byTier.set(key, []);
        byTier.get(key).push(subnet);
    });
    const residentsOf = new Map();
    cy.edges().forEach((e) => {
        if (_edgeType(e) !== E.residesInSubnet) return;
        if (!residentsOf.has(e.target().id())) residentsOf.set(e.target().id(), []);
        residentsOf.get(e.target().id()).push(e.source());
    });
    const piles = [];
    byTier.forEach((subnets, key) => {
        if (subnets.length < 2) return;
        subnets.sort((a, b) => String(a.data("label")).localeCompare(String(b.data("label"))));
        const [representative, ...copies] = subnets;
        // Out of the nesting while it runs, so the boxes are sized for one zone; applyStack collapses the copies.
        const hide = (n) => n.addClass(ELEVATION_HIDDEN_CLASS + " " + STACK_COLLAPSED_CLASS);
        copies.forEach((copy) => {
            hide(copy);
            (residentsOf.get(copy.id()) || []).forEach(hide);
        });
        piles.push({
            members: subnets, representative, stackId: "zones:" + key, direction: "down-right", depthCap: 2, chip: false,
            label: ((representative.data("tags") || {}).tier || representative.data("label")) + " ×" + subnets.length,
        });
    });
    return piles;
}

/**
 * Stamp the `ranked` columns inside each VPC, left to right: the internet gateway, then the subnet tiers
 * in `layout:order`.
 */
function _stampVpcColumns(cy) {
    cy.edges().forEach((e) => {
        if (_edgeType(e) !== E.partitioned) return;
        const subnet = e.target();
        if (subnet.hasClass(ELEVATION_HIDDEN_CLASS)) return;
        const tier = Number((subnet.data("tags") || {})["layout:order"]);
        subnet.data({_stage: Number.isFinite(tier) ? tier + 1 : 99, _order: 0});
    });
    cy.edges().forEach((e) => {
        if (_edgeType(e) === E.attachedToVpc) e.source().data({_stage: 0, _order: 0});
    });
}

/**
 * Stamp the top-level `ranked` columns, left to right: customers, then the organization with the
 * administrator beneath it, then GitHub, then the developer. A person or computer takes its column
 * from its `actor` / `device` dimension; a node with a `layout:column` tag takes the tag.
 */
function _stampRootColumns(cy) {
    cy.nodes().forEach((n) => {
        const type = n.data("entity_type");
        const dims = n.data("dimensions") || {};
        const tags = n.data("tags") || {};
        const actor = dims.actor || dims.device;
        if (actor in ACTOR_COLUMN && KIND_ORDER[type]) {
            const column = ACTOR_COLUMN[actor];
            //: The administrator goes beneath the organization, which is first in column 1.
            const below = column === 1 ? 1 : 0;
            n.data({_stage: column, _order: below + KIND_ORDER[type]});
        } else if (tags["layout:column"] !== undefined) {
            n.data({_stage: Number(tags["layout:column"]), _order: Number(tags["layout:order"] || 0)});
        }
    });
}
