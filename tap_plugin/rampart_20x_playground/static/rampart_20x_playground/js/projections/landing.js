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
 * left to right: the customer, their computer, the internet gateway, the load balancer, the database. The load balancer is the anchor: the roots
 * outside the account and the gateway are put on its horizontal line (align-only). The database is already on it (the same VPC column).
 * GitHub, the developer's computer and the developer are NOT on it: they stand, in that order after the boundary, on the delivery line
 * through the Continuous Delivery pile (exception 29).
 *
 * The people, their computers, the gateway, load balancer, database, Route 53 zone, ECR repository, Lambda,
 * buckets, secrets, pipeline and CodeBuild projects are icon-centric-solo nodes (icon-node.js): the icon and
 * its name, no card. GitHub is an icon node with a card. Icon nodes are terminal, so a computer's local account
 * and GitHub's accounts, repository, workflow, runs and packages are not drawn.
 *
 * Deploy path: the AWS icons of the delivery path (the secret a deploy Lambda retrieves, the ECR repository, the
 * buckets, the pipeline, the Lambda and the CodeBuild projects) are half size and stand as ONE card pile at the bottom-right of the
 * account under the VPC, and a titled scope box, "Continuous Delivery", marks them as one collection (exception 28); the account
 * is grown to hold it.
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
 *   7. the application flow's click window (Wave 7): a node-tap handler on the flow node, reading the node's own name,
 *      description and `dataclass.*` dimensions (no network call), drawn with the tap_viz info window's CSS classes
 *      (should become a projection-declared `node_info` window of tap_viz, a sibling of the status-badge info window,
 *      bound to a node type; the host-body tap is reserved for projections by req-viz-panel-click-semantics);
 *   8. the application flow's place and look: a solo icon (the circle) at half the standard icon size, centred in the gap between the
 *      customer's computer and the boundary, on the line of sight (a `rankedPlacement` centring of a root column and
 *      a per-type `shape` and size hint of the type's default display);
 *   9. the edge lift (`lift-edge.js`, a `lift_edge` section of the runtime) and the two elevations of the account:
 *      at the account elevation the task's interior is hidden and the flow's edge is lifted onto the task; past the
 *      reveal zoom the interior is shown and the lift is destroyed (the second Elevation of the projection);
 *  10. the interior's relative scale: the interior of the task is laid out and labelled at 1/ELEVATION_ZOOM_RATIO of the
 *      account's sizes, so its text is as large on screen at the reveal zoom as the account's text is at the account
 *      zoom, and the task box never changes size (a per-elevation label and size scale of the Elevation definition);
 *  11. tap-web and gunicorn as siblings in the container: a derived containment (`_deriveInterior`, should become a
 *      `flatten` option of a projectNested relationship), ordered by the `column` dimension.
 *  19. the text base size: every label is FONT_SCALE (2) times the runtime's base font, so the settle mode's constant on-screen
 *      size is twice as large (`_scaleFont`; should become a `font_scale` option of the zoom_settle config, or a larger
 *      `normal` label-size tier in tap_viz's label sizing);
 *  20. the data-flow arrowhead at FLOW_ARROW_SCALE (2) times the base arrow (should become a per-edge-type arrow-scale display hint);
 *  21. the web task's own label at the two elevations: centred in the box at the account elevation, upper-left once the interior
 *      is shown (`_placeTaskLabel`; should become a per-elevation label anchor of the Elevation definition);
 *  22. the subnets' labels inside the box, top-centre (should become a `label_position: inside` of the subnet's display hint, overriding the
 *      aws_core default of an outside label, applied here as a data override before placeParentLabels);
 *  23. the badges (the open-findings bubble and the type badges) follow the zoom_settle `icon` class (`_followIconPolicy`;
 *      should become a `badge` class of zoom_settle, which sizes the status and type badges as it sizes the icon cards).
 *  24. the solo icons carry no border: a bypass `border-width: 0` after applyIconNodes (`_noBorder`), because the settle mode can read the
 *      stylesheet's border (the `node[fill_color]` rule's 2 px) before the solo rule applies, write it scaled as a bypass, and so
 *      override the solo rule for good (should become: zoom_settle skips a node whose `_icon_solo` is set, or applyIconNodes writing
 *      `border-width: 0` itself for a solo node);
 *  25. the label of a person and of their computer in a horizontal pair is PAIR_FONT_FACTOR of the usual size, so the two names do not touch
 *      (`_closePairs` marks them and `_scaleFont` reads the mark; should become a per-node `label_scale` display hint).
 *  26. the database's two forms: at the account elevation the RDS instance is a solo icon; past the reveal zoom it becomes a standard
 *      box (the type icon as a badge at its top-right, its name upper-left) with the PostgreSQL program drawn inside, laid out
 *      once at the box's size and restyled on the elevation change (should become a per-elevation `form` of a node type in the
 *      Elevation definition: `icon-solo` at one elevation, `standard` at the next, its interior shown with it; and a
 *      `badge_corner` option of the badge nodes);
 *  27. the other application flows: a flow that carries no `column` dimension is not in the nesting (a flow cannot nest in an
 *      account or a subnet), so it is hidden while the nesting runs and stood afterwards in the gap between the two boxes its
 *      lines end on, on the line that joins their centres (`_placeFlows`; should become a `place: between-endpoints` option of
 *      the nested layouts, which centres an edge-defined node in the gap between the siblings of the lowest common ancestor).
 *  28. the delivery pile: the Continuous Delivery icons are half size and stand as a card pile (each icon offset down and right of the
 *      one behind it, in `layout:order` from the back to the front) at the bottom-right of the account, with the titled scope box around
 *      the pile; only the front icon keeps its name (`_placeDeployPile`; should become a `pile` arrangement of the align/distribute
 *      helpers, a `corner: bottom-right` of the nested layouts' reserved row, and a `label_scope: front` of the pile);
 *  29. the delivery line: the nodes that carry `line: delivery` (the `layout:line` tag on a node type that has tags) leave the line of sight
 *      and are put on the horizontal line through the pile, in their own column order (`_onDeliveryLine`; should become an
 *      `align-to-line` of a named group in the ranked natural layout of the roots).
 *  30. a slotted VPC: a VPC that carries `place: bottom-center` is not in the account's rows (it would stand beside the production VPC).
 *      It is hidden with its subnets and what resides in them while the nesting runs, then drawn by hand (`_placeSlotted`) at the
 *      centre of the account's bottom row, in the same row as the delivery pile: the VPC holds its subnet and the subnet its solo-icon instance, sized
 *      from the same paddings, the account grown to hold the row (should become a `slot: bottom-center` of the nested layouts' tiered rows, a tier
 *      chosen by a dimension and not only by entity type).
 *  31. a node's name hidden: the nodes that carry the dimension `label: hidden` (the Route 53 zone, the source-puller Lambda, the teleport EC2 instance;
 *      the internet gateway, the load balancer and the database carried it until exception 47) draw no name (`_hideLabels`; should become a `label: hidden` display hint of
 *      a node, applied per instance, with the revealed form of a node type free to show it again);
 *  32. a node's logo: a node that carries the dimension `icon: <app>/icons/<key>.svg` shows that static icon (the Teleport logo on the teleport
 *      EC2 instance) in a bordered card like GitHub's, instead of its type's icon (`_logoNodes`; should become the instance-level icon override
 *      `req-grid-icon-instance`, served as the node's `icon_url`, and a `card` form chosen by the display hint of the node);
 *  33. the subnets' names are subtle: SUBNET_LABEL_FACTOR of the usual size and a normal weight (should become a `label_scale` and
 *      `label_weight` of the subnet's display hint, the same hint as 25 and 22);
 *  34. the scope box's title at the size of the container titles: the HTML title of tap_viz's scope box is a fixed 11 px of the model, so it is
 *      resized on each zoom to the size the settle mode gives a container title (`_syncScopeTitle`; should become a `label_size` option of
 *      the scope-box helper that follows the zoom_settle font class);
 *  35. (superseded by 38; should become the per-node `icon_angle` hint) a reversed flow: the `arrow: reversed` dimension is gone; the direction of
 *      every flow is its `icon_angle`.
 *  36. the database's program on the line of sight at the revealed elevation: the PostgreSQL program is moved up inside the standard box, so
 *      its centre is on the same horizontal line as gunicorn (`_alignDatabaseProgram`; should become an `align` of a nested member to the
 *      anchor's line, as 17, with a title row that does not push a member down);
 *  37. GitHub a little further right: the first node on the delivery line is moved right by GITHUB_SHIFT, so the source-pull arrow has room
 *      (`_shiftGithub`; should become a `gap-before` of a named group in the ranked natural layout of the roots).
 *  38. a flow's direction: the dimension `icon_angle` of an application flow (degrees; 0 = north / up, 90 = east, 180 = south, 270 = west;
 *      default 90) turns the flow's circle icon (the icon's own arrow points east at 90, so the icon file is rewrapped in a rotation) and puts
 *      NOTHING else (the arrowhead is always on the destination end, whatever the angle: arrows point from the session initiator to the
 *      target, and the icon marks the way the data moves) (`_flowAngle`, `_rotateFlowIcons`, `_styleFlowEdges`;
 *      should become a per-node `icon_angle` display hint of the application-flow type, which the node's icon and its edge types'
 *      arrow shape both read).
 *  39. the interior programs' names inside their boxes: centred in the box, wrapped to the box's width, FLOW_FONT_FACTOR-like smaller
 *      (`_labelProgramsInside`; should become a `label_position: inside` display hint of the program type's revealed form, with a
 *      `label_scale`, the same hints as 22 and 33).
 *  40. the flows' names are FLOW_FONT_FACTOR of the usual size (`_scaleFont` reads the mark; should become a `label_scale` display hint of the
 *      application-flow type, the hint of 25 and 33).
 *  41. the database's revealed box title: top-centre and DB_TITLE_FACTOR of the usual size (should become a `label_position: top-center` and a
 *      `label_scale` of the standard form of the RDS type, the hints of 22 and 33, in the Elevation definition of 26).
 *  42. a node's icon drawn as its own card: the nodes with `icon_form: solo` beside an `icon` dimension (the internet gateway, as the load
 *      balancer's purple card with a white glyph) keep the solo form with that icon, not the bordered logo card of 32 (`_logoNodes`; same exit as 32,
 *      the instance-level icon override, whose form is chosen by the display hint of the node).
 *  43. the Admin Access VPC snug around its subnet: SLOT_PADDING is the room on all sides of the slotted VPC (exception 30; same exit).
 *  44. the Admin Access VPC and its logo card are compact: the logo card (exception 32) is drawn at DEPLOY_SCALE of the solo icon size, like the
 *      Continuous Delivery icons, its name is hidden by `label: hidden` (exception 31), and the slotted subnet and VPC shrink to it
 *      (SLOT_SUBNET_WIDTH, SLOT_NAMELESS_BOTTOM; exceptions 30 and 43, same exit as 32 for the size, 31 for the name, 30 for the boxes).
 *  45. overview nits, round four: the VPCs' titles are VPC_TITLE_FACTOR of the usual size (`_scaleFont` reads the factor; should become a
 *      `label_scale` display hint of the VPC type, the hint of 25 and 33); the account hugs the delivery pile and the slotted VPC when the
 *      front icon's name is hidden (PILE_NAMELESS_ROOM; same exit as 28); the scope box's title has no background (same exit as 34);
 *      a flow's name is one line (`text-wrap: none` in `_styleFlow`; same exit as 40, a `label_wrap` of the display hint).
 *  46. overview nits, round five: the Route 53 zone is DEPLOY_SCALE of the solo icon size, the scope box's title and the boundary's title are the
 *      VPC titles' size (VPC_TITLE_FACTOR), and the account's and the VPCs' titles are TITLE_DARKEN of their own border colour (`_colourTitles`; should
 *      become a `label_color` of the container type's display hint; the sizes, the same `label_scale` hint as 45, the icon the same size hint as 44).
 *  47. the internet gateway, the load balancer and the database show their names again, directly below their icons, at SUBNET_LABEL_FACTOR of the
 *      usual size and a normal weight (`NAMED_ICON_TYPES`; should become a `label_scale` and `label_weight` display hint of the node type, the hints of 33;
 *      the revealed database box keeps its own title of exception 41).
 *  48. the operating system inside the container, overview nits round six: the container is drawn as container > operating system > [gunicorn, tap-web],
 *      the OS a box of its own (`_deriveInterior`, `_styleOs`; should become a multi-edge `via` path of a projectNested relationship, the
 *      `flatten` option of 11, and a per-node display override for the box's colours). The OS is the one the container's image runs (RUNS_IMAGE,
 *      then RUNS_OPERATING_SYSTEM); the programs it holds are the ones the container runs (RUNS_PROGRAM, directly or through another program).
 *      No official edge says "this OS holds this program": the containment is derived from the container they share and never written to the grid.
 *  49. the libraries and the packages inside the container as two piles with their true counts (`_collapseInteriorPiles`, `INTERIOR_PILES`; should become
 *      the `pile` arrangement of 28 with a count chip in the nested layouts, a `via` path as in 48, and an `exclude_types` of the badge nodes
 *      that is per elevation). Each pile is tap_viz's own stack (applyStack): the face card, two cards behind it and a chip with the count of all of
 *      them; the libraries are the ones the container's programs load (LOADS_LIBRARY), the packages the ones its image has installed
 *      (INSTALLS_PACKAGE). The image host is on the grid only to join them and is never drawn. They show only at the revealed elevation (their cards and
 *      chips are hidden by style with the interior, because the elevation class on them re-enters the stack's position handler).
 * None changes the Python, the vocabulary or the data rules.
 *
 * Running parts (Wave 3): an ECS task holds its container (RUNS_CONTAINER), the container runs gunicorn and gunicorn
 * runs the tap-web program (RUNS_PROGRAM). The task is drawn as task > container > [tap-web, gunicorn]: tap-web (left,
 * by its `column` dimension) and gunicorn (right) are SIBLINGS in the container, and gunicorn -> tap-web is drawn as the
 * arrow between them. The nesting is DATA in the `relationships` below (never a type test in code). The application
 * flow is a circle on the line of sight between the customer's computer and the account; APPLICATION_FLOW_SOURCE and
 * APPLICATION_FLOW_DESTINATION are its two lines. At the account elevation the destination line ends on the task (the
 * lift), past the reveal zoom it ends on the tap-web program.
 */

import {projectNested, ELEVATION_HIDDEN_CLASS, VIEWPORT_PARENT_CLASS, HIDDEN_CONTAINMENT_CLASS} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";
import {applyStack, STACK_COLLAPSED_CLASS} from "/static/tap_viz/js/runtime/stack.js";
import {applyIconNodes} from "/static/tap_viz/js/runtime/icon-node.js";
import {closeInfoWindow} from "/static/tap_viz/js/runtime/info-window.js";
import {applyBadgeNodes} from "/static/tap_viz/js/runtime/badge-nodes.js";
import {liftEdge, containedNodes, LIFTED_EDGE_CLASS} from "/static/rampart_20x_playground/js/projections/lift-edge.js";
import {alignDistributeHorizontal} from "/static/tap_viz/js/runtime/align-distribute.js";
import {applyScopeBoxes} from "/static/tap_viz/js/runtime/layout-scope-boxes.js";
import {normalizeSettleConfig, modelFactor} from "/static/tap_viz/js/runtime/zoom-settle.js";

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
    ec2: "aws_core__aws_ec2_instance",
    task: "aws_core__aws_ecs_task",
    ecsContainer: "aws_core__aws_ecs_container",
    program: "computing_core__program",
    os: "computing_core__operating_system",
    pkg: "computing_core__package",
    lib: "computing_core__library",
    flow: "computing_core__application_flow",
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
    runsContainer: "RUNS_CONTAINER__aws_core",
    runsProgram: "RUNS_PROGRAM__computing_core",
    runsImage: "RUNS_IMAGE__computing_core",
    runsOs: "RUNS_OPERATING_SYSTEM__computing_core",
    installsPackage: "INSTALLS_PACKAGE__computing_core",
    loadsLibrary: "LOADS_LIBRARY__computing_core",
    //: Derived by `_deriveInterior`, never in the grid (playground exception 48): for the nesting only.
    containsOs: "CONTAINS_OS__playground",
    osRunsProgram: "OS_RUNS_PROGRAM__playground",
    containsLibrary: "CONTAINS_LIBRARY__playground",
    containsPackage: "CONTAINS_PACKAGE__playground",
    flowSource: "APPLICATION_FLOW_SOURCE__computing_core",
    flowDestination: "APPLICATION_FLOW_DESTINATION__computing_core",
};
const CONTAINERS = [T.boundary, T.account, T.vpc, T.subnet, T.task, T.ecsContainer, T.os, T.host, T.platform, T.ghAccount, T.repo, T.workflow, T.package];
//: Shown as icon nodes: the type icon is the card, the name is below it.
const ICON_TYPES = [T.platform];
const ICON = {width: 84, height: 84};
//: Shown as icon-centric-solo nodes at the icon-node size (no card): the people and their computers. Same box as
//: the carded icon nodes they were, so nothing moves.
const SOLO_ICON_TYPES = [T.human, T.host];
//: Shown as icon-centric-solo nodes: the icon and the name, no card.
const SOLO_TYPES = [T.igw, T.alb, T.ec2, T.zone, T.ecr, T.lambda, T.bucket, T.secret, T.pipeline, T.codebuild];
const SOLO = {width: 72, height: 72};
//: The deploy path inside the account: the AWS icons of the delivery path. A secret is part of it only when a deploy
//: Lambda retrieves it (RETRIEVES_SECRET_FROM): that is the GitHub App token (a secret no deploy node
//: retrieves would not be part of it).
const DEPLOY_TYPES = [T.ecr, T.bucket, T.pipeline, T.lambda, T.codebuild];
const DEPLOY_SECRET_READERS = [T.lambda];
//: Playground exception 28: the deploy icons are DEPLOY_SCALE of the solo icon size, and stand as a pile: each is offset PILE_STEP (model
//: units) right and down of the one behind it.
const DEPLOY_SCALE = 0.5;
const PILE_STEP = 22;
//: The title of the scope box around the deploy pile.
const DEPLOY_LABEL = "Continuous Delivery";
//: Room the scope box takes around its icons, on all sides.
const DEPLOY_BOX_PADDING = 28;
//: Room under the pile for the front icon's name (model units), inside the account.
const PILE_NAME_ROOM = 90;
//: Playground exception 45: the room under a front icon whose name is hidden (`label: hidden`), so the account hugs the pile.
const PILE_NAMELESS_ROOM = 0;
//: Playground exceptions 31, 32 and 42: the dimensions that hide a node's name, give a node an icon of its own and say that icon is a whole card, and their values.
const LABEL_KEY = "label";
const LABEL_HIDDEN = "hidden";
const ICON_KEY = "icon";
const ICON_PATH = /^[a-z0-9_]+\/icons\/[a-z0-9-]+\.svg$/;
const ICON_FORM_KEY = "icon_form";
const ICON_FORM_SOLO = "solo";
//: Playground exception 38: the dimension that says which way a flow points (degrees, 0 = north, 90 = east, 180 = south, 270 = west), the
//: direction the flow's icon file already points, and the direction a flow without one points.
const ICON_ANGLE_KEY = "icon_angle";
const FLOW_ICON_ANGLE = 90;
//: Playground exception 40: the size of a flow's name, as a share of the usual one.
const FLOW_FONT_FACTOR = 0.7;
//: Playground exception 39: a program's name inside its box takes this share of the box's width, at PROGRAM_FONT_FACTOR of the usual size.
const PROGRAM_LABEL_FIT = 0.92;
const PROGRAM_FONT_FACTOR = 0.8;
//: Playground exception 41: the revealed database box's title size, as a share of the usual one.
const DB_TITLE_FACTOR = 0.6;
//: Playground exception 33: the subnets' name size, as a share of the usual one, and its weight.
const SUBNET_LABEL_FACTOR = 0.6;
const SUBNET_LABEL_WEIGHT = "normal";
//: Playground exception 47: the solo icons that show a subtle name directly below them at the account elevation.
const NAMED_ICON_TYPES = [T.igw, T.alb, T.rds];
//: Playground exception 45: the VPCs' title size, as a share of the usual (account) one: between the subnets' (SUBNET_LABEL_FACTOR) and the account's.
const VPC_TITLE_FACTOR = 0.8;
//: Playground exception 37: how far right, in model units, the first node of the delivery line (GitHub) moves.
const GITHUB_SHIFT = 70;
//: Playground exception 29: the dimension (and the tag, on a node type that has a tagging system) that puts a node on the delivery line, and
//: its value.
const LINE_KEY = "line";
const LINE_TAG = "layout:line";
const LINE_DELIVERY = "delivery";
//: Playground exception 30: the dimension that gives a VPC a slot of its own, and the slot.
const PLACE_KEY = "place";
const PLACE_BOTTOM_CENTER = "bottom-center";
//: Playground exceptions 30 and 43: the room, in model units, between a slotted VPC's edge and the subnet it holds, on every side.
const SLOT_PADDING = 12;
//: Playground exception 43: the room above the subnet, so the VPC's type badge (at its corner) and the subnet's (at its own) do not overlap.
const SLOT_TOP = 28;
//: Playground exception 44: the slotted subnet's least width (it holds one small icon; its title is short), and the room under a resident
//: whose name is hidden (`label: hidden`; a resident with a name keeps the usual top and bottom room), so the boxes are snug around the small icon.
const SLOT_SUBNET_WIDTH = 120;
const SLOT_SUBNET_TOP = 56;
const SLOT_NAMELESS_BOTTOM = 10;
//: Playground exception (should become the spacing option of the tap_viz align/distribute helpers): the gap, in
//: model units, between the boxes of a person and their computer. One constant for all three pairs.
const PAIR_GAP = 28;
//: Playground exception 25 (same exit): the label size of a person and of their computer in a horizontal pair, as a share of the usual
//: one. The names are wider than the icon at twice the base font, and the two touch across PAIR_GAP.
const PAIR_FONT_FACTOR = 0.65;
//: Playground exception (same exit): the clear gap between the bottom edge of the box that holds the account (the
//: boundary) and the pair that hangs below it. Wide enough for the administration flow's circle and its name in between.
const BELOW_ACCOUNT_GAP = 220;
//: Playground exception (same exit): the extra room between the administrator pair's computer and person for the computer's two-line name.
const PAIR_NAME_ROOM = 30;
//: Playground exception 26: the box of the database when it is a standard node (model units at the account scale): the layout reserves
//: it, the solo icon (SOLO) stands at its centre at the account elevation. The interior program is laid out at INTERIOR_SCALE inside it.
const RDS_BOX = {width: 200, height: 120};
//: Playground exception 26: the box's fill when it is a standard node, a light blue so the program inside stands out, and its border.
const RDS_FILL = "#BFD4F2";
const RDS_BORDER = "#2E5C99";
const RDS_LABEL = "#0F2A4F";
//: Playground exception 27: the horizontal gap between two columns of the VPC. Wide enough for a flow's circle between the private
//: and the database tier (the circle is half an icon; its name stands above it).
const VPC_COLUMN_GAP = 130;

//: Playground exception (same exit as _styleBoundary): the boundary's line colour (a true red), its width and how far
//: its title stands above the box.
const BOUNDARY_RED = "#dc2626";
const BOUNDARY_LINE_WIDTH = 4;
const BOUNDARY_LABEL_RISE = 8;

//: Playground exception 8 (same exit): the application flow is a solo icon node (its type icon is the circle) at HALF the
//: standard icon size (ICON), in the dark blue of a river of data, its name above it; its two lines are thick and the same
//: blue, the source line without an arrowhead (a per-edge-type display hint of tap_viz: width, colour, arrow shape).
const FLOW_SCALE = 0.5;
const FLOW_BLUE = "#0B3D91";
const FLOW_EDGE_WIDTH = 5;
const FLOW_LABEL_GAP = 4;
//: Playground exception 20 (should become a per-edge-type arrow-scale display hint): the data-flow arrowhead is twice the base
//: arrow. The zoom_settle `arrow` class then holds that on screen.
//: Ruled 2026-10-20 (George: far too big, at most half): 1, half of the 2 it was.
const FLOW_ARROW_SCALE = 1;
//: Playground exception 19 (should become a `font_scale` option of the zoom_settle config, or a larger `normal` label tier): the
//: factor on the runtime's base font of every label. zoom_settle writes base * clamp(z^a) / z from each element's own base, so
//: doubling the base doubles the on-screen text at every zoom (its exponent is 0, so its band never cancels it).
const FONT_SCALE = 2;
//: The font size, in px, the panel's stylesheet gives a node (panel-graph.js, `node`: 11px). The settle mode starts from it, because the
//: standard chrome's 14px and 15px do not survive the projection's later stylesheet pass; the doubled size is written over it.
const BASE_FONT = 11;
//: Playground exceptions 9 and 10 (should become the second Elevation of the projection and its per-elevation scale).
//: The projection has two elevations: the account (the initial one) and the interior, which the zoom watcher activates at
//: ELEVATION_REVEAL_ZOOM (the `zoom` of the second elevation in pages.grift.json, pinned by a test). The reveal zoom is
//: ELEVATION_ZOOM_RATIO times the zoom the account is fitted to at load (about 0.6 at the demo size), so the interior,
//: drawn at INTERIOR_SCALE of the account's sizes, reads as large on screen as the account does.
const ELEVATION_REVEAL_ZOOM = 1.2;
//: Playground exception 9 switch: true reveals the task's interior past ELEVATION_REVEAL_ZOOM and lifts the flow back onto
//: the tap-web program; false would keep the account elevation at every zoom. The deploy row's scope box used to overflow the
//: stack on the way back out; tap_viz fixed that (tap#1077), and it is checked at 2.0 / 0.6 / 1.3 with no console errors.
const REVEAL_ON_ZOOM = true;
//: Playground exception 12 (should become a `badge_size` option of the projection's node_style): the type badges keep one
//: size, in model units. The runtime derives it from the smallest host drawn (0.35 of its shorter side, 24 at least), and
//: hiding the small interior made it 31 and more.
const BADGE_SIZE = 24;
//: Playground exception 17: room, in model units, added above the task's contents. The container is moved up onto the line of
//: sight (_alignInteriorToLine), and without this it would stand against the task's title and its type badge.
const TASK_TOP_ROOM = 36;
//: Playground exception 15: how long the interior fades in and out (milliseconds).
const FADE_MS = 450;
const ELEVATION_ZOOM_RATIO = 2;
const INTERIOR_SCALE = 1 / ELEVATION_ZOOM_RATIO;
//: The `lift_edge` section: containment-style relationships (the shape of projectNested's), saying what the task holds,
//: so an edge that ends inside it is lifted onto it while the interior is hidden.
const LIFT_EDGE = [
    {name: "task-holds-container", gryphon: `(parent:${T.task})-[:${E.runsContainer}]->(child:${T.ecsContainer})`},
    {name: "container-holds-os", gryphon: `(parent:${T.ecsContainer})-[:${E.containsOs}]->(child:${T.os})`},
    {name: "os-holds-program", gryphon: `(parent:${T.os})-[:${E.osRunsProgram}]->(child:${T.program})`},
    {name: "container-holds-library", gryphon: `(parent:${T.ecsContainer})-[:${E.containsLibrary}]->(child:${T.lib})`},
    {name: "container-holds-package", gryphon: `(parent:${T.ecsContainer})-[:${E.containsPackage}]->(child:${T.pkg})`},
    {name: "database-holds-program", gryphon: `(parent:${T.rds})-[:${E.runsProgram}]->(child:${T.program})`},
];
//: Playground exceptions 11 and 48: the derived containment edges (never in the grid) the interior's nesting reads.
const DERIVED_TYPES = [E.containsOs, E.osRunsProgram, E.containsLibrary, E.containsPackage];
//: Playground exception 49: the interior piles. The title of each pile by the derived edge that holds its members, the prefix of a pile's
//: stack id (the elevation watcher finds the pile's cards and count chip by it), the offset (model units, interior scale) between its
//: cards and how many layers it shows. The chip carries the true count.
const INTERIOR_PILES = {[E.containsLibrary]: "Libraries", [E.containsPackage]: "Packages"};
const INTERIOR_STACK_PREFIX = "interior:";
const INTERIOR_PILE_STEP = 4;
const INTERIOR_PILE_DEPTH = 3;
//: Playground exception 49: the gap between the two piles (model units, interior scale), wide enough for the line of sight to pass between them.
const PILE_GAP = 40;
//: Playground exception 48: the operating-system box inside the container: its fill, border and title colour.
const OS_FILL = "#DCE6F2";
const OS_BORDER = "#5B7DB1";
const OS_LABEL = "#1E3A5F";
//: The application flow's click window: the dimensions it lists (a key prefix), its width, and its class name (the
//: tap_viz info window's own, so it looks like it).
const FLOW_DIMENSION_PREFIX = "dataclass.";
const FLOW_WINDOW_WIDTH = 320;
const FLOW_WINDOW_OFFSET = 12;
const FLOW_WINDOW_CLASS = "tap-info-window";

const LEAF = {width: 200, height: 54};
const SUBNET = {width: 230, height: 90};
const CONTAINER = {width: 220, height: 110};

export async function execute(context) {
    const {cy, trigger_reason} = context;
    _resetElevation(cy);
    const chrome = applyStandardChrome(cy);
    const labelInset = parentLabelInset({...chrome, inset: 16});
    //: The bottom edge leaves room for the name under an icon node, which is drawn outside its card.
    const pad = {top: 14 + labelInset, right: 24, bottom: 40, left: 24};
    //: The interior's own chrome and padding, at INTERIOR_SCALE (playground exception 10).
    const interiorChrome = {...chrome, parentFontSize: chrome.parentFontSize * INTERIOR_SCALE, nodeFontSize: chrome.nodeFontSize * INTERIOR_SCALE};
    const interiorInset = 16 * INTERIOR_SCALE;
    const interiorPad = {top: 14 * INTERIOR_SCALE + parentLabelInset({...interiorChrome, inset: interiorInset}),
        right: 24 * INTERIOR_SCALE, bottom: 24 * INTERIOR_SCALE, left: 24 * INTERIOR_SCALE};

    const types = [...new Set(cy.nodes().map((n) => n.data("entity_type")).filter(Boolean))];
    const baseSizes = Object.fromEntries(types.map((t) => [t, t === T.subnet ? SUBNET : CONTAINERS.includes(t) ? CONTAINER : LEAF]));
    // The interior is sized at INTERIOR_SCALE (a leaf program, and the container's floor); the circle of the flow is half an icon.
    baseSizes[T.program] = {width: LEAF.width * INTERIOR_SCALE, height: LEAF.height * INTERIOR_SCALE};
    baseSizes[T.ecsContainer] = {width: 0, height: 0};
    baseSizes[T.os] = {width: 0, height: 0};
    baseSizes[T.lib] = baseSizes[T.pkg] = baseSizes[T.program];
    baseSizes[T.rds] = RDS_BOX;
    baseSizes[T.flow] = {width: ICON.width * FLOW_SCALE, height: ICON.height * FLOW_SCALE};
    // Playground exception 49: the image host only joins the container to its operating system and packages; it is never drawn.
    cy.edges().filter((e) => _edgeType(e) === E.runsImage).forEach((e) => e.target().addClass(ELEVATION_HIDDEN_CLASS));
    const piles = _collapseZoneCopies(cy);
    const shown = (types) => cy.nodes().filter((n) => types.includes(n.data("entity_type")) && !n.hasClass(ELEVATION_HIDDEN_CLASS));
    // Playground exception 32: a node with a logo is a bordered card like GitHub, with the logo as its icon.
    const logos = _logoNodes(shown(SOLO_TYPES));
    applyIconNodes(cy, {members: shown(ICON_TYPES), ...ICON, iconNodeId: "landing"});
    // Playground exception 44: a logo card is drawn at the size of the delivery icons, not the standard card size.
    applyIconNodes(cy, {members: logos, width: SOLO.width * DEPLOY_SCALE, height: SOLO.height * DEPLOY_SCALE, iconNodeId: "landing-logo"});
    applyIconNodes(cy, {members: shown(SOLO_ICON_TYPES), ...ICON, solo: true, iconNodeId: "landing-solo-icon"});
    const deploy = _deployPath(cy, shown);
    // Playground exception 46: the Route 53 zone is drawn at the size of the delivery icons.
    const zones = shown([T.zone]).not(deploy).not(logos);
    applyIconNodes(cy, {members: shown(SOLO_TYPES).not(deploy).not(logos).not(zones), ...SOLO, solo: true, iconNodeId: "landing-solo"});
    applyIconNodes(cy, {members: zones, width: SOLO.width * DEPLOY_SCALE, height: SOLO.height * DEPLOY_SCALE, solo: true, iconNodeId: "landing-solo-zone"});
    // Playground exception 28: the deploy icons are half size.
    applyIconNodes(cy, {members: deploy, width: SOLO.width * DEPLOY_SCALE, height: SOLO.height * DEPLOY_SCALE, solo: true, iconNodeId: "landing-solo-deploy"});
    // Playground exception 38: a flow's circle is turned to the way its data goes.
    await _rotateFlowIcons(shown([T.flow]));
    applyIconNodes(cy, {members: shown([T.flow]), width: ICON.width * FLOW_SCALE, height: ICON.height * FLOW_SCALE, solo: true, iconNodeId: "landing-solo-flow"});
    _noBorder(cy.nodes().filter((n) => n.data("_icon_solo")));
    // Playground exception (deploy pile room; should become a reserve option of the nested layouts): the deploy icons
    // are out of the nesting while it runs, so the account is sized for its own rows; they are placed as a pile below
    // them afterwards, which grows the account.
    deploy.addClass(ELEVATION_HIDDEN_CLASS);
    // Playground exception 30: a slotted VPC, its subnets and their residents are out of the nesting; they are drawn by hand below.
    const slotted = _slottedVpcs(cy, shown);
    slotted.nodes.addClass(ELEVATION_HIDDEN_CLASS);
    slotted.edges.addClass(HIDDEN_CONTAINMENT_CLASS);
    // Playground exception 27: a flow with no `column` is not in the nesting; it is out of the way while the nesting runs.
    const placed = _placedFlows(shown([T.flow]));
    placed.addClass(ELEVATION_HIDDEN_CLASS);
    _stampVpcColumns(cy);
    _stampRootColumns(cy);
    // Playground exceptions 11, 48 and 49: the interior's derived containment, and its piles (all but the face of each out of the nesting).
    _deriveInterior(cy);
    piles.push(..._collapseInteriorPiles(cy));

    const result = await projectNested(cy, {
        relationships: [
            {name: "boundary-holds-account", gryphon: `(parent:${T.boundary})<-[:${E.scopedTo}]-(child:${T.account})`},
            {name: "account-holds", gryphon: `(parent:${T.account})<-[:${E.belongs}]-(child)`},
            {name: "vpc-holds-subnets", gryphon: `(parent:${T.vpc})-[:${E.partitioned}]->(child)`},
            {name: "vpc-holds-gateway", gryphon: `(parent:${T.vpc})<-[:${E.attachedToVpc}]-(child)`},
            {name: "subnet-holds", gryphon: `(parent:${T.subnet})<-[:${E.residesInSubnet}]-(child)`},
            {name: "task-holds-container", gryphon: `(parent:${T.task})-[:${E.runsContainer}]->(child:${T.ecsContainer})`},
            {name: "container-holds-os", gryphon: `(parent:${T.ecsContainer})-[:${E.containsOs}]->(child:${T.os})`},
            {name: "os-holds-program", gryphon: `(parent:${T.os})-[:${E.osRunsProgram}]->(child:${T.program})`},
            {name: "container-holds-library", gryphon: `(parent:${T.ecsContainer})-[:${E.containsLibrary}]->(child:${T.lib})`},
            {name: "container-holds-package", gryphon: `(parent:${T.ecsContainer})-[:${E.containsPackage}]->(child:${T.pkg})`},
            {name: "database-holds-program", gryphon: `(parent:${T.rds})-[:${E.runsProgram}]->(child:${T.program})`},
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
        paddings: {...Object.fromEntries(CONTAINERS.map((t) => [t, pad])), [T.task]: {...pad, top: pad.top + TASK_TOP_ROOM}, [T.ecsContainer]: interiorPad, [T.os]: interiorPad, [T.rds]: {...interiorPad, top: pad.top}},
        innerLayout: {name: "ranked", sort: "order", columnGap: 140, rowGap: 56, columnLayout: "flow"},
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
            [T.vpc]: {name: "ranked", sort: "order", columnGap: VPC_COLUMN_GAP, rowGap: 12},
            [T.rds]: {name: "flow", gap: 12 * INTERIOR_SCALE, sort: "label"},
            [T.subnet]: {name: "flow", gap: 8, sort: "label"},
            [T.task]: {name: "flow", gap: 12, sort: "label"},
            //: tap-web left, gunicorn right: the `column` dimension (read by _stampRootColumns) orders the siblings.
            [T.ecsContainer]: {name: "ranked", sort: "order", columnGap: 12 * INTERIOR_SCALE, rowGap: PILE_GAP},
            //: Inside the operating system: gunicorn left, tap-web right, as they stood in the container.
            [T.os]: {name: "ranked", sort: "order", columnGap: 12 * INTERIOR_SCALE, rowGap: 12 * INTERIOR_SCALE},
        },
    });

    piles.forEach((pile) => {
        applyStack(cy, pile);
    });
    // Playground exception 48: the container's own RUNS_PROGRAM edges are the containment the operating-system box now shows.
    cy.edges().filter((e) => _edgeType(e) === E.runsProgram && e.source().data("entity_type") === T.ecsContainer)
        .addClass(HIDDEN_CONTAINMENT_CLASS);
    deploy.removeClass(ELEVATION_HIDDEN_CLASS);
    placed.removeClass(ELEVATION_HIDDEN_CLASS);

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
        const row = roots.filter((n) => n.data("_stage") !== productStage && !_onDeliveryLine(n));
        cy.scratch("landing_row", alignDistributeHorizontal(cy, {members: row, anchorNode: anchor, distribute: false, reactive: false}));
    }

    // Playground exception (gateway on the line; should become an anchor-relative align of a nested node in the
    // ranked natural layout): the internet gateway is the first column of the VPC and is top-aligned with it, so
    // it sits above the line. Put it on the anchor's line, align-only.
    const gateway = shown([T.igw]);
    if (anchor.nonempty() && gateway.nonempty()) {
        alignDistributeHorizontal(cy, {members: gateway, anchorNode: anchor, distribute: false, reactive: false});
    }

    // Playground exception (deploy pile room): the account grows downward for the pile. The line of sight does not
    // move (the anchor is above the growth); what stands beneath the account is placed by _closePairs afterwards.
    if (cy.scratch("landing_deploy")) cy.scratch("landing_deploy").destroy();
    const accountBottom = account.nonempty() ? account.boundingBox({includeLabels: false, includeOverlays: false}).y2 : 0;
    const slotSize = _slotSize(slotted, pad);
    const pile = _placeDeployPile(cy, account, deploy, pad, slotSize.height);
    cy.scratch("landing_deploy", pile);
    _placeSlotted(cy, account, slotted, slotSize, pile, pad);
    _growAncestors(cy, account, accountBottom);
    // Playground exception 29: the delivery line runs through the pile.
    if (pile.lineY !== undefined) {
        alignDistributeHorizontal(cy, {members: roots.filter(_onDeliveryLine), anchor: {y: pile.lineY}, distribute: false, reactive: false});
        _shiftGithub(roots.filter(_onDeliveryLine));
    }
    _closePairs(roots, account, productRoot);
    _centreFlow(cy, roots, productRoot, shown([T.flow]).not(placed));
    _alignInteriorToLine(cy, anchor);
    _alignDatabaseProgram(cy, anchor);
    _placeFlows(cy, placed);

    // An empty container is still a box, not a leaf.
    cy.nodes(CONTAINERS.map((t) => `[entity_type = "${t}"]`).join(", ")).forEach((n) => {
        if (n.data("_is_icon_node")) return;
        if (!cy.nodes().some((c) => c.data("_viewport_parent") === n.id())) n.addClass("tap-viewport-parent");
    });
    // Playground exception 10: the interior's labels at INTERIOR_SCALE (placeParentLabels reads `cy.nodes` and `cy.batch`
    // only, so it is handed the interior's parents and the rest separately).
    const interior = containedNodes(cy, LIFT_EDGE).outermost;
    const isInterior = (n) => interior.has(n.id()) || _interiorStackPart(n);
    const parents = cy.nodes("." + VIEWPORT_PARENT_CLASS);
    const isSubnet = (n) => n.data("entity_type") === T.subnet;
    const isDatabase = (n) => n.data("entity_type") === T.rds;
    const isVpc = (n) => n.data("entity_type") === T.vpc;
    placeParentLabels(_only(cy, parents.filter((n) => !isInterior(n) && !isSubnet(n) && !isDatabase(n) && !isVpc(n))), {
        anchor: "upper-left", inset: 16,
        parentFontSize: chrome.parentFontSize, parentFontWeight: chrome.parentFontWeight,
    });
    // Playground exception 45: the VPCs' titles are VPC_TITLE_FACTOR of the usual size (`_scaleFont` reads the factor), bold as before.
    parents.filter((n) => isVpc(n) && !isInterior(n)).forEach((n) => n.scratch("landingFontFactor", VPC_TITLE_FACTOR));
    // Playground exception 46: the boundary's title is the same size as the VPC titles (`_styleBoundary` measures it afterwards).
    shown([T.boundary]).forEach((n) => n.scratch("landingFontFactor", VPC_TITLE_FACTOR));
    placeParentLabels(_only(cy, parents.filter((n) => isVpc(n) && !isInterior(n))), {
        anchor: "upper-left", inset: 16,
        parentFontSize: chrome.parentFontSize * VPC_TITLE_FACTOR, parentFontWeight: chrome.parentFontWeight,
    });
    // Playground exception 22 (a `label_position: inside` of the subnet's display hint): the subnets' labels stand inside the box,
    // top-centre. aws_core's default puts them outside, above the box; the data override makes placeParentLabels treat them as
    // inside labels. Placed for the text FONT_SCALE times the base, which is what settle mode draws.
    const subnets = parents.filter(isSubnet);
    subnets.forEach((n) => {
        n.data("label_position", "inside");
        // Playground exception 33: subtle, smaller and not bold (`_scaleFont` reads the factor).
        n.scratch("landingFontFactor", SUBNET_LABEL_FACTOR);
    });
    placeParentLabels(_only(cy, subnets), {
        anchor: "top-center", inset: 16,
        parentFontSize: chrome.parentFontSize * FONT_SCALE * SUBNET_LABEL_FACTOR, parentFontWeight: SUBNET_LABEL_WEIGHT,
    });
    subnets.style({"font-weight": SUBNET_LABEL_WEIGHT});
    _keepTaskLabel(cy);
    // Playground exception 26: the database's box label, upper-left, at the text size the settle mode draws; kept for the reveal.
    // Playground exception 41: its title is top-centre and smaller (`_scaleFont` reads the factor).
    parents.filter(isDatabase).forEach((n) => n.scratch("landingFontFactor", DB_TITLE_FACTOR));
    placeParentLabels(_only(cy, parents.filter(isDatabase)), {
        anchor: "top-center", inset: 16,
        parentFontSize: chrome.parentFontSize * FONT_SCALE * DB_TITLE_FACTOR, parentFontWeight: chrome.parentFontWeight,
    });
    placeParentLabels(_only(cy, parents.filter(isInterior)), {
        anchor: "upper-left", inset: interiorInset,
        parentFontSize: interiorChrome.parentFontSize, parentFontWeight: chrome.parentFontWeight,
    });
    parents.filter(isInterior).style({"font-size": `${interiorChrome.parentFontSize}px`});
    cy.nodes().filter((n) => isInterior(n) && !n.hasClass(VIEWPORT_PARENT_CLASS)).style({"font-size": `${interiorChrome.nodeFontSize}px`});
    // Playground exceptions 39 and 40: the interior programs' names inside their boxes, the flows' names smaller.
    _labelProgramsInside(cy.nodes().filter((n) => isInterior(n) && [T.program, T.lib, T.pkg].includes(n.data("entity_type"))));
    // Playground exception 48: the operating-system box, in its own colours.
    _styleOs(cy.nodes(`[entity_type = "${T.os}"]`));
    shown([T.flow]).forEach((n) => n.scratch("landingFontFactor", FLOW_FONT_FACTOR));
    // Playground exception 47: the gateway's, the load balancer's and the database's names, under their icons, are as subtle as the subnets'.
    shown(NAMED_ICON_TYPES).forEach((n) => n.scratch("landingFontFactor", SUBNET_LABEL_FACTOR));
    // Playground exception 19: after every label's size is set, so the doubled size is the base the settle mode starts from.
    cy.nodes().forEach((n) => _scaleFont(n, isInterior(n) ? undefined : BASE_FONT));
    _keepDatabase(cy.nodes(`[entity_type = "${T.rds}"]`));
    _formDatabase(cy, cy.nodes(`[entity_type = "${T.rds}"]`), false);
    _hideLabels(cy);
    shown(NAMED_ICON_TYPES).not(`[entity_type = "${T.rds}"]`).style({"font-weight": SUBNET_LABEL_WEIGHT});
    // One line each, so the name stays inside the subnet's bottom room.
    shown(NAMED_ICON_TYPES).style({"text-wrap": "none"});
    _layerEdges(cy);
    _styleFlow(cy, shown([T.flow]));
    _styleBoundary(cy, shown([T.boundary]));
    _colourTitles(cy, parents.filter((n) => !isInterior(n) && (isVpc(n) || n.data("entity_type") === T.account)));
    _styleContainer(cy, cy.nodes(`[entity_type = "${T.ecsContainer}"]`));
    // Playground exception 9: the account elevation hides the interior and lifts the flow's edge onto the task; a zoom
    // past ELEVATION_REVEAL_ZOOM shows the interior and destroys the lift. The layout itself never changes between the two.
    _watchElevation(cy, context);
    _bindFlowWindow(cy);
    _pinBadgeSize(cy);
    _followIconPolicy(cy);
    if (trigger_reason === "initial_load") cy.fit(cy.nodes(":visible"), 40);
    return {warnings: result.warnings || []};
}

