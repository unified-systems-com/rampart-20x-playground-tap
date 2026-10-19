/**
 * landing: the nested layout behind the Overview page (req-rampart-20x-playground-govcloud-view).
 *
 * Configuration of the tap_viz runtime and data reads only; no geometry of its own
 * (req-rampart-20x-playground-nongoals). The overview shows the running parts of the system inside the product
 * account: the organization, the other accounts, the ECS cluster and service and the identity provider stay on
 * the grid and are not selected by the page's Searches. Containment comes only from edges aws_core declares:
 *
 *   - boundary ⊃ the account      SCOPED_TO_COMPLIANCE_BOUNDARY (account → boundary; compliance_core declares it)
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
 * Top level, left to right: the customer and their computer, the authorization boundary around the product account,
 * GitHub, the developer's computer and the developer. The administrator and their computer hang under the
 * bottom-centre of the boundary (the account's bottom-centre x), the computer above the person. The line of sight is one horizontal line,
 * left to right: the customer, their computer, the internet gateway, the load balancer, the database, GitHub, the
 * developer's computer and the developer. The load balancer is the anchor: the roots outside the account and the
 * gateway are put on its horizontal line (align-only). The database is already on it (the same VPC column).
 *
 * The people, their computers, the gateway, load balancer, database, Route 53 zone, ECR repository, Lambda,
 * buckets, secrets, pipeline and CodeBuild projects are icon-centric-solo nodes (icon-node.js): the icon and
 * its name, no card. GitHub is an icon node with a card. Icon nodes are terminal, so a computer's local account
 * and GitHub's accounts, repository, workflow, runs and packages are not drawn.
 *
 * Deploy path: the AWS icons of the delivery path (the secret a deploy Lambda retrieves, the ECR repository, the
 * buckets, the pipeline, the Lambda and the CodeBuild projects) stand in ONE tightly packed horizontal row, centred at
 * the bottom-middle of the account under the VPC, and a titled scope box, "Continuous Delivery", marks them as one
 * collection. The row is the tap_viz align-distribute helper with its `label` option (as samsite's Deploy & Bootstrap
 * row); the account is grown to hold it.
 *
 * PLAYGROUND EXCEPTION (standing exception, George 2026-10-19: custom tweaks in the playground's JavaScript layout
 * are permitted while the concepts settle; exit: fold into tap_viz when they do). Each tweak below is marked
 * "playground exception" with the tap_viz runtime form it should become:
 *   1. the account's growth for the row and the choice of its members (a `reserve` option of the nested
 *      layouts, and a nesting-aware member rule: delivery types and the secrets a deploy Lambda retrieves);
 *   2. the gateway on the anchor's line (an `alignTo` of a nested node in the ranked natural layout, so a nested
 *      column can be centre-aligned to an anchor without a post-pass);
 *   3. a person and their computer as a close pair, and the administrator pair under the account (the spacing
 *      option of the align/distribute helpers);
 *   4. waiting for the scene to be shown before the scope box is drawn (a fix in the tap_viz scope-box helper);
 *   6. the boundary's look: transparent, a bold red line, its title above the box (a per-node display override);
 *   5. the boundary growing with the account when the account grows for the row (the same `reserve` option as 1,
 *      applied through the nesting: a parent follows the growth of its child).
 * None changes the Python, the vocabulary or the data rules.
 */

import {projectNested, ELEVATION_HIDDEN_CLASS} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";
import {applyStack, STACK_COLLAPSED_CLASS} from "/static/tap_viz/js/runtime/stack.js";
import {applyIconNodes} from "/static/tap_viz/js/runtime/icon-node.js";
import {alignDistributeHorizontal} from "/static/tap_viz/js/runtime/align-distribute.js";

