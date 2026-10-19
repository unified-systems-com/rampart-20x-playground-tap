/**
 * landing: the nested layout behind the Overview page (req-rampart-20x-playground-govcloud-view).
 *
 * Configuration of the tap_viz runtime and data reads only; no geometry of its own
 * (req-rampart-20x-playground-nongoals). The overview shows the running parts of the system inside the product
 * account: the organization, the other accounts, the ECS cluster and service and the identity provider stay on
 * the grid and are not selected by the page's Searches. Containment comes only from edges aws_core declares:
 *
 *   - account ⊃ its members       BELONGS_TO_ACCOUNT (resource → account)
 *   - VPC ⊃ its subnets           PARTITIONED_INTO_SUBNET (VPC → subnet)
 *   - VPC ⊃ its internet gateway  ATTACHED_TO_VPC (gateway → VPC)
 *   - subnet ⊃ what runs in it    RESIDES_IN_SUBNET (resource → subnet)
 *
 * Order comes from tags on the nodes: a subnet's `layout:order` tag (public 0, private 1, isolated 2) is
 * its column in the VPC, after the internet gateway, so the request path reads left to right: gateway,
 * public tier (load balancer), private tier (web task), isolated tier (database).
 * The subnets of one tier in several zones are copies of each other: they are drawn as one stacked
 * subnet carrying the count, with what runs in the first zone inside it (stack.js).
 * Every other edge in the scene is a line.
 *
 * Top level, left to right: the customer and their computer, the product account, GitHub, the developer's computer and the developer. The administrator and their computer
 * stand beneath the product account, the computer above the person. The line of sight is one horizontal line,
 * left to right: the customer, their computer, the internet gateway, the load balancer, the database, GitHub, the
 * developer's computer and the developer. The load balancer is the anchor: the roots outside the account and the
 * gateway are put on its horizontal line (align-only). The database is already on it (the same VPC column).
 *
 * The people, their computers, the gateway, load balancer, database, Route 53 zone, ECR repository, Lambda,
 * buckets, secrets, pipeline and CodeBuild projects are icon-centric-solo nodes (icon-node.js): the icon and
 * its name, no card. GitHub is an icon node with a card. Icon nodes are terminal, so a computer's local account
 * and GitHub's accounts, repository, workflow, runs and packages are not drawn.
 *
 * Deploy path: the AWS icons of the delivery path (the secrets, the ECR repository, the buckets, the pipeline, the
 * Lambda and the CodeBuild projects) stand in ONE column, centred at the bottom-middle of the account, under the
 * certificate and the key.
 *
 * PLAYGROUND EXCEPTION (standing exception, George 2026-10-19: custom tweaks in the playground's JavaScript layout
 * are permitted while the concepts settle; exit: fold into tap_viz when they do). Each tweak below is marked
 * "playground exception" with the tap_viz runtime form it should become:
 *   1. the deploy column (a `column` tier kind of the tiered-rows natural layout, or a `stack` arrangement that
 *      reserves its own room in the container);
 *   2. the gateway on the anchor's line (an `alignTo` of a nested node in the ranked natural layout, so a nested
 *      column can be centre-aligned to an anchor without a post-pass).
 * Neither changes the Python, the vocabulary or the data rules.
 */

import {projectNested, ELEVATION_HIDDEN_CLASS} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";
import {applyStack, STACK_COLLAPSED_CLASS} from "/static/tap_viz/js/runtime/stack.js";
import {applyIconNodes} from "/static/tap_viz/js/runtime/icon-node.js";
import {alignDistributeHorizontal, alignDistributeVertical} from "/static/tap_viz/js/runtime/align-distribute.js";