/**
 * Playground exception 24 (should become: zoom_settle leaves a solo icon's border alone, or applyIconNodes writes the zero itself): a solo
 * icon draws no border. The stylesheet says so (`node[?_icon_solo]`), but a bypass style wins over it, and the settle mode writes one
 * (the border it read, scaled) if it reads the node before the solo data is set. An explicit zero is read as the base, and zero is
 * never scaled.
 */
function _noBorder(nodes) {
    nodes.forEach((n) => n.style({"border-width": 0}));
}

/**
 * Playground exception 13 (should become an `edge_layer` option of applyStandardChrome: edges drawn above the container
 * fills and below the leaf nodes): how tap_viz orders what Cytoscape draws. Cytoscape sorts by `z-compound-depth` first
 * (bottom, auto, top), then, at the same depth, by `z-index-compare` (auto draws every node after every edge, whatever
 * its z-index; manual compares the z-index of the two), then by `z-index`. applyStandardChrome gives every edge
 * `z-compound-depth: top`, so every edge is drawn over every node, the load balancer and the internet gateway included.
 * Here the edges go to `auto` depth with a z-index just above the highest container (nested-projection gives a container
 * z-index = 10 x its depth), and nodes compare manually: the container fills stay below the edge, and every leaf node
 * (an icon node, a person, GitHub) is lifted just above it, keeping its own depth order, so an edge passes behind the
 * nodes on its way. Badges, stack cards and the stack chip keep the z-index the stylesheet gives them (999, 1000, the
 * stack's own), which is above. A lifted edge added later takes the edge rule, so it needs nothing of its own.
 */