const T = {
    vpc: "aws_core__aws_vpc",
    subnet: "aws_core__aws_subnet",
    account: "aws_core__aws_account",
    boundary: "compliance_core__compliance_boundary",
    igw: "aws_core__aws_internet_gateway",
    alb: "aws_core__aws_alb",
    rds: "aws_core__aws_rds_instance",
    zone: "aws_core__aws_route53_zone",
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
    scopedTo: "SCOPED_TO_COMPLIANCE_BOUNDARY__compliance_core",
    retrievesSecret: "RETRIEVES_SECRET_FROM__aws_core",
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
const CONTAINERS = [T.boundary, T.account, T.vpc, T.subnet, T.host, T.platform, T.ghAccount, T.repo, T.workflow, T.package];
//: Shown as icon nodes: the type icon is the card, the name is below it.
const ICON_TYPES = [T.platform];
const ICON = {width: 84, height: 84};
//: Shown as icon-centric-solo nodes at the icon-node size (no card): the people and their computers. Same box as
//: the carded icon nodes they were, so nothing moves.
const SOLO_ICON_TYPES = [T.human, T.host];
//: Shown as icon-centric-solo nodes: the icon and the name, no card.
const SOLO_TYPES = [T.igw, T.alb, T.rds, T.zone, T.ecr, T.lambda, T.bucket, T.secret, T.pipeline, T.codebuild];
const SOLO = {width: 72, height: 72};
//: The deploy path inside the account: the AWS icons of the delivery path. A secret is part of it only when a deploy
//: Lambda retrieves it (RETRIEVES_SECRET_FROM): that is the GitHub App token (a secret no deploy node
//: retrieves would not be part of it).
const DEPLOY_TYPES = [T.ecr, T.bucket, T.pipeline, T.lambda, T.codebuild];
const DEPLOY_SECRET_READERS = [T.lambda];
//: The gap between two icons of the deploy row (model units): fairly tight, but wide enough that the names under
//: neighbouring icons (wrapped at 104 units) do not run together.
const DEPLOY_GAP = 28;
//: The title of the scope box around the deploy row.
const DEPLOY_LABEL = "Continuous Delivery";
//: Room the scope box takes around its icons, on all sides: it must contain the names under the icons.
const DEPLOY_BOX_PADDING = 36;
//: Playground exception (should become the spacing option of the tap_viz align/distribute helpers): the gap, in
//: model units, between the boxes of a person and their computer. One constant for all three pairs.
const PAIR_GAP = 28;
//: Playground exception (same exit): the clear gap between the bottom edge of the box that holds the account (the
//: boundary) and the pair that hangs below it.
const BELOW_ACCOUNT_GAP = 56;

//: Playground exception (same exit as _styleBoundary): the boundary's line colour (a true red), its width and how far
//: its title stands above the box.
const BOUNDARY_RED = "#dc2626";
const BOUNDARY_LINE_WIDTH = 4;
const BOUNDARY_LABEL_RISE = 8;

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
    // Playground exception (deploy row room; should become a reserve option of the nested layouts): the deploy icons
    // are out of the nesting while it runs, so the account is sized for its own rows; they are placed in one row below
    // them afterwards, which grows the account.
    const deploy = _deployPath(cy, shown);
    deploy.addClass(ELEVATION_HIDDEN_CLASS);
    _stampVpcColumns(cy);
    _stampRootColumns(cy);

    const result = await projectNested(cy, {
        relationships: [
            {name: "boundary-holds-account", gryphon: `(parent:${T.boundary})<-[:${E.scopedTo}]-(child:${T.account})`},
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
            [T.boundary]: {name: "flow", gap: 12, sort: "label"},
            [T.platform]: {name: "flow", gap: 20, sort: "label"},
            [T.ghAccount]: {name: "flow", gap: 20, sort: "label"},
            [T.repo]: {name: "flow", gap: 12, sort: "label"},
            [T.workflow]: {name: "flow", gap: 12, sort: "label"},
            [T.package]: {name: "flow", gap: 12, sort: "label"},
            //: Inside the account, by row: the DNS zone in the top-left corner, then the VPC. The deploy path is the row
            //: below them. The certificate, the key and the runtime secret are not on the Overview (no `overview` value).
            [T.account]: {
                name: "tiered-rows", rowGap: 44, itemGap: 40,
                tiers: [
                    {name: "dns", entityTypes: [T.zone], align: "start"},
                    {name: "vpc", entityTypes: [T.vpc]},
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
    // path's line. What stands in the product's column besides the boundary around the account (the
    // administrator's computer and the administrator) goes under the boundary instead. The product's column is
    // the column of the account's outermost ancestor, found through the nesting, never by a type.
    if (cy.scratch("landing_row")) cy.scratch("landing_row").destroy();
    const anchor = shown([T.alb]).first();
    const account = shown([T.account]).first();
    const roots = cy.nodes().filter((n) => Number.isInteger(n.data("_stage")) && n.data("_viewport_parent") === undefined
        && !n.hasClass(ELEVATION_HIDDEN_CLASS));
    const productRoot = account.nonempty() ? _outermost(cy, account) : account;
    const productStage = productRoot.nonempty() ? productRoot.data("_stage") : undefined;
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

    // Playground exception (deploy row room): the account grows downward for the row. The line of sight does not
    // move (the anchor is above the growth); what stands beneath the account is placed by _closePairs afterwards.
    if (cy.scratch("landing_deploy")) cy.scratch("landing_deploy").destroy();
    const accountBottom = account.nonempty() ? account.boundingBox({includeLabels: false, includeOverlays: false}).y2 : 0;
    cy.scratch("landing_deploy", _placeDeployRow(cy, account, deploy, pad.bottom));
    _growAncestors(cy, account, accountBottom);
    _closePairs(roots, account, productRoot);

    // An empty container is still a box, not a leaf.
    cy.nodes(CONTAINERS.map((t) => `[entity_type = "${t}"]`).join(", ")).forEach((n) => {
        if (n.data("_is_icon_node")) return;
        if (!cy.nodes().some((c) => c.data("_viewport_parent") === n.id())) n.addClass("tap-viewport-parent");
    });
    placeParentLabels(cy, {
        anchor: "upper-left", inset: 16,
        parentFontSize: chrome.parentFontSize, parentFontWeight: chrome.parentFontWeight,
    });
    _styleBoundary(cy, shown([T.boundary]));
    if (trigger_reason === "initial_load") cy.fit(cy.nodes(":visible"), 40);
    return {warnings: result.warnings || []};
}

/**
 * The outermost node of the nesting that holds `node`: itself when nothing holds it.
 */
function _outermost(cy, node) {
    let top = node;
    for (let parent = cy.getElementById(top.data("_viewport_parent") || ""); parent.nonempty();
         parent = cy.getElementById(top.data("_viewport_parent") || "")) {
        top = parent;
    }
    return top;
}

/**
 * Playground exception (should become the same `reserve` option as the account's growth, applied through the
 * nesting so a parent follows its child): when the account has grown downward for the deploy row, the boxes that hold
 * it (the boundary) grow by the same amount, keeping their top edge.
 */
function _growAncestors(cy, node, oldBottom) {
    const delta = node.boundingBox({includeLabels: false, includeOverlays: false}).y2 - oldBottom;
    if (!(delta > 0)) return;
    for (let parent = cy.getElementById(node.data("_viewport_parent") || ""); parent.nonempty();
         parent = cy.getElementById(parent.data("_viewport_parent") || "")) {
        parent.style({height: parent.height() + delta});
        parent.position({x: parent.position("x"), y: parent.position("y") + delta / 2});
    }
}

/**
 * Playground exception (should become a per-node display override on the entity, or a `display` hint a plugin's
 * default display can be given per instance in tap_viz; compliance_core's default for the type stays as it is, as
 * other instances share it): the authorization boundary is drawn as a transparent box with a bold true-red line,
 * and its title stands outside the box, above its top edge, centred. Applied after placeParentLabels, which anchors
 * every container's label inside the box.
 */
function _styleBoundary(cy, boundary) {
    boundary.forEach((n) => {
        n.style({
            "background-opacity": 0,
            "border-width": BOUNDARY_LINE_WIDTH,
            "border-color": BOUNDARY_RED,
            "border-opacity": 1,
            "color": BOUNDARY_RED,
            "text-valign": "top", "text-halign": "center",
            "text-margin-x": 0, "text-margin-y": -BOUNDARY_LABEL_RISE,
            "text-wrap": "none", "text-max-width": `${n.width()}px`,
        });
    });
}

function _whenShown(cy, draw, tries = 600) {
    const container = cy.container();
    if (!container || container.style.visibility !== "hidden" || tries <= 0) {
        draw();
        return;
    }
    requestAnimationFrame(() => _whenShown(cy, draw, tries - 1));
}

/**
 * Stand the deploy-path icons in one row, left to right, DEPLOY_GAP apart (the tap_viz align-distribute helper, with
 * its `label` option drawing the titled scope box), the row centred on the account's centre line below the account's
 * other contents. Playground exception: the account grows downward to hold the row, and the members and their order
 * are chosen here: the `layout:order` tag when a node has one, then label (a stable key, never a place). The edges
 * between two icons of the row are hidden (they would run along and under the icons); edges that leave it stay.
 * Returns a handle whose destroy() removes the row's box and restores those edges.
 */
function _placeDeployRow(cy, account, deploy, bottomPad) {
    const restore = () => cy.edges().filter((e) => e.data("_row_internal")).forEach((e) => {
        e.removeData("_row_internal");
        e.removeStyle("display");
    });
    restore();
    if (account.empty() || deploy.empty()) return {destroy: restore};
    const box = account.boundingBox({includeLabels: false, includeOverlays: false});
    const others = cy.nodes().filter((n) => n.data("_viewport_parent") === account.id() && !n.hasClass(ELEVATION_HIDDEN_CLASS)
        && !deploy.anySame(n));
    const above = others.nonempty() ? others.boundingBox({includeLabels: true, includeOverlays: false}).y2 : box.y1;
    const iconHeight = (n) => Number(n.data("_icon_h")) || n.height();
    const tagOrder = (n) => Number((n.data("tags") || {})["layout:order"]);
    const ordered = deploy.toArray().sort((a, b) => {
        const ta = tagOrder(a), tb = tagOrder(b);
        if (Number.isFinite(ta) && Number.isFinite(tb) && ta !== tb) return ta - tb;
        return String(a.data("label")).localeCompare(String(b.data("label")));
    });
    const half = iconHeight(ordered[0]) / 2;
    // The scope box starts DEPLOY_BOX_PADDING above the icons; keep it clear of what is above.
    const y = above + 44 + DEPLOY_BOX_PADDING + half;
    const baseZ = Number(account.style("z-index")) + 10;
    ordered.forEach((n) => {
        n.style({"z-index": baseZ});
        n.data("_viewport_parent", account.id());
    });
    const row = {members: ordered, anchor: {x: account.position("x"), y}, anchorMode: "center", gap: DEPLOY_GAP, sort: false};
    alignDistributeHorizontal(cy, row);
    let handle = {destroy: () => {}}, destroyed = false;
    // Playground exception: the scope box tracks its members' bounds, and cytoscape recurses computing them while the
    // projection is still revealing the scene (the graph element is hidden). Draw the box once the scene is shown.
    // Should become a fix in the tap_viz scope-box helper (observed 2026-10-19), after which this wait goes.
    _whenShown(cy, () => {
        if (!destroyed) handle = alignDistributeHorizontal(cy, {...row, label: DEPLOY_LABEL, style: {padding: DEPLOY_BOX_PADDING}});
    });
    cy.edges().filter((e) => deploy.anySame(e.source()) && deploy.anySame(e.target())).forEach((e) => {
        e.data("_row_internal", true);
        e.style("display", "none");
    });
    // Bottom of the box: the icons, the room for their names, then the account's own bottom padding.
    const newBottom = y + half + DEPLOY_BOX_PADDING + bottomPad;
    const delta = Math.max(0, newBottom - box.y2);
    if (delta > 0) {
        account.style({height: box.h + delta});
        account.position({x: account.position("x"), y: account.position("y") + delta / 2});
    }
    return {destroy: () => {
        destroyed = true;
        handle.destroy();
        restore();
    }};
}

/**
 * Playground exception (should become the spacing option of the tap_viz align/distribute helpers): a person and
 * their computer stand close together, PAIR_GAP apart, and the computer is the one that moves, toward its person
 * and so away from the account. The pair is read from the data: the `actor` dimension of a person and the `device`
 * dimension of a computer carry the same value (`customer`, `developer`, `administrator`). Two that stand in the
 * same column (the administrator's, beneath the account) are a vertical pair, the computer above the person; the
 * pair hangs under the bottom-centre of the box that holds the account. Otherwise the pair is horizontal and the computer moves along the
 * line toward the person.
 */
function _closePairs(roots, account, productRoot) {
    const dim = (n, key) => (n.data("dimensions") || {})[key];
    const people = roots.filter((n) => n.data("entity_type") === T.human && dim(n, "actor") !== undefined);
    const computers = roots.filter((n) => n.data("entity_type") === T.host && dim(n, "device") !== undefined);
    people.forEach((person) => {
        computers.filter((c) => dim(c, "device") === dim(person, "actor")).forEach((computer) => {
            if (person.data("_stage") === computer.data("_stage")) {
                // Hangs under the bottom-centre of the box that holds the account (the boundary), which is the
                // account's bottom-centre x: the computer first, the person below it.
                const x = account.position("x");
                const bottom = productRoot.boundingBox({includeLabels: false, includeOverlays: false}).y2;
                const y = bottom + BELOW_ACCOUNT_GAP + computer.height() / 2;
                computer.position({x, y});
                person.position({x, y: y + (person.height() + computer.height()) / 2 + PAIR_GAP});
            } else {
                const toward = Math.sign(account.position("x") - person.position("x"));
                computer.position({y: computer.position("y"),
                    x: person.position("x") + toward * ((person.width() + computer.width()) / 2 + PAIR_GAP)});
            }
        });
    });
}

/**
 * The deploy-path icons: the delivery types, plus every secret a deploy node retrieves (an edge, not a name).
 */
function _deployPath(cy, shown) {
    const readers = shown(DEPLOY_SECRET_READERS);
    const secrets = shown([T.secret]).filter((secret) => cy.edges().some((e) => _edgeType(e) === E.retrievesSecret
        && e.target().same(secret) && readers.anySame(e.source())));
    return shown(DEPLOY_TYPES).union(secrets);
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
 * and `row` dimensions (their types have no tagging system); a type that has one (GitHub) carries
 * `layout:column` and `layout:order` tags. The boundary around the account is a compliance_core type with no tagging
 * system, so it carries `column` and `row` dimensions like a person.
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