const T = {
    vpc: "aws_core__aws_vpc",
    subnet: "aws_core__aws_subnet",
    account: "aws_core__aws_account",
    igw: "aws_core__aws_internet_gateway",
    alb: "aws_core__aws_alb",
    rds: "aws_core__aws_rds_instance",
    zone: "aws_core__aws_route53_zone",
    cert: "aws_core__aws_acm_certificate",
    key: "aws_core__aws_kms_key",
    ecr: "aws_core__aws_ecr_repository",
    pipeline: "aws_core__aws_codepipeline_pipeline",
    codebuild: "aws_core__aws_codebuild_project",
    lambda: "aws_core__aws_lambda",
    bucket: "aws_core__aws_s3_bucket",
    secret: "aws_core__aws_secrets_manager_secret",
    human: "identity_core__human",
    host: "computing_core__host",
    platform: "github_core__github_platform",
    ghAccount: "github_core__github_account",
    repo: "github_core__github_repository",
    workflow: "github_core__github_workflow",
    package: "github_core__github_package",
};
const E = {
    belongs: "BELONGS_TO_ACCOUNT__aws_core",
    partitioned: "PARTITIONED_INTO_SUBNET__aws_core",
    attachedToVpc: "ATTACHED_TO_VPC__aws_core",
    residesInSubnet: "RESIDES_IN_SUBNET__aws_core",
    definesOsUser: "DEFINES_OS_USER__computing_core",
    hostsAccount: "HOSTS_ACCOUNT__github_core",
    ownsRepo: "OWNS_REPO__github_core",
    definesWorkflow: "DEFINES_WORKFLOW__github_core",
    executesWorkflow: "EXECUTES_WORKFLOW__github_core",
    publishesPackage: "PUBLISHES_PACKAGE__github_core",
    publishesVersion: "PUBLISHES_PACKAGE_VERSION__github_core",
};
const CONTAINERS = [T.account, T.vpc, T.subnet, T.host, T.platform, T.ghAccount, T.repo, T.workflow, T.package];
//: Shown as icon nodes: the type icon is the card, the name is below it.
const ICON_TYPES = [T.platform];
const ICON = {width: 84, height: 84};
//: Shown as icon-centric-solo nodes at the icon-node size (no card): the people and their computers. Same box as
//: the carded icon nodes they were, so nothing moves.
const SOLO_ICON_TYPES = [T.human, T.host];
//: Shown as icon-centric-solo nodes: the icon and the name, no card.
const SOLO_TYPES = [T.igw, T.alb, T.rds, T.cert, T.key, T.zone, T.ecr, T.lambda, T.bucket, T.secret, T.pipeline, T.codebuild];
const SOLO = {width: 72, height: 72};
//: The deploy path inside the account: every AWS icon of the delivery path. The certificate and the key are not
//: part of it (they stand under the load balancer and the database).
const DEPLOY_TYPES = [T.secret, T.ecr, T.bucket, T.pipeline, T.lambda, T.codebuild];
//: Distance between the centres of two icons in the deploy column: the icon, then room for a three-line name.
const DEPLOY_PITCH = 120;

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
    const shown = (types) => cy.nodes().filter((n) => types.includes(n.data("entity_type")) && !n.hasClass(ELEVATION_HIDDEN_CLASS));
    applyIconNodes(cy, {members: shown(ICON_TYPES), ...ICON, iconNodeId: "landing"});
    applyIconNodes(cy, {members: shown(SOLO_ICON_TYPES), ...ICON, solo: true, iconNodeId: "landing-solo-icon"});
    applyIconNodes(cy, {members: shown(SOLO_TYPES), ...SOLO, solo: true, iconNodeId: "landing-solo"});
    // Playground exception (deploy column; should become a column tier of tiered-rows): the deploy icons are out
    // of the nesting while it runs, so the account is sized for its own rows; they are placed in one column below
    // them afterwards, which grows the account.
    const deploy = shown(DEPLOY_TYPES);
    deploy.addClass(ELEVATION_HIDDEN_CLASS);
    _stampVpcColumns(cy);
    _stampRootColumns(cy);

    const result = await projectNested(cy, {
        relationships: [
            {name: "account-holds", gryphon: `(parent:${T.account})<-[:${E.belongs}]-(child)`},
            {name: "vpc-holds-subnets", gryphon: `(parent:${T.vpc})-[:${E.partitioned}]->(child)`},
            {name: "vpc-holds-gateway", gryphon: `(parent:${T.vpc})<-[:${E.attachedToVpc}]-(child)`},
            {name: "subnet-holds", gryphon: `(parent:${T.subnet})<-[:${E.residesInSubnet}]-(child)`},
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
        innerLayout: {name: "ranked", sort: "order", columnGap: 90, rowGap: 56, columnLayout: "flow"},
        innerLayouts: {
            [T.host]: {name: "flow", gap: 12, sort: "label"},
            [T.platform]: {name: "flow", gap: 20, sort: "label"},
            [T.ghAccount]: {name: "flow", gap: 20, sort: "label"},
            [T.repo]: {name: "flow", gap: 12, sort: "label"},
            [T.workflow]: {name: "flow", gap: 12, sort: "label"},
            [T.package]: {name: "flow", gap: 12, sort: "label"},
            //: Inside the account, by row: the DNS zone in the top-left corner, the VPC, the certificate and the
            //: key (placed under the load balancer and the database). The deploy path is the column below them.
            [T.account]: {
                name: "tiered-rows", rowGap: 44, itemGap: 40,
                tiers: [
                    {name: "dns", entityTypes: [T.zone], align: "start"},
                    {name: "vpc", entityTypes: [T.vpc]},
                    {name: "protection", entityTypes: [T.cert, T.key]},
                ],
            },
            [T.vpc]: {name: "ranked", sort: "order", columnGap: 16, rowGap: 12},
            [T.subnet]: {name: "flow", gap: 8, sort: "label"},
        },
    });

    piles.forEach((pile) => {
        applyStack(cy, pile);
    });
    deploy.removeClass(ELEVATION_HIDDEN_CLASS);

    // Everything that stands outside the product's column already has its column; put it on the request
    // path's line. What stands in the product's column besides the account (the administrator's computer
    // and the administrator) goes under the account instead.
    if (cy.scratch("landing_row")) cy.scratch("landing_row").destroy();
    const anchor = shown([T.alb]).first();
    const account = shown([T.account]).first();
    const roots = cy.nodes().filter((n) => Number.isInteger(n.data("_stage")) && n.data("_viewport_parent") === undefined
        && !n.hasClass(ELEVATION_HIDDEN_CLASS));
    const productStage = account.nonempty() ? account.data("_stage") : undefined;
    if (anchor.nonempty()) {
        const row = roots.filter((n) => n.data("_stage") !== productStage);
        cy.scratch("landing_row", alignDistributeHorizontal(cy, {members: row, anchorNode: anchor, distribute: false, reactive: false}));
    }

    // Playground exception (gateway on the line; should become an anchor-relative align of a nested node in the
    // ranked natural layout): the internet gateway is the first column of the VPC and is top-aligned with it, so
    // it sits above the line. Put it on the anchor's line, align-only.
    const gateway = shown([T.igw]);
    if (anchor.nonempty() && gateway.nonempty()) {
        alignDistributeHorizontal(cy, {members: gateway, anchorNode: anchor, distribute: false, reactive: false});
    }

    // The certificate stands directly under the load balancer, and the key directly under the database.
    [[T.cert, T.alb], [T.key, T.rds]].forEach(([type, above]) => {
        const member = shown([type]), anchorNode = shown([above]).first();
        if (member.nonempty() && anchorNode.nonempty()) {
            alignDistributeVertical(cy, {members: member, anchorNode, distribute: false, reactive: false});
        }
    });

    // Under the account, top to bottom in their own order (the computer, then the person).
    const beneath = roots.filter((n) => n.data("_stage") === productStage && !n.same(account))
        .sort((a, b) => a.data("_order") - b.data("_order"));
    // Playground exception (deploy column): the account grows downward for the column; what stands beneath it
    // moves down by the same amount. The line of sight does not move (the anchor is above the growth).
    const grown = _placeDeployColumn(cy, account, deploy, pad.bottom);
    beneath.forEach((n) => n.position({x: n.position("x"), y: n.position("y") + grown}));
    if (beneath.length > 1) {
        alignDistributeVertical(cy, {members: beneath, sort: false, gap: 56});
    }

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

/**
 * Playground exception: stand the deploy-path icons in ONE column, centred on the account's own centre line, below
 * the account's other contents, and grow the account (downward only) to hold them. Order within the column is by
 * label (stable). Returns how far the account's bottom edge moved. Should become a `column` tier of the
 * tiered-rows natural layout in tap_viz, which would size the container itself.
 */
function _placeDeployColumn(cy, account, deploy, bottomPad) {
    if (account.empty() || deploy.empty()) return 0;
    const box = account.boundingBox({includeLabels: false, includeOverlays: false});
    const others = cy.nodes().filter((n) => n.data("_viewport_parent") === account.id() && !n.hasClass(ELEVATION_HIDDEN_CLASS)
        && !deploy.anySame(n));
    const above = others.nonempty() ? others.boundingBox({includeLabels: true, includeOverlays: false}).y2 : box.y1;
    const iconHeight = (n) => Number(n.data("_icon_h")) || n.height();
    const x = account.position("x");
    const ordered = deploy.toArray().sort((a, b) => String(a.data("label")).localeCompare(String(b.data("label"))));
    let y = above + 44;
    let last = y;
    ordered.forEach((n, i) => {
        const half = iconHeight(n) / 2;
        const cyY = i === 0 ? y + half : last + DEPLOY_PITCH;
        n.position({x, y: cyY});
        // One layer above the account, as the nesting would have drawn a child of it.
        n.style({"z-index": Number(account.style("z-index")) + 10});
        n.data("_viewport_parent", account.id());
        last = cyY;
    });
    const newBottom = last + iconHeight(ordered[ordered.length - 1]) / 2 + bottomPad;
    const delta = Math.max(0, newBottom - box.y2);
    if (delta > 0) {
        account.style({height: box.h + delta});
        account.position({x: account.position("x"), y: account.position("y") + delta / 2});
    }
    return delta;
}

function _edgeType(e) {
    return e.data("edge_type") || e.data("label") || "";
}

/**
 * The subnets of one VPC that share a tier (the same `tier` tag) are zone copies of each other; their typed
 * availability zones are what tell the copies apart.
 * Collapse all but the first (by label) and what resides in them before nesting, so the box is sized for
 * one; return the stack options to apply once the scene is positioned.
 */
function _collapseZoneCopies(cy) {
    const byTier = new Map();
    cy.edges().forEach((e) => {
        if (_edgeType(e) !== E.partitioned) return;
        const subnet = e.target();
        const key = e.source().id() + "|" + ((subnet.data("tags") || {}).tier ?? "");
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
 * Stamp the top-level `ranked` columns, left to right. A person or a computer carries its place in the `column`
 * and `row` dimensions (their types have no tagging system); a type that has one (the account, GitHub) carries
 * `layout:column` and `layout:order` tags.
 */
function _stampRootColumns(cy) {
    cy.nodes().forEach((n) => {
        const dims = n.data("dimensions") || {};
        const tags = n.data("tags") || {};
        if (dims.column !== undefined) {
            n.data({_stage: Number(dims.column), _order: Number(dims.row || 0)});
        } else if (tags["layout:column"] !== undefined) {
            n.data({_stage: Number(tags["layout:column"]), _order: Number(tags["layout:order"] || 0)});
        }
    });
}