function _layerEdges(cy) {
    const isParent = (n) => n.hasClass(VIEWPORT_PARENT_CLASS);
    const isOwnLayer = (n) => n.data("_is_badge") || n.data("_is_status_badge") || n.data("_is_stack_card")
        || n.data("_is_stack_chip") || n.data("_stack_front_id") !== undefined;
    const z = (n) => Number(n.style("z-index")) || 0;
    const containers = cy.nodes().filter(isParent);
    const edgeZ = (containers.nonempty() ? Math.max(...containers.map(z)) : 0) + 1;
    cy.style()
        .selector("edge").style({"z-compound-depth": "auto", "z-index": edgeZ})
        .selector("node").style({"z-index-compare": "manual"})
        .update();
    cy.batch(() => {
        cy.nodes().forEach((n) => {
            if (isParent(n) || isOwnLayer(n)) return;
            n.style({"z-index": edgeZ + 1 + Math.round(z(n) / 10)});
            // Playground exception 26: the database's solo form is a leaf (above the edges) and its box form a container (below them).
            if (n.data("entity_type") === T.rds) n.scratch("landing_db_layers", {box: edgeZ - 1, solo: edgeZ + 1 + Math.round(z(n) / 10)});
        });
    });
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
            // Left-aligned: a centred label is shifted so its left end stands on the box's left edge.
            "text-margin-x": _boundaryLabelShift(n),
            "text-margin-y": -BOUNDARY_LABEL_RISE,
            "text-wrap": "none", "text-max-width": `${n.width()}px`,
        });
    });
}

/**
 * Playground exception 18 (same exit as _styleBoundary, a per-node display override): the ECS container is a darker orange than the
 * task around it (aws_core's default for the type is the task's own peach, #F9D7B7, so a container does not stand out inside it).
 * Its type icon is the aws_core badge, drawn when the interior is shown (_refreshBadges).
 */
const CONTAINER_FILL = "#F29B38";
const CONTAINER_BORDER = "#B45309";
const CONTAINER_LABEL = "#3B1A00";
function _styleContainer(cy, containers) {
    containers.forEach((n) => n.style({
        "background-color": CONTAINER_FILL, "background-opacity": 1,
        "border-color": CONTAINER_BORDER, "border-width": 3, "color": CONTAINER_LABEL,
    }));
}

/**
 * Playground exception 46 (should become a `label_color` of the container type's display hint): the titles of the account and of the VPCs
 * are a darker accent of their own box's border colour, TITLE_DARKEN of it, not black. Read from the node's own border colour.
 */
const TITLE_DARKEN = 0.6;
function _colourTitles(cy, containers) {
    containers.forEach((n) => {
        const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(n.style("border-color"));
        if (!m) return;
        n.style({"color": `rgb(${[m[1], m[2], m[3]].map((v) => Math.round(Number(v) * TITLE_DARKEN)).join(",")})`});
    });
}

function _boundaryLabelShift(node) {
    const ctx = document.createElement("canvas").getContext("2d");
    if (!ctx) return 0;
    ctx.font = `${node.style("font-weight")} ${node.style("font-size")} sans-serif`;
    const textWidth = ctx.measureText(node.data("label") || "").width;
    return -(node.width() - textWidth) / 2;
}

function _whenShown(cy, draw, tries = 600, waited = false) {
    const container = cy.container();
    // Playground exception (same exit): always at least one frame after the run, so a re-run of the layout (the second
    // elevation) has finished moving nodes before the box starts tracking them (it recurses otherwise).
    if (waited && (!container || container.style.visibility !== "hidden" || tries <= 0)) {
        draw();
        return;
    }
    requestAnimationFrame(() => _whenShown(cy, draw, tries - 1, true));
}

/**
 * Playground exception 28 (should become a `pile` arrangement of the align/distribute helpers, a bottom-right corner of the nested layouts'
 * reserved row, and a front-only name): stand the deploy-path icons as a card pile at the bottom-right of the account, below the account's
 * other contents. The members are put in order from the back to the front (the `layout:order` tag when a node has one, then label, a stable
 * key and never a place), each PILE_STEP right and down of the one behind it, the last in front; only the front icon keeps its name, since
 * the others' names would stand under the icons in front. The titled scope box (tap_viz's own) surrounds exactly the pile. The account
 * grows downward to hold it. The edges between two icons of the pile are hidden (they would run along and under the icons); edges that
 * leave it stay. Returns a handle whose destroy() removes the box and restores those edges, and whose `lineY` is the horizontal line
 * through the front icon of the pile (the delivery line, exception 29).
 */
function _placeDeployPile(cy, account, deploy, pad, slotHeight = 0) {
    const restore = () => {
        cy.edges().filter((e) => e.data("_row_internal")).forEach((e) => {
            e.removeData("_row_internal");
            e.removeStyle("display");
        });
        cy.nodes().filter((n) => n.scratch("landing_pile_hidden_name")).forEach((n) => {
            n.removeScratch("landing_pile_hidden_name");
            n.removeStyle("text-opacity");
        });
    };
    restore();
    if (account.empty() || deploy.empty()) return {destroy: restore};
    const box = account.boundingBox({includeLabels: false, includeOverlays: false});
    const others = cy.nodes().filter((n) => n.data("_viewport_parent") === account.id() && !n.hasClass(ELEVATION_HIDDEN_CLASS)
        && !deploy.anySame(n));
    const above = others.nonempty() ? others.boundingBox({includeLabels: true, includeOverlays: false}).y2 : box.y1;
    const iconWidth = (n) => Number(n.data("_icon_w")) || n.width();
    const iconHeight = (n) => Number(n.data("_icon_h")) || n.height();
    const tagOrder = (n) => Number((n.data("tags") || {})["layout:order"]);
    const ordered = deploy.toArray().sort((a, b) => {
        const ta = tagOrder(a), tb = tagOrder(b);
        if (Number.isFinite(ta) && Number.isFinite(tb) && ta !== tb) return ta - tb;
        return String(a.data("label")).localeCompare(String(b.data("label")));
    });
    const w = iconWidth(ordered[0]), h = iconHeight(ordered[0]);
    const spread = PILE_STEP * (ordered.length - 1);
    // The scope box starts DEPLOY_BOX_PADDING above the icons (and 44 clear of what is above) and its right edge stands DEPLOY_BOX_PADDING
    // inside the account's padding.
    const top = above + 44 + DEPLOY_BOX_PADDING;
    const left = box.x2 - pad.right - DEPLOY_BOX_PADDING - (w + spread);
    const baseZ = Number(account.style("z-index")) + 10;
    ordered.forEach((n, i) => {
        n.style({"z-index": baseZ + i});
        n.position({x: left + w / 2 + PILE_STEP * i, y: top + h / 2 + PILE_STEP * i});
        n.data("_viewport_parent", account.id());
        if (i < ordered.length - 1) {
            n.style({"text-opacity": 0});
            n.scratch("landing_pile_hidden_name", true);
        }
    });
    let handle = {destroy: () => {}}, destroyed = false;
    const ids = new Set(ordered.map((n) => n.id()));
    // Playground exception: the scope box tracks its members' bounds, and cytoscape recurses computing them while the
    // projection is still revealing the scene (the graph element is hidden). Draw the box once the scene is shown.
    // Should become a fix in the tap_viz scope-box helper (observed 2026-10-19), after which this wait goes.
    _whenShown(cy, () => {
        if (destroyed) return;
        const boxes = applyScopeBoxes(cy, [{label: DEPLOY_LABEL, filter: (n) => ids.has(n.id()), style: {padding: DEPLOY_BOX_PADDING}}]);
        const title = _syncScopeTitle(cy);
        handle = {destroy: () => {
            title.destroy();
            boxes.destroy();
        }};
    });
    cy.edges().filter((e) => deploy.anySame(e.source()) && deploy.anySame(e.target())).forEach((e) => {
        e.data("_row_internal", true);
        e.style("display", "none");
    });
    // Bottom of the box: the pile, the room for the front name, then the account's own bottom padding.
    // The slotted VPC (exception 30) stands in the same row, from the row's top; the row is as tall as the taller of the two.
    // Playground exception 45: no room for a front name that is hidden.
    const nameRoom = _labelHidden(ordered[ordered.length - 1]) ? PILE_NAMELESS_ROOM : PILE_NAME_ROOM;
    const newBottom = Math.max(top + h + spread + DEPLOY_BOX_PADDING + nameRoom, above + 44 + slotHeight) + pad.bottom;
    const delta = Math.max(0, newBottom - box.y2);
    if (delta > 0) {
        account.style({height: box.h + delta});
        account.position({x: account.position("x"), y: account.position("y") + delta / 2});
    }
    return {
        rowTop: above + 44,
        // Ruled 2026-10-20: the line through the FRONT icon of the pile (the source puller), not the middle of the pile.
        lineY: top + h / 2 + spread,
        destroy: () => {
            destroyed = true;
            handle.destroy();
            restore();
        },
    };
}

/**
 * Playground exception 30: the VPCs that carry `place: bottom-center`, with what stands in them: their subnets (PARTITIONED_INTO_SUBNET) and what
 * resides in those (RESIDES_IN_SUBNET), and the edges that would draw that containment as lines (these and the VPC's ownership by an
 * account), which nesting would have consumed. Read from the shown nodes and the edges, never a type or a name.
 */
function _slottedVpcs(cy, shown) {
    const vpcs = shown([T.vpc]).filter((n) => (n.data("dimensions") || {})[PLACE_KEY] === PLACE_BOTTOM_CENTER);
    const chains = vpcs.map((vpc) => {
        const subnets = cy.edges().filter((e) => _edgeType(e) === E.partitioned && e.source().same(vpc)).map((e) => e.target());
        const subnetIds = new Set(subnets.map((n) => n.id()));
        const residents = cy.edges().filter((e) => _edgeType(e) === E.residesInSubnet && subnetIds.has(e.target().id()))
            .map((e) => ({subnet: e.target(), node: e.source()}));
        return {vpc, subnets, residents};
    });
    const nodes = cy.collection();
    const edges = cy.collection();
    chains.forEach(({vpc, subnets, residents}) => {
        nodes.merge(vpc);
        subnets.forEach((n) => nodes.merge(n));
        residents.forEach(({node}) => nodes.merge(node));
        edges.merge(vpc.connectedEdges().filter((e) => _edgeType(e) === E.partitioned || _edgeType(e) === E.belongs));
        subnets.forEach((n) => edges.merge(n.connectedEdges().filter((e) => _edgeType(e) === E.residesInSubnet)));
    });
    return {chains, nodes, edges};
}

/**
 * Playground exception 30: the box sizes of a slotted VPC, from the paddings the nesting would use: the instance is a solo icon, the
 * subnet holds it under a title and above its name, the VPC holds the subnet under its own title.
 */
function _slotSize(slotted, pad) {
    const sizes = slotted.chains.map(({vpc, subnets, residents}) => {
        const subnetBoxes = subnets.map((subnet) => {
            const held = residents.filter((r) => r.subnet.same(subnet)).map((r) => r.node);
            const iconW = held.length ? Math.max(...held.map((n) => Number(n.data("_icon_w")) || n.width())) : 0;
            const iconH = held.length ? Math.max(...held.map((n) => Number(n.data("_icon_h")) || n.height())) : 0;
            // Playground exception 44: a small resident with no name needs neither the subnet's usual width nor the room for its name.
            const nameless = held.length && held.every(_labelHidden);
            const bottom = nameless ? SLOT_NAMELESS_BOTTOM : pad.bottom;
            const top = nameless ? Math.min(pad.top, SLOT_SUBNET_TOP) : pad.top;
            return {subnet, held, width: Math.max(SLOT_SUBNET_WIDTH, iconW + pad.left + pad.right), height: top + iconH + bottom, top, iconH};
        });
        const width = Math.max(...subnetBoxes.map((b) => b.width), 0) + 2 * SLOT_PADDING;
        const height = SLOT_TOP + subnetBoxes.reduce((sum, b) => sum + b.height, 0) + SLOT_PADDING;
        return {vpc, subnetBoxes, width, height};
    });
    return {sizes, height: Math.max(0, ...sizes.map((b) => b.height))};
}

/**
 * Playground exception 30 (should become a `slot: bottom-center` of the nested layouts' tiered rows): draw each slotted VPC by hand at the
 * centre of the account's bottom row, from the row's top (the same top the delivery pile uses), centred on the account's centre line. Each
 * subnet is centred in its VPC and each resident (a solo icon) in its subnet; the boxes carry the container class and the nesting data,
 * as the nested layout would have stamped them.
 */
function _placeSlotted(cy, account, slotted, slotSize, pile, pad) {
    if (account.empty() || !slotSize.sizes.length) return;
    const baseZ = Number(account.style("z-index")) + 10;
    slotSize.sizes.forEach(({vpc, subnetBoxes, width, height}) => {
        const x = account.position("x");
        const top = pile.rowTop;
        vpc.style({width, height, "z-index": baseZ});
        vpc.position({x, y: top + height / 2});
        vpc.data("_viewport_parent", account.id());
        vpc.addClass(VIEWPORT_PARENT_CLASS);
        // The subnets stand under the VPC's title room, one above the other.
        let y = top + height - SLOT_PADDING - subnetBoxes.reduce((sum, b) => sum + b.height, 0);
        subnetBoxes.forEach(({subnet, held, top: st, width: sw, height: sh}) => {
            subnet.style({width: sw, height: sh, "z-index": baseZ + 10});
            subnet.position({x, y: y + sh / 2});
            subnet.data("_viewport_parent", vpc.id());
            subnet.addClass(VIEWPORT_PARENT_CLASS);
            // A resident stands under the subnet's title room, its name below it inside the bottom room.
            held.forEach((n) => {
                n.position({x, y: y + st + (Number(n.data("_icon_h")) || n.height()) / 2});
                n.data("_viewport_parent", subnet.id());
            });
            y += sh;
        });
    });
    slotted.nodes.removeClass(ELEVATION_HIDDEN_CLASS);
}

/**
 * Playground exception 31: whether a node's name is hidden, read from its `label` dimension.
 */
function _labelHidden(n) {
    return (n.data("dimensions") || {})[LABEL_KEY] === LABEL_HIDDEN;
}

function _hideLabels(cy) {
    cy.batch(() => cy.nodes().filter(_labelHidden).forEach((n) => n.style({"text-opacity": 0})));
}

/**
 * Playground exception 32: the nodes among `candidates` that carry an `icon` dimension naming a static icon (`<app>/icons/<key>.svg`, the
 * grid's icon convention): their `icon_url` is set to it. Anything that is not of that shape is ignored.
 */
function _logoNodes(candidates) {
    const withIcon = candidates.filter((n) => ICON_PATH.test(String((n.data("dimensions") || {})[ICON_KEY] || "")));
    withIcon.forEach((n) => n.data("icon_url", `/static/${n.data("dimensions")[ICON_KEY]}`));
    // Playground exception 42: an icon that is a whole card of its own stays a solo icon (it is the card).
    return withIcon.filter((n) => (n.data("dimensions") || {})[ICON_FORM_KEY] !== ICON_FORM_SOLO);
}

/**
 * Playground exception 37: GitHub, the first node of the delivery line (the lowest column), moves GITHUB_SHIFT right.
 */
function _shiftGithub(members) {
    const first = members.toArray().sort((a, b) => a.data("_stage") - b.data("_stage"))[0];
    if (first) first.position({x: first.position("x") + GITHUB_SHIFT, y: first.position("y")});
}

/**
 * Playground exception 36: the PostgreSQL program (what the database runs) is moved to the line of sight, so at the revealed
 * elevation it is level with gunicorn. The box stays where the layout put it (centred on the line); only the program moves.
 */
function _alignDatabaseProgram(cy, anchor) {
    if (anchor.empty()) return;
    const {outermost} = containedNodes(cy, LIFT_EDGE);
    outermost.forEach((top, id) => {
        const n = cy.getElementById(id);
        if (n.data("entity_type") !== T.program) return;
        const holder = cy.getElementById(top);
        if (holder.empty() || holder.data("entity_type") !== T.rds) return;
        n.position({x: n.position("x"), y: anchor.position("y")});
    });
}

function _settleConfig(cy) {
    const host = cy.container() && cy.container().closest("[data-zoom-settle]");
    try {
        return host ? normalizeSettleConfig(JSON.parse(host.dataset.zoomSettle)) : null;
    } catch (_err) {
        return null;
    }
}

/**
 * Playground exception 34 (should become a `label_size` option of the scope-box helper): the scope box's title is an HTML element
 * scaled with the canvas, 11 px of the model. Every zoom sets it to what the settle mode gives a container title: the doubled base
 * times the font class's factor, so it is the same size on screen as the other container titles.
 */
function _syncScopeTitle(cy) {
    const apply = () => {
        const config = _settleConfig(cy);
        const factor = config ? modelFactor(cy.zoom(), config.classes.font) : 1;
        // Playground exception 46: the same size as the VPC titles (Admin Access).
        const size = `${BASE_FONT * FONT_SCALE * factor * VPC_TITLE_FACTOR}px`;
        const root = cy.container();
        if (!root) return;
        // Right-aligned to the box: the larger title then runs left over empty account space, not over the flow name beside the box.
        root.querySelectorAll(".tap-scope-box__label").forEach((el) => {
            el.style.fontSize = size;
            el.style.left = "auto";
            el.style.right = "12px";
            // Playground exception 45: no fill behind the title.
            el.style.background = "transparent";
        });
    };
    cy.on("zoom", apply);
    apply();
    return {destroy: () => cy.off("zoom", apply)};
}

/**
 * Playground exception 29 (should become an `align-to-line` of a named group in the ranked natural layout of the roots): whether a node
 * stands on the delivery line, read from its data: the dimension `line` (people and computers, which have no tagging system) or the tag
 * `layout:line` (a type that has one, GitHub) is `delivery`. Never a type, a name or an id.
 */
function _onDeliveryLine(n) {
    return (n.data("dimensions") || {})[LINE_KEY] === LINE_DELIVERY || (n.data("tags") || {})[LINE_TAG] === LINE_DELIVERY;
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
                person.position({x, y: y + (person.height() + computer.height()) / 2 + PAIR_GAP + PAIR_NAME_ROOM});
                // Playground exception 25: the vertical pair's names are as small as the horizontal pairs'.
                person.scratch("landingFontFactor", PAIR_FONT_FACTOR);
                computer.scratch("landingFontFactor", PAIR_FONT_FACTOR);
            } else {
                person.scratch("landingFontFactor", PAIR_FONT_FACTOR);
                computer.scratch("landingFontFactor", PAIR_FONT_FACTOR);
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

/**
 * Playground exception 7 (STANDING EXCEPTION; should become a projection-declared `node_info` window of tap_viz, a
 * sibling of the status-badge info window, bound to a node type): a tap on an application flow opens a window with
 * the node's own name, description and `dataclass.*` dimensions. It reads only the node's Cytoscape data (`label`,
 * `fields.description`, `dimensions`, all lifted from the envelope by panel-graph.js): no network call. It reuses the
 * tap_viz info window's CSS classes and behaves like it: a close X, ESC, a click outside, one window at a time (a
 * status-badge window is closed first; a badge click closes this one through the outside click).
 * Bound once per graph (the previous handler is removed first), because the layout runs again on every elevation change.
 */
function _bindFlowWindow(cy) {
    // Not an event namespace: Cytoscape (3.x here) does not fire a namespaced listener for a plain "tap". The handler is
    // kept in the graph's scratch so the next run of the layout unbinds exactly it.
    const previous = cy.scratch("playgroundFlowWindowHandler");
    if (previous) cy.off("tap", "node", previous);
    const handler = (evt) => {
        const node = evt.target;
        if (node.data("entity_type") !== T.flow) return;
        _openFlowWindow(cy, node);
    };
    cy.scratch("playgroundFlowWindowHandler", handler);
    cy.on("tap", "node", handler);
}

let _flowWindow = null;

function _closeFlowWindow() {
    if (!_flowWindow) return;
    const state = _flowWindow;
    _flowWindow = null;
    document.removeEventListener("keydown", state.keydown);
    if (state.outsideClick) document.removeEventListener("click", state.outsideClick, true);
    if (state.el.parentNode) state.el.parentNode.removeChild(state.el);
}

function _openFlowWindow(cy, node) {
    const panelEl = cy.container();
    if (!panelEl) return;
    const wasThis = _flowWindow && _flowWindow.nodeId === node.id();
    _closeFlowWindow();
    closeInfoWindow();
    if (wasThis) return;
    const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    const dims = Object.entries(node.data("dimensions") || {}).filter(([key]) => key.startsWith(FLOW_DIMENSION_PREFIX))
        .sort(([a], [b]) => a.localeCompare(b));
    const description = (node.data("fields") || {}).description || "";
    const rows = dims.length
        ? dims.map(([key, value]) => `<tr><td>${esc(key)}</td><td><strong>${esc(value)}</strong></td></tr>`).join("")
        : `<tr><td>none</td></tr>`;
    const el = document.createElement("div");
    el.className = FLOW_WINDOW_CLASS;
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", "Application flow details");
    el.dataset.playgroundFlowWindow = "true";
    el.innerHTML = `
        <div class="tap-info-window__header">
            <div class="tap-info-window__title">
                <div class="tap-info-window__name">${esc(node.data("label") || node.id())}</div>
                <div class="tap-info-window__type">${esc(node.data("entity_type"))}</div>
            </div>
            <button type="button" class="tap-info-window__close" aria-label="Close">×</button>
        </div>
        <div class="tap-info-window__body">
            <section class="tap-info-window__section">
                <div class="tap-info-window__section-header"><span class="tap-info-window__set-name">Description</span></div>
                <div class="tap-info-window__section-body" data-flow-description>${esc(description)}</div>
            </section>
            <section class="tap-info-window__section">
                <div class="tap-info-window__section-header">
                    <span class="tap-info-window__set-name">Data classification</span>
                    <span class="tap-info-window__count">${dims.length}</span>
                </div>
                <div class="tap-info-window__section-body">
                    <table class="tap-info-window__table"><tbody>${rows}</tbody></table>
                </div>
            </section>
        </div>`.trim();
    // Positioned like the tap_viz info window: right of the node, clamped to the panel.
    const rpos = node.renderedPosition();
    const panelRect = panelEl.getBoundingClientRect();
    const left = Math.min(Math.max(0, rpos.x + node.renderedWidth() / 2 + FLOW_WINDOW_OFFSET), Math.max(0, panelRect.width - FLOW_WINDOW_WIDTH));
    const top = Math.min(Math.max(0, rpos.y - node.renderedHeight() / 2), Math.max(0, panelRect.height - 40));
    el.style.position = "absolute";
    el.style.left = `${left}px`;
    el.style.top = `${top}px`;
    el.style.width = `${FLOW_WINDOW_WIDTH}px`;
    el.style.maxHeight = `${Math.floor(panelRect.height * 0.6)}px`;
    panelEl.appendChild(el);
    const state = {el, nodeId: node.id(), keydown: null, outsideClick: null};
    _flowWindow = state;
    el.querySelector(".tap-info-window__close").addEventListener("click", (e) => {
        e.stopPropagation();
        _closeFlowWindow();
    });
    state.keydown = (e) => {
        if (e.key === "Escape") _closeFlowWindow();
    };
    document.addEventListener("keydown", state.keydown);
    // One tick so the tap that opened the window does not dismiss it.
    setTimeout(() => {
        if (_flowWindow !== state) return;
        state.outsideClick = (e) => {
            if (!state.el.contains(e.target)) _closeFlowWindow();
        };
        document.addEventListener("click", state.outsideClick, true);
    }, 0);
}

/**
 * Playground exception 27: the flows that are not ranked among the roots, those with no `column` dimension (the customer's flow
 * carries one and is placed by `_centreFlow`).
 */
function _placedFlows(flows) {
    return flows.filter((flow) => (flow.data("dimensions") || {}).column === undefined);
}

/** The chain of nodes that hold `node`, innermost first, read from the nesting the layout stamped. */
function _holders(cy, node) {
    const chain = [];
    for (let up = cy.getElementById(node.data("_viewport_parent") || ""); up.nonempty();
         up = cy.getElementById(up.data("_viewport_parent") || "")) chain.push(up);
    return chain;
}

/**
 * Playground exception 27 (should become a `place: between-endpoints` option of the nested layouts): each flow stands in the gap
 * between the two boxes its lines end on. The ends are the nodes drawn at the account elevation (the outermost holder in the
 * `lift_edge` relationships, so the web task and not the program inside it). Each end is taken up to the box that is a child of
 * the lowest holder the two share (a subnet, the authorization boundary, a root), and the flow stands midway between the facing
 * edges of those two boxes, on the line that joins the ends' centres: horizontally when they are further apart across than down,
 * vertically when not. Two boxes that overlap on that axis put it at the middle of their centres.
 */
function _placeFlows(cy, flows) {
    const {outermost} = containedNodes(cy, LIFT_EDGE);
    const drawn = (n) => cy.getElementById(outermost.get(n.id()) || n.id());
    const box = (n) => n.boundingBox({includeLabels: false, includeOverlays: false});
    flows.forEach((flow) => {
        const from = cy.edges().filter((e) => _edgeType(e) === E.flowSource && e.target().same(flow)).map((e) => e.source())[0];
        const to = cy.edges().filter((e) => _edgeType(e) === E.flowDestination && e.source().same(flow)).map((e) => e.target())[0];
        if (!from || !to) return;
        const a = drawn(from), b = drawn(to);
        const chainA = [a, ..._holders(cy, a)], chainB = [b, ..._holders(cy, b)];
        const shared = chainA.find((n) => chainB.some((m) => m.same(n)));
        const upTo = (chain) => (shared ? chain.slice(0, chain.findIndex((n) => n.same(shared))) : chain).pop() || chain[0];
        const outerA = upTo(chainA), outerB = upTo(chainB);
        const pa = a.position(), pb = b.position();
        const ba = box(outerA), bb = box(outerB);
        let x = (pa.x + pb.x) / 2, y = (pa.y + pb.y) / 2;
        if (Math.abs(pa.x - pb.x) >= Math.abs(pa.y - pb.y)) {
            const [left, right] = pa.x <= pb.x ? [ba, bb] : [bb, ba];
            if (right.x1 > left.x2) x = (left.x2 + right.x1) / 2;
        } else {
            const [top, bottom] = pa.y <= pb.y ? [ba, bb] : [bb, ba];
            if (bottom.y1 > top.y2) y = (top.y2 + bottom.y1) / 2;
        }
        flow.position({x, y});
    });
}

/**
 * Playground exception 26: remember the database's box and the label style the layout gave it (upper-left), before it is
 * made a solo icon, for the reveal.
 */
function _keepDatabase(nodes) {
    nodes.forEach((n) => {
        const label = {};
        ["text-valign", "text-halign", "text-margin-x", "text-margin-y", "text-wrap", "text-max-width"].forEach((prop) => {
            label[prop] = n.style(prop);
        });
        n.scratch("landing_db", {w: n.width(), h: n.height(), label});
    });
}

/**
 * Playground exception 26 (should become the `icon-solo` / `standard` forms of a node type in the Elevation definition): the
 * database is a solo icon at the account elevation and a standard box (light blue, its name upper-left, its type badge at the
 * top-right, the program drawn inside) once the interior is shown. The box is the size the layout reserved; the solo icon
 * stands at its centre.
 */
function _formDatabase(cy, nodes, revealed) {
    nodes.forEach((n) => {
        const keep = n.scratch("landing_db");
        const icons = n.scratch("landing_db_icons");
        if (icons) icons.destroy();
        n.removeScratch("landing_db_icons");
        if (!keep) return;
        if (revealed) {
            // The container class draws the box's own look (and suppresses the type icon, which the badge shows).
            n.addClass(VIEWPORT_PARENT_CLASS);
            const layers = n.scratch("landing_db_layers");
            if (layers) n.style({"z-index": layers.box});
            // Playground exception 31: the revealed standard box shows its name again.
            n.removeStyle("text-opacity font-weight");
            n.style({
                "width": keep.w, "height": keep.h, "shape": "round-rectangle",
                "background-color": RDS_FILL, "background-opacity": 1, "border-color": RDS_BORDER, "border-width": 3,
                "border-opacity": 1, "color": RDS_LABEL, ...keep.label,
            });
        } else {
            // The container class would hide the icon the solo form is made of.
            n.removeClass(VIEWPORT_PARENT_CLASS);
            const layers = n.scratch("landing_db_layers");
            if (layers) n.style({"z-index": layers.solo});
            n.removeStyle("background-color background-opacity border-color border-width border-opacity color shape "
                + Object.keys(keep.label).join(" "));
            n.scratch("landing_db_icons", applyIconNodes(cy, {members: n, ...SOLO, solo: true, iconNodeId: `landing-solo-db-${n.id()}`}));
            if (_labelHidden(n)) n.style({"text-opacity": 0});
            // Playground exception 47: the solo form's name is subtle (normal weight); the revealed box's title keeps its own.
            n.style({"font-weight": SUBNET_LABEL_WEIGHT});
        }
        n.dirtyBoundingBoxCache();
    });
}

/**
 * Playground exception 26 (should become a `badge_corner` option of the badge nodes): the database's type badge stands at the
 * top-right corner of its box, not the upper-left the runtime gives every other node. Runs after the badge pass and again on
 * each move of the box, after the runtime's own handler.
 */
function _moveDatabaseBadge(cy) {
    const previous = cy.scratch("landing_db_badge");
    if (previous) cy.off("position bounds", "node[_badge_active]", previous);
    // Re-entrancy guard (the tap#289 class): reading the host's box can emit `bounds` on it again.
    const placing = new Set();
    const place = (host) => {
        const badge = cy.getElementById(`badge:${host.id()}`);
        if (badge.empty() || placing.has(host.id())) return;
        placing.add(host.id());
        try {
            const bb = host.boundingBox({includeLabels: false});
            const pos = badge.position();
            if (pos.x !== bb.x2 || pos.y !== bb.y1) {
                badge.unlock();
                badge.position({x: bb.x2, y: bb.y1});
                badge.lock();
            }
        } finally {
            placing.delete(host.id());
        }
    };
    const handler = (evt) => {
        if (evt.target.data("entity_type") === T.rds) place(evt.target);
    };
    cy.scratch("landing_db_badge", handler);
    cy.on("position bounds", "node[_badge_active]", handler);
    cy.nodes(`[entity_type = "${T.rds}"][?_badge_active]`).forEach(place);
}

/**
 * Playground exception 9: undo the previous run's elevation state, so the layout always sizes the whole interior: the lift
 * is destroyed (the original edges come back), the interior is shown, the derived containment edges are removed.
 */
function _resetElevation(cy) {
    const lift = cy.scratch("landing_lift");
    if (lift) lift.destroy();
    cy.removeScratch("landing_lift");
    // The scope box of the deploy row and the row align track their members; they go before the members move again.
    ["landing_deploy", "landing_row"].forEach((key) => {
        if (cy.scratch(key)) cy.scratch(key).destroy();
        cy.removeScratch(key);
    });
    containedNodes(cy, LIFT_EDGE).outermost.forEach((_top, id) => cy.getElementById(id).removeClass(ELEVATION_HIDDEN_CLASS));
    cy.edges().filter((e) => DERIVED_TYPES.includes(_edgeType(e))).remove();
    // Playground exception 26: the nesting sizes the database as a box, so its solo form is taken off first.
    _formDatabase(cy, cy.nodes(`[entity_type = "${T.rds}"]`), true);
}

/**
 * Playground exceptions 11, 48 and 49 (should become a `flatten` option of a projectNested relationship, and a `via` path of a
 * relationship that walks several edge types): for each ECS container, derived containment edges, read from the official edges and never
 * written to the grid, so the interior nests as container > operating system > programs, beside the library and package piles:
 *   - the container's operating system: the image it runs (RUNS_IMAGE) runs it (RUNS_OPERATING_SYSTEM);
 *   - every program the container runs, directly or through another program (RUNS_PROGRAM), is held by that operating system;
 *   - the libraries those programs load (LOADS_LIBRARY) and the packages the image has installed (INSTALLS_PACKAGE) are held by the container.
 */
function _deriveInterior(cy) {
    const out = new Map();
    cy.edges().forEach((e) => {
        const type = _edgeType(e);
        if (!out.has(type)) out.set(type, new Map());
        const bySource = out.get(type);
        if (!bySource.has(e.source().id())) bySource.set(e.source().id(), []);
        bySource.get(e.source().id()).push(e.target().id());
    });
    const step = (ids, type) => [...new Set(ids.flatMap((id) => (out.get(type) || new Map()).get(id) || []))];
    const closure = (ids, type) => {
        const seen = new Set();
        let frontier = ids;
        while (frontier.length) {
            frontier = step(frontier, type).filter((id) => !seen.has(id));
            frontier.forEach((id) => seen.add(id));
        }
        return [...seen];
    };
    const added = [];
    const add = (source, target, edgeType) => added.push({group: "edges", data: {id: `contains:${source}|${target}|${edgeType}`,
        source, target, edge_type: edgeType, label: edgeType}});
    cy.nodes(`[entity_type = "${T.ecsContainer}"]`).forEach((container) => {
        const image = step([container.id()], E.runsImage);
        const systems = step(image, E.runsOs);
        const programs = closure([container.id()], E.runsProgram);
        systems.forEach((os) => {
            add(container.id(), os, E.containsOs);
            programs.forEach((program) => add(os, program, E.osRunsProgram));
        });
        step(programs, E.loadsLibrary).forEach((lib) => add(container.id(), lib, E.containsLibrary));
        step(image, E.installsPackage).forEach((pkg) => add(container.id(), pkg, E.containsPackage));
    });
    if (added.length) cy.add(added);
}

/**
 * Playground exception 49 (should become the `pile` arrangement of exception 28 with a count chip, in the nested layouts): the members of
 * each derived pile edge of a container are one pile. All but the first (by label) are out of the nesting while it runs, so the box
 * is sized for one card; returns the stack options (tap_viz's applyStack, whose count chip carries the true count) to apply once the
 * scene is positioned.
 */
function _collapseInteriorPiles(cy) {
    const byHolder = new Map();
    cy.edges().forEach((e) => {
        const type = _edgeType(e);
        if (INTERIOR_PILES[type] === undefined) return;
        const key = e.source().id() + "|" + type;
        if (!byHolder.has(key)) byHolder.set(key, {type, members: []});
        byHolder.get(key).members.push(e.target());
    });
    const piles = [];
    byHolder.forEach(({type, members}, key) => {
        members.sort((a, b) => String(a.data("label")).localeCompare(String(b.data("label"))));
        const [representative, ...copies] = members;
        copies.forEach((n) => n.addClass(ELEVATION_HIDDEN_CLASS + " " + STACK_COLLAPSED_CLASS));
        piles.push({members, representative, stackId: INTERIOR_STACK_PREFIX + key, direction: "down-right", offset: INTERIOR_PILE_STEP,
            depthCap: INTERIOR_PILE_DEPTH, chip: true, label: INTERIOR_PILES[type]});
    });
    return piles;
}

/** Playground exception 49: a card or count chip of an interior pile. */
function _interiorStackPart(n) {
    return Boolean(n.data("_is_stack_card") || n.data("_is_stack_chip")) && String(n.data("_stack_id")).startsWith(INTERIOR_STACK_PREFIX);
}

/**
 * Playground exception 48 (same exit as _styleContainer, a per-node display override): the operating-system box is a light blue-grey
 * box with a darker border, so it stands out inside the orange container.
 */
function _styleOs(systems) {
    systems.forEach((n) => n.style({
        "background-color": OS_FILL, "background-opacity": 1, "border-color": OS_BORDER, "border-width": 2, "color": OS_LABEL,
    }));
}

/** A stand-in for the graph that offers only the given nodes to a helper that reads `cy.nodes` and `cy.batch`. */
function _only(cy, nodes) {
    return {batch: (fn) => cy.batch(fn), nodes: () => nodes};
}

/**
 * Playground exception 8 (should become a per-type display hint of the type, and a per-edge-type display hint of tap_viz:
 * width, colour, arrow shape): the application flow's name stands above its icon in dark blue, and its two lines are thick
 * and dark blue, the source line a plain line and the destination line with its arrowhead. Re-applied to a lifted edge, which
 * is a new element.
 */
function _styleFlow(cy, flows) {
    flows.forEach((flow) => flow.style({
        // Playground exception 38: a flow that points up or down has its name beside the circle, so its vertical line does not run through it.
        ...(_flowAngle(flow) % 180 === 0
            ? {"text-valign": "center", "text-halign": "right", "text-margin-x": FLOW_LABEL_GAP, "text-margin-y": 0}
            : {"text-valign": "top", "text-halign": "center", "text-margin-x": 0, "text-margin-y": -FLOW_LABEL_GAP}),
        "color": FLOW_BLUE,
        // Ruled 2026-10-20 (George): no fill behind a flow's name.
        "text-background-opacity": 0,
        // Playground exception 45: a flow's name is one line, never wrapped.
        "text-wrap": "none",
    }));
    _styleFlowEdges(cy);
}

function _styleFlowEdges(cy) {
    cy.edges().forEach((edge) => {
        const type = _edgeType(edge);
        if (type !== E.flowSource && type !== E.flowDestination) return;
        // Arrowhead convention: arrows point from the session initiator (the flow's source) to its target (the flow's destination), so the ONE
        // arrowhead is always on the destination line's target end; `icon_angle` turns only the circle marker's glyph (the way the data moves).
        const head = type === E.flowDestination;
        edge.style({
            "width": FLOW_EDGE_WIDTH, "line-color": FLOW_BLUE, "target-arrow-color": FLOW_BLUE, "source-arrow-color": FLOW_BLUE,
            "target-arrow-shape": head ? "triangle" : "none",
            "source-arrow-shape": "none",
            ...(head ? {"arrow-scale": FLOW_ARROW_SCALE} : {}),
        });
    });
}

/**
 * Playground exception 38: the angle a flow points, in degrees (0 = north, 90 = east, 180 = south, 270 = west), from its `icon_angle`
 * dimension; FLOW_ICON_ANGLE when it has none or it is not a number.
 */
function _flowAngle(flow) {
    const value = Number((flow.data("dimensions") || {})[ICON_ANGLE_KEY]);
    const given = Number.isFinite(value) && (flow.data("dimensions") || {})[ICON_ANGLE_KEY] !== "" ? value : FLOW_ICON_ANGLE;
    return ((given % 360) + 360) % 360;
}

const _flowIconSource = new Map();

/**
 * Playground exception 38: turn each flow's icon to its angle. The icon file points east; the file is read once and wrapped in a rotation
 * about its centre (an SVG used as an image cannot load another file, so the wrapper holds the original's shapes), and the node's `icon_url`
 * becomes that data URI. The original URL is kept in the node's scratch so a second run starts from it. A flow at the default angle, or whose
 * icon cannot be read, keeps its file.
 */
async function _rotateFlowIcons(flows) {
    for (const flow of flows.toArray()) {
        const url = flow.scratch("landingFlowIconUrl") || flow.data("icon_url");
        if (!url || String(url).startsWith("data:")) continue;
        flow.scratch("landingFlowIconUrl", url);
        const turn = _flowAngle(flow) - FLOW_ICON_ANGLE;
        if (turn === 0) {
            flow.data("icon_url", url);
            continue;
        }
        try {
            if (!_flowIconSource.has(url)) {
                const response = await fetch(url);
                if (!response.ok) throw new Error(String(response.status));
                _flowIconSource.set(url, await response.text());
            }
            const text = _flowIconSource.get(url);
            const open = text.match(/<svg[^>]*>/);
            const inner = open ? text.slice(open.index + open[0].length, text.lastIndexOf("</svg>")) : "";
            const box = open && open[0].match(/viewBox="([^"]+)"/);
            const [x, y, w, h] = box ? box[1].split(/[\s,]+/).map(Number) : [0, 0, 80, 80];
            const wrapped = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="${x} ${y} ${w} ${h}">`
                + `<g transform="rotate(${turn} ${x + w / 2} ${y + h / 2})">${inner}</g></svg>`;
            flow.data("icon_url", `data:image/svg+xml;charset=utf-8,${encodeURIComponent(wrapped)}`);
        } catch (_err) {
            flow.data("icon_url", url);
        }
    }
}

/**
 * Playground exception 39 (should become a `label_position: inside` display hint of the program type's revealed form): a program's name is
 * centred inside its box, wrapped to the box's width, at PROGRAM_FONT_FACTOR of the usual size (`_scaleFont` reads the factor).
 */
function _labelProgramsInside(programs) {
    programs.forEach((n) => {
        n.scratch("landingFontFactor", PROGRAM_FONT_FACTOR);
        n.style({
            "text-valign": "center", "text-halign": "center", "text-margin-x": 0, "text-margin-y": 0,
            "text-wrap": "wrap", "text-max-width": `${n.width() * PROGRAM_LABEL_FIT}px`,
        });
    });
}

/**
 * Playground exception 8: the flow stands in the middle of the gap between what lies left of it on the line of sight
 * (the customer's computer) and the product's box, on the line of sight (the root row is already aligned to it).
 */
function _centreFlow(cy, roots, productRoot, flows) {
    if (productRoot.empty()) return;
    const box = (n) => n.boundingBox({includeLabels: false, includeOverlays: false});
    const right = box(productRoot).x1;
    flows.forEach((flow) => {
        const left = roots.filter((n) => n.data("_stage") < flow.data("_stage") && !n.same(flow)).map((n) => box(n).x2);
        if (!left.length) return;
        flow.position({x: (Math.max(...left) + right) / 2, y: flow.position("y")});
    });
}

/**
 * Playground exception 9 (should become the projection's second Elevation, `zoom` = ELEVATION_REVEAL_ZOOM, running the same
 * layout with the interior shown; it is a watcher here because the layout's helpers (the deploy row's scope box, the
 * stacks) are not yet safe to run twice): applies the elevation the zoom is in now, and again whenever the zoom crosses
 * the reveal zoom. Nothing is laid out again, so nothing outside the interior can move or resize.
 */
function _watchElevation(cy, context) {
    const previous = cy.scratch("landing_elevation_watch");
    if (previous) cy.off("zoom", previous);
    let revealed = null;
    let epoch = 0;
    const interiorOf = () => {
        const interior = cy.collection();
        containedNodes(cy, LIFT_EDGE).outermost.forEach((_top, id) => interior.merge(cy.getElementById(id)));
        // What belongs to the interior: its nodes, their type badges and the edges that touch them (not the lifted edge).
        // The piles' collapsed members stay collapsed (exception 49); their cards and count chips are part of the interior.
        const faces = interior.filter((n) => !n.hasClass(STACK_COLLAPSED_CLASS));
        const badges = cy.nodes("[?_is_badge]").filter((n) => faces.some((h) => h.id() === n.data("_badge_host")));
        return faces.union(cy.nodes().filter(_interiorStackPart)).union(badges).union(interior.connectedEdges().not("." + LIFTED_EDGE_CLASS));
    };
    const hide = () => {
        const next = liftEdge(cy, {relationships: LIFT_EDGE});
        next.contained.addClass(ELEVATION_HIDDEN_CLASS);
        // The piles' cards and count chips by style: the elevation class on them re-enters the stack's position handler (tap#304 class).
        cy.nodes().filter(_interiorStackPart).style("display", "none");
        cy.scratch("landing_lift", next);
        _styleFlowEdges(cy);
    };
    const apply = () => {
        const now = cy.zoom() >= ELEVATION_REVEAL_ZOOM;
        if (now === revealed) return;
        const first = revealed === null;
        revealed = now;
        epoch += 1;
        const mine = epoch;
        // Playground exception 15 (should become a `fade` option of an Elevation: its newly shown nodes and edges fade in over
        // the given milliseconds, and out on the way back): a Cytoscape style animation of opacity, never a snap.
        cy.elements().stop(true);
        _placeTaskLabel(cy, now, !first);
        // In one batch: the scope box of the deploy row measures its members on every change, and would recurse otherwise.
        if (now) {
            // The lift goes first: the containment is read from the edges, and the lift hides the original ones.
            cy.batch(() => {
                const lift = cy.scratch("landing_lift");
                if (lift) lift.destroy();
                cy.removeScratch("landing_lift");
                const interior = interiorOf();
                // Shown first (a badge is drawn for what is visible), then faded in from nothing below.
                interior.style("opacity", 1);
                interior.removeClass(ELEVATION_HIDDEN_CLASS);
                interior.removeStyle("display");
                _formDatabase(cy, cy.nodes(`[entity_type = "${T.rds}"]`), true);
            });
            // The container's own type badge: badges are drawn for what is shown when they are applied, and the interior was not.
            _refreshBadges(cy, context);
            const shownNow = interiorOf();
            cy.batch(() => shownNow.style("opacity", 0));
            shownNow.animate({style: {opacity: 1}, duration: FADE_MS, easing: "ease-in-out"});
        } else if (first) {
            hide();
        } else {
            const interior = interiorOf();
            let done = false;
            // The animation ends on every element at the same time; the hide runs once.
            const finish = () => {
                if (done || mine !== epoch) return;
                done = true;
                cy.batch(() => {
                    hide();
                    _formDatabase(cy, cy.nodes(`[entity_type = "${T.rds}"]`), false);
                });
                _refreshBadges(cy, context);
                interior.style("opacity", 1);
            };
            interior.animate({style: {opacity: 0}, duration: FADE_MS, easing: "ease-in-out", complete: finish});
            if (!interior.length) finish();
        }
    };
    cy.scratch("landing_elevation_watch", apply);
    if (REVEAL_ON_ZOOM) cy.on("zoom", apply);
    apply();
}

/**
 * Playground exception 17 (should become an `align` of a nested layout's member to the anchor's line, the `alignTo` of
 * exception 2 applied to the member the application flow ends on): the program the application flow's destination line ends on
 * stands ON the line of sight, so the arrow from the load balancer is horizontal at every elevation (at the account elevation
 * it ends on the task, whose centre is already on the line). The interior (the container and its programs) moves as one by the
 * distance the program is off the line; no box is resized, and the task keeps its centre.
 */
function _alignInteriorToLine(cy, anchor) {
    if (anchor.empty()) return;
    const target = cy.edges().filter((e) => _edgeType(e) === E.flowDestination).map((e) => e.target())
        .find((n) => n.data("entity_type") === T.program);
    if (!target) return;
    const dy = anchor.position("y") - target.position("y");
    if (!dy) return;
    const {outermost} = containedNodes(cy, LIFT_EDGE);
    // Only what the same node holds moves with it: the database's program is not the web task's.
    const holder = outermost.get(target.id());
    outermost.forEach((top, id) => {
        if (top !== holder) return;
        const n = cy.getElementById(id);
        n.position({x: n.position("x"), y: n.position("y") + dy});
    });
}

/**
 * Playground exception 16 (should become: the type badges of a projection follow its elevations, applied again when an elevation
 * shows nodes that were hidden when they were first applied): applyBadgeNodes is the runtime's own pass and is safe to run again;
 * it badges what is shown now, and skips the types the projection excludes (the types whose badges it flagged on its first pass).
 */
function _refreshBadges(cy, context) {
    let exclude = cy.scratch("landing_badge_exclude");
    if (!exclude) {
        exclude = [...new Set(cy.nodes("[?_badge_excluded]").map((n) => n.data("entity_type")))];
        cy.scratch("landing_badge_exclude", exclude);
    }
    const previous = cy.scratch("landing_badge_handle");
    if (previous) previous.destroy();
    cy.scratch("landing_badge_handle", applyBadgeNodes(cy, {excludeTypes: exclude}));
    _moveDatabaseBadge(cy);
}

/**
 * Playground exception 12: the projection adds the type badges after this layout, with a size it derives; once they stand,
 * give them all BADGE_SIZE. A badge is centred on its host's corner, so resizing it keeps it on the corner. The open-findings
 * bubble (a status badge, added later still) is given FONT_SCALE times its font here too (exception 19), and both kinds are
 * sized by the zoom_settle icon class (`_followIconPolicy`, exception 23).
 */
function _pinBadgeSize(cy) {
    const previous = cy.scratch("landing_badge_pin");
    if (previous) cy.off("add", "node", previous);
    let queued = false;
    const handler = (evt) => {
        if (!(evt.target.data("_is_badge") || evt.target.data("_is_status_badge")) || queued) return;
        queued = true;
        setTimeout(() => {
            queued = false;
            cy.nodes("[?_is_status_badge]").forEach(_scaleFont);
            cy.nodes("[?_is_badge]").forEach((n) => n.scratch("landingBadgeBase", BADGE_SIZE));
            _syncBadgeSizes(cy);
        }, 0);
    };
    cy.scratch("landing_badge_pin", handler);
    cy.on("add", "node", handler);
}

/**
 * Playground exception 19 (should become a `font_scale` option of the zoom_settle config, or a larger `normal` label tier):
 * a node's font base is FONT_SCALE times what the runtime gave it. The first size seen is kept in the node's scratch, so a second
 * run of the layout never doubles it again; zoom_settle then takes the doubled size as the element's own base.
 */
function _scaleFont(n, given) {
    if (n.data("_is_badge")) return;
    let base = n.scratch("landingFontBase");
    if (base === undefined) {
        base = given === undefined ? n.numericStyle("font-size") : given;
        if (!(base > 0)) return;
        n.scratch("landingFontBase", base);
    }
    const factor = n.scratch("landingFontFactor") || 1;
    n.style({"font-size": `${base * FONT_SCALE * factor}px`});
    n.dirtyBoundingBoxCache();
}

/**
 * Playground exception 21 (should become a per-elevation label anchor of the Elevation definition): remember where the layout
 * put each web task's label (upper-left, like every container's); the elevation watcher moves it.
 */
function _keepTaskLabel(cy) {
    cy.nodes(`[entity_type = "${T.task}"]`).forEach((n) => n.scratch("landing_task_label",
        {mx: n.numericStyle("text-margin-x"), my: n.numericStyle("text-margin-y")}));
}

/**
 * Playground exception 21: the web task's label is centred in its box at the account elevation (no margin from the centre) and
 * stands upper-left once the interior is shown; it glides between the two over FADE_MS on a change of elevation.
 */
function _placeTaskLabel(cy, revealed, animate) {
    cy.nodes(`[entity_type = "${T.task}"]`).forEach((n) => {
        const upperLeft = n.scratch("landing_task_label");
        if (!upperLeft) return;
        const to = revealed ? upperLeft : {mx: 0, my: 0};
        const style = {"text-margin-x": to.mx, "text-margin-y": to.my};
        if (animate) n.animate({style, duration: FADE_MS, easing: "ease-in-out"});
        else n.style(style);
    });
}

/**
 * Playground exception 23 (should become a `badge` class of the zoom_settle config: status and type badges sized as the icon
 * cards are): the badges are not icon nodes, so zoom_settle leaves their size alone. This sizes them by the same `icon` class
 * (the panel's own band, read from its zoom_settle config) each time the settle mode has written, and when a badge is added.
 */
function _followIconPolicy(cy) {
    const previous = cy.scratch("landing_badge_follow");
    if (previous) cy.off("tapzoomsettled", previous);
    const handler = () => _syncBadgeSizes(cy);
    cy.scratch("landing_badge_follow", handler);
    cy.on("tapzoomsettled", handler);
}

function _syncBadgeSizes(cy) {
    const config = _settleConfig(cy);
    const factor = config ? modelFactor(cy.zoom(), config.classes.icon) : 1;
    cy.batch(() => {
        cy.nodes("[?_is_badge], [?_is_status_badge]").forEach((n) => {
            let base = n.scratch("landingBadgeBase");
            if (base === undefined) {
                base = n.width();
                n.scratch("landingBadgeBase", base);
            }
            n.style({width: base * factor, height: base * factor});
        });
    });
}
