# Rampart 20x Playground GovCloud Landing View Specification

**The first landing-page system visualization for the playground: a TAP / git-serious deployment as it
would run inside AWS GovCloud, drawn at the multi-account elevation, and built only from edges the grid
already holds.**

This file elaborates `req-rampart-20x-playground-page-landing` in `spec-rampart_20x_playground-v0.md`.
That requirement says the first screen is the system visualization; this one says what is on it and where.
It inherits the v0 spec's rules and does not restate them: the plugin ships data only
(`req-rampart-20x-playground-nongoals`), the nodes come from the mock inventory
(`req-rampart-20x-playground-mock-inventory`), and the data is mock; the one authorization boundary the Overview
draws, around the git-serious account, is a drawn scope that claims no authorization
(`req-rampart-20x-playground-nongoals-3`).

## Philosophy

The deployment drawn here is a stand-in for a hosted git-serious service inside a multi-account,
FedRAMP-shaped hosting environment. The hosting environment is built in the `highbar-hosting` project
(criticalsecllc repository); the product is git-serious (unified-systems-com organization).

The view has to be *true to the grid*. Every box is a node the grid holds and every line is an edge the
grid holds. Where the story wants an arrow the grid cannot yet carry, the arrow is **left out and recorded
as a gap** below. It is not drawn from an edge minted for the picture. That rule is the point of the
exercise: the gaps found here are the work list for the plugins that own them, in the same way the v0 spec
turns gaps into findings against the owning plugin and not into code here.

Ruled 2026-10-14: the same applies to nesting. Both the lines and the containment on the page come from official edges
only; explicit data flows are later work, and nothing is drawn or nested to make the picture feel complete.

The view is also the first elevation. A later spec covers zooming into each component (high availability,
subnets and security groups, VPC endpoints and egress). This one fixes only what is on the top view and
leaves hooks for what comes after.

**Provenance markers.**
*Observed* (read from the named source on 2026-10-13, not run): the edge definitions of `aws-core-tap`
(75 edge files on `main`; 10 at the pinned tag `v0.5.0`, commit `d93ca2ee`), `github-core-tap`,
`git-core-tap`, `identity-core-tap` and `computing-core-tap` at their default branches; the AWS
announcement of public Route 53 zones in GovCloud, April 2025.
*Not checked*: the edge definitions of the releases the `demo` record pins for `github_core`, `git_core`,
`identity_core` and `computing_core`; the account list of the `highbar-hosting` project; anything with the
plugins loaded. The implementer verifies each claimed edge with the plugins loaded before relying on it
(`req-rampart-20x-playground-govcloud-grid-true-3`).

## Goals

| # | Name | Description |
| :---: | --- | --- |
| 1 | Three Directions | Customers sit to the left, code and containers come in from the right, and administration from below. All three meet at the product account by position. Lines appear only where an official edge exists (ruled 2026-10-14). |
| 2 | Production-Shaped | The product account looks like a production deployment: DNS, edge protection, a load balancer, containers across availability zones, a highly available database with backups, secrets and keys. |
| 3 | Account Separation | The support accounts are visibly separate from the product account and visibly receive its evidence (logs, findings, backups). |
| 4 | Grid-True | Everything drawn is backed by existing nodes and edges; everything else is a recorded gap. |
| 5 | Zoom-Ready | The top view leaves room for the elevation system to open each component later without redrawing the page. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-govcloud-view | [Landing View](#landing-view) | Proposed | `/playground` opens on a full-page multi-account projection of the git-serious deployment in GovCloud |
| req-rampart-20x-playground-govcloud-layout | [Spatial Layout](#spatial-layout) | Proposed | Customers left, product account centre, deployment path right, support accounts in a row along the bottom, administrator below |
| req-rampart-20x-playground-govcloud-product | [Product Account](#product-account) | Proposed | DNS, edge, load balancer, containers, database, secrets, keys and the deploy system, with the containers at the centre |
| req-rampart-20x-playground-govcloud-deploy | [Deployment Path](#deployment-path) | Proposed | Developer to laptop to GitHub to GHCR to ECR to the deploy step to the containers |
| req-rampart-20x-playground-govcloud-support | [Support Accounts](#support-accounts) | Proposed | Five support accounts in a horizontal row beneath the product account |
| req-rampart-20x-playground-govcloud-admin | [Administrator](#administrator) | Proposed | A representative infrastructure administrator and their computer below the support row |
| req-rampart-20x-playground-govcloud-grid-true | [Grid-True Edges](#grid-true-edges) | Proposed | Every drawn relationship maps to an existing edge; the rest are recorded gaps; the mapping needs an `aws_core` release newer than the pinned `v0.5.0` |
| req-rampart-20x-playground-govcloud-gaps | [Recorded Gaps](#recorded-gaps) | Proposed | The arrows, nodes and edge splits this view needs and the grid does not yet have |
| req-rampart-20x-playground-govcloud-population | [Population](#population) | Proposed | Drawn from the mock inventory bundle, as data, with no code |
| req-rampart-20x-playground-govcloud-actors | [People, Computers And Placement Hints](#people-computers-and-placement-hints) | Proposed | A customer, a developer and an administrator with their computers, placed by two small dimension axes, `actor` and `device` |
| req-rampart-20x-playground-govcloud-deferred | [Deferred To The Zoom View](#deferred-to-the-zoom-view) | Proposed | High availability, egress and endpoints, agents, cross-region backup |

### Landing View
----
RID: `req-rampart-20x-playground-govcloud-view`

Status: `Proposed`

The landing page opens directly into a full-page projection of the whole deployment, at the elevation where
the unit is an AWS account. It needs no scrolling at the demo screen size.

#### Implementation

Built on the tap_viz runtime as data: a projection, arrangements and layout configuration, not new geometry
code. The `create-layout` skill is the entry point: it asks first whether the scene can be expressed as data,
and for this view it should be. It mounts on the `/playground` page of
`req-rampart-20x-playground-page-landing`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-view-1 | Opens On The Projection | Proposed | `GET /playground` renders the multi-account projection with no setup step. | |
| req-rampart-20x-playground-govcloud-view-2 | Fits One Screen | Proposed | The whole view is legible at the demo display size without scrolling or panning. | |
| req-rampart-20x-playground-govcloud-view-3 | Elements Are Navigable | Proposed | Each account and each major component is a clickable element, so a later zoom view has something to attach to. | The zoom itself is out of scope here. |

### Spatial Layout
----
RID: `req-rampart-20x-playground-govcloud-layout`

Status: `Proposed`

The layout expresses the three flows as three directions meeting at the centre.

| Area | Placement |
| --- | --- |
| Customers and their computers | Far left, centred vertically. |
| Product account | Centre of the screen. |
| Route53 | **Upper-left corner of the product account**, so the customer's DNS lookup runs diagonally up and to the right while the main traffic runs horizontally. |
| Main request path | Customer computer, internet gateway, VPC, WAF, load balancer and containers placed left to right on one horizontal line. Position only: no line between them unless an official edge exists. |
| git-serious containers | At the centre of the whole visualization. |
| Deployment path | To the right of the containers, reading right to left toward them. |
| Support accounts | A horizontal row aligned along the bottom edge of the product account. |
| Administrator and computer | Below the support row. |

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-layout-1 | Containers Are Central | Proposed | The git-serious containers sit at the centre of the view. | |
| req-rampart-20x-playground-govcloud-layout-2 | Request Nodes Are Horizontal | Proposed | One horizontal line, left to right: the customer, the customer's computer, the internet gateway, the load balancer, the database (the last three inside the product account, which is inside the authorization boundary). The load balancer is the anchor (ruled 2026-10-19); the gateway is aligned to its line and the customer and their computer are aligned to it, align-only. GitHub, the developer's computer and the developer are not on this line: they stand on the delivery line (`req-rampart-20x-playground-govcloud-layout-22`). | Placement only; lines follow `grid-true`. The order outside the boundary is data: `column` and `row` dimensions on people, computers and the boundary (a compliance_core type with no tagging system), `layout:column` and `layout:order` tags on GitHub; the account, nested in the boundary, carries none. A GitHub node whose tags a later collection batch has overwritten has no column and leaves the line; re-import the mock inventory. |
| req-rampart-20x-playground-govcloud-layout-3 | Route53 Upper-Left | Proposed | Route53 is placed in the upper-left of the product account. | |
| req-rampart-20x-playground-govcloud-layout-4 | Deployment Enters From The Right | Proposed | The deployment path enters the product account from the right. | |
| req-rampart-20x-playground-govcloud-layout-5 | Support Row Along The Bottom | Proposed | The support accounts form one horizontal row along the bottom of the product account. | |
| req-rampart-20x-playground-govcloud-layout-6 | Administrator Below | Proposed | The administrator and their computer hang directly under the bottom-centre of the product account's authorization boundary: the computer's and the person's centres are the account's centre x (the boundary is symmetric about the account), the computer a clear gap (`BELOW_ACCOUNT_GAP`) below the boundary's bottom edge, the person `PAIR_GAP` below the computer. | Ruled 2026-10-19. The pair is the one in the boundary's own column (the product's column is the column of the account's outermost ancestor, found through the nesting), read from the `actor` and `device` dimensions (`req-rampart-20x-playground-govcloud-layout-10`). Playground exception (`req-rampart-20x-playground-nongoals-5`). |
| req-rampart-20x-playground-govcloud-layout-11 | Certificate, Key And Runtime Secret Are Not On The Overview | Proposed | The TLS certificate, the database encryption key and the runtime secret are not drawn on the Overview. They carry no `overview` value, so the Overview's Searches do not select them; they stay on the grid and on the Inventory page. | Ruled 2026-10-19. No node is deleted; the layout holds no code for them. |
| req-rampart-20x-playground-govcloud-layout-8 | Deploy Icons Are One Titled Row | Proposed | The AWS icons of the delivery path (the Terraform state bucket, the Terraform pipeline and the source-puller Lambda, in that order left to right, set by each node's `layout:order` tag; the GitHub App token, the ECR repository, the bundle bucket and the apply and plan CodeBuild projects carry no `overview` value and are not drawn) are half size (`DEPLOY_SCALE` 0.5 of the solo icon) and stand as a card pile at the bottom-right of the product account, below the VPC: each icon `PILE_STEP` model units right and down of the one behind it, back to front in `layout:order` (the state bucket at the back, the pipeline, the source-puller Lambda in front), the pile's right edge inside the account's right padding; only the front icon keeps its name. A subtle titled scope box, `Continuous Delivery` (tap_viz's own), surrounds exactly the pile. A secret is in the row only when it is drawn and a deploy Lambda retrieves it (`RETRIEVES_SECRET_FROM`); none is drawn today. GitHub stays outside the account. | Ruled 2026-10-19; the five hidden nodes ruled 2026-10-20 (the four Searches that pull a far end of a hidden node also filter on `overview`). Ruled 2026-10-20 (George: half size, a card pile, bottom-right of the account, keep the grouping; it was one row before). The account grows downward to hold the pile; edges between two icons of the pile are hidden. Playground exception 28 (`req-rampart-20x-playground-nongoals-5`); exit: a `pile` arrangement of the align/distribute helpers. |
| req-rampart-20x-playground-govcloud-layout-9 | Gateway On The Line | Proposed | The internet gateway's centre is on the load balancer's horizontal line to the pixel. | Ruled 2026-10-19. Playground exception (`req-rampart-20x-playground-nongoals-5`); should become an anchor-relative align of a nested node in the `ranked` natural layout. |
| req-rampart-20x-playground-govcloud-layout-10 | A Person And Their Computer Stand Together | Proposed | A person and their computer are a close pair: one configured gap (`PAIR_GAP`, 28 model units) between their boxes, the same for all three pairs. The people stay where they are; the computer moves toward its person and so away from the account (the customer's computer left, the developer's laptop right, the administrator's workstation down), leaving a clear gap between each computer and the account for the application-flow edge. | Ruled 2026-10-19. The pair is read from the data: a person's `actor` dimension and a computer's `device` dimension carry the same value. Pairs in the same column are vertical. Playground exception (`req-rampart-20x-playground-nongoals-5`); should become the spacing option of the align/distribute helpers. |
| req-rampart-20x-playground-govcloud-layout-12 | The Account Sits In An Authorization Boundary | Proposed | One `compliance_core__compliance_boundary` node, "Authorization Boundary" (`source` the plugin's slug, `source_key` `git-serious`; dimensions `dcom: design`, `overview: shown`, `column: 3`, `row: 0`), and one `SCOPED_TO_COMPLIANCE_BOUNDARY__compliance_core` edge from the git-serious account only. The boundary is the account and everything nested in it; GitHub and the people stand outside it. The layout nests the account in the boundary through a `projectNested` relationship, `(parent:compliance_boundary)<-[:SCOPED_TO_COMPLIANCE_BOUNDARY__compliance_core]-(child:account)`, so no edge is drawn (containment); a Search ("landing scoped") brings the edge in. The boundary is named exactly "Authorization Boundary". Its box is transparent (no fill, so the account and everything in it show unchanged), keeps a bold true-red line (`#dc2626`, 4 units) and carries its `name` as a title centred above the top edge, outside the box. It contains the account and only it, and grows downward with the account for the deploy row. | Ruled 2026-10-19 (Overview Wave 2). Name is the ui session's choice, George may override. No new types. The product's column is the column of the account's outermost ancestor, found through the nesting, never by a type; the boundary growth and look (transparent, red line, outside title) are playground exceptions (`req-rampart-20x-playground-nongoals-5`); should become the `reserve` option applied through the nesting and a per-node display override. compliance_core's default display for the type (pink fill, inside title) is left alone; if the owning plugin's default should change, that is its own decision. aws_core's boundary queries read the same type and edge; the playground's Search is its own node and does not edit theirs. |
| req-rampart-20x-playground-govcloud-layout-13 | The Running Parts Nest | Proposed | Web task a is drawn as the chain task > container > gunicorn > tap-web: an `aws_core__aws_ecs_container` per task (`RUNS_CONTAINER__aws_core`, task to container), gunicorn as `computing_core__program` run by the container and the tap-web program run by gunicorn (`RUNS_PROGRAM__computing_core`, container to gunicorn, gunicorn to tap-web). The layout nests them through three `projectNested` relationships (`task-holds-container`, `container-holds-program`, `program-holds-program`), so the chain is data in the layout's configuration and no edge is drawn for it; Searches ("landing runs-container", "landing runs-program") bring the edges in. The interior is stamped `overview: shown` on web task a only: web task b is the stacked copy of a in the second zone, and its container and programs stay on the grid. Each container holds exactly one set of programs (gunicorn and tap-web per container), and each container reaches the one image host through `RUNS_IMAGE__computing_core`. | Ruled 2026-10-19 (Overview Wave 3; George: the program edge is RUNS_PROGRAM, the container runs gunicorn only). The task, container and gunicorn boxes make web task a larger than its neighbours; the private tier grows with it and the line of sight (`-2`) is unchanged. The first-pass look shows the whole chain; the later elevation lift hides and reveals the interior by these relationships. |
| req-rampart-20x-playground-govcloud-layout-14 | The Application Flow Is Drawn Between The Computer And The Program | Proposed | One `computing_core__application_flow` node ("customer data", dimension `dataclass.customer: data`, keyless, so it carries its own fixed entity id in the application flow bundle) is drawn in its own column between the customer's computer and the boundary, below the line of sight, with its two lines: `APPLICATION_FLOW_SOURCE__computing_core` from the customer's computer to the flow and `APPLICATION_FLOW_DESTINATION__computing_core` from the flow to the gunicorn program of web task a. The flow is not one of the eight nodes of the line of sight. | Ruled 2026-10-19 (Overview Wave 3, first pass; the single collapsible arrow and the lift come later). The flow's place is a playground exception (`req-rampart-20x-playground-nongoals-5`, item 8). |
| req-rampart-20x-playground-govcloud-layout-15 | The Application Flow Has A Click Window | Proposed | A tap on the application flow node opens a window with the node's name, its description and its `dataclass.*` dimension keys and values (today `dataclass.customer`: `data`). It is a node-tap handler in `landing.js`, reads only the node's own Cytoscape data (`label`, `fields.description`, `dimensions`) and makes no network call; it uses the tap_viz info window's CSS classes and dismisses with the close X, ESC or a click outside, one window at a time (opening it closes a status-badge window, and a badge click closes it). | Ruled 2026-10-19 (Overview Wave 7, Q33 and Q36: each flow is stamped with ONE value of `dataclass.customer`). STANDING EXCEPTION (`req-rampart-20x-playground-nongoals-5`, item 7): the host-body tap is reserved for projections (`req-viz-panel-click-semantics`); exit: a projection-declared node info window in tap_viz. |
| req-rampart-20x-playground-govcloud-layout-16 | The Flow Edge Is Lifted And Layered | Proposed | At the account elevation the task's interior is hidden and the application flow's destination line ends on the web task (the edge is lifted onto the outermost node that holds the program, by the configured containment relationships); past the reveal zoom it ends on the gunicorn program. Edges are drawn above the container fills (boundary, account, VPC, subnet, task) and below every leaf node: the load balancer, the internet gateway, the customer, the computers, the flow circle, the database, GitHub and the developer's laptop and developer draw in front of the line, which passes behind them. The flow is a half-size dark-blue circle (`#0B3D91`) centred in the gap between the customer's computer and the boundary, on the line of sight, with a plain source line and an arrowed destination line. | Ruled 2026-10-19. Playground exceptions 8, 9 and 13 (`req-rampart-20x-playground-nongoals-5`); exit for 13: an `edge_layer` option of tap_viz's standard chrome (Cytoscape draws by `z-compound-depth`, then `z-index-compare`, then `z-index`; the standard chrome's edge rule `z-compound-depth: top` puts every edge over every node). The zoom reveal (`REVEAL_ON_ZOOM`) is on: the scope-box recursion is fixed in tap_viz (tap#1077). |
| req-rampart-20x-playground-govcloud-layout-17 | Fonts Scale Per Elevation, Boxes Do Not | Proposed | The interior of the web task is laid out and labelled at 1/2 of the account's sizes (`INTERIOR_SCALE`, the inverse of the ratio between the reveal zoom and the zoom the account is fitted to), so its text is as large on screen at the reveal zoom as the account's text is at the account zoom, and zooming in never resizes the task box or any box around it; the layout is not run again between elevations. Status and type badges keep one size in model units. | Ruled 2026-10-19 (George: relative per-elevation font sizes). Playground exceptions 10 and 12; exit: a per-elevation label and size scale of the Elevation definition and a `badge_size` option of the projection's node style. |
| req-rampart-20x-playground-govcloud-layout-18 | The Revealed Interior Reads Left To Right On The Line | Proposed | Zoomed past the reveal, the interior of web task a shows gunicorn on the LEFT and tap-web on the RIGHT inside the container (the `column` dimension: gunicorn 0, tap-web 1), titled `gunicorn` and `tap-web` (no task suffix; the entity ids are unchanged, so identity does not move). The gunicorn program stands on the line of sight, so the arrow from the load balancer is horizontal at the zoomed-in elevation as at the account elevation, where it ends on the task, whose centre is on the line. The ECS container is a darker orange than the task (fill `#F29B38`, border `#B45309`) and carries its type badge (aws_core's `aws-ecs` icon; the container is no longer in the projection's badge `exclude_types`). The interior fades in when the reveal turns it on and out on the way back. The interior's font sizes do not change (`req-rampart-20x-playground-govcloud-layout-17`). | Ruled 2026-10-19 (George, review of the zoomed Overview). Playground exceptions 15 to 18 (`req-rampart-20x-playground-nongoals-5`); exits: an Elevation `fade`, type badges that follow the elevations, an align of a nested member to the anchor's line, a per-node display override. |
| req-rampart-20x-playground-govcloud-layout-19 | Overview Zoom Polish | Proposed | The Overview's text is twice the runtime's base font (`FONT_SCALE` 2 over the 11 px stylesheet base) and follows the panel's `zoom_settle` font class (exponent 0.5, so 2x at zoom 1, about 1.5x at a 1500 px fit); the data-flow arrowhead was twice the base arrow (now the base arrow, `req-rampart-20x-playground-govcloud-layout-24`); the web task's label is centred in its box at the account elevation and upper-left once the interior is shown; the subnets' labels stand inside their boxes, top-centre, and the two isolated subnets are the `database` tier (tag `tier: database`, label "database ×2"); the open-findings bubble and the type badges are sized by the settle `icon` class (exponent 0.75, band 0.4 to 2.5). | Ruled 2026-10-20 (George, review of the zoomed Overview, points 1, 2, 3, 4, 5). Playground exceptions 19 to 23 (`req-rampart-20x-playground-nongoals-5`); exits: a `font_scale` option of zoom_settle, a per-edge-type arrow-scale hint, a per-elevation label anchor, a `label_position: inside` display hint, a `badge` class of zoom_settle. Terminating the flow at gunicorn is not part of this: it needs an edge replacement the importer cannot do without `grid.delete`. |
| req-rampart-20x-playground-govcloud-layout-23 | Teleport Is A VPC In The Account | Proposed | Teleport is not an account. It is an `aws_core__aws_vpc` named `teleport` that belongs to the git-serious account (`BELONGS_TO_ACCOUNT__aws_core`), partitioned into one `aws_core__aws_subnet` named `public` (`PARTITIONED_INTO_SUBNET__aws_core`, tags `tier: public`, `layout:order: 0`), in which one `aws_core__aws_ec2_instance` named `teleport` resides (`RESIDES_IN_SUBNET__aws_core`); all three carry `dcom: design`, `overview: shown` and the account and region dimensions of their siblings (the instance also `inventory: cloud`, like the load balancer). No `teleport__` node is added: the teleport plugin is vocabulary only. The Overview draws the VPC, its subnet and the instance (a solo icon, in the centre of the subnet) at the centre-bottom of the git-serious account, in the same bottom row as the Continuous Delivery pile and to its left. Which VPC stands there is data: the dimension `place: bottom-center` on the VPC. | Ruled 2026-10-20 (George: 'teleport isn't an account, it's in its own VPC inside the git-serious account'; 'add a subnet named public, place [an EC2 instance named teleport] in solo-icon mode in the center, and position the VPC, nested subnet and teleport icon at center-bottom of the git-serious account'). The `remote-access` placeholder account stays on the grid, not shown. Playground exception 30 (`req-rampart-20x-playground-nongoals-5`); exit: a `slot: bottom-center` of the nested layouts' tiered rows. The instance id and addresses are invented. |
| req-rampart-20x-playground-govcloud-layout-24 | Overview Tweaks, Round Two | Proposed | The data-flow arrowhead is the base arrow (`FLOW_ARROW_SCALE` 1, half of the 2 of `req-rampart-20x-playground-govcloud-layout-19`); a flow's name has no fill behind it; the delivery line (GitHub, the laptop and the developer) runs through the FRONT icon of the Continuous Delivery pile (the source puller), not the middle of the pile, and GitHub stands `GITHUB_SHIFT` model units further right; the Continuous Delivery title is the size of a container title (the settle `font` class applied to the doubled base, right-aligned to its box so it runs left over free space); the `source pull` flow's arrowhead points at the puller (from `req-rampart-20x-playground-govcloud-layout-25` by `icon_angle`, edges unchanged); the subnets' names are `SUBNET_LABEL_FACTOR` (0.6) of the usual size and not bold; the nodes that carry the dimension `label: hidden` (the Route 53 zone, the internet gateway, the load balancer, the source-puller Lambda, and the database at the account elevation; the revealed database box shows its name again) draw no name; the teleport EC2 instance carries the dimension `icon: teleport/icons/teleport-cluster.svg` and is drawn as a bordered logo card like GitHub, still an `aws_ec2_instance` (no `teleport__` node); at the revealed elevation the PostgreSQL program stands on the same horizontal line as gunicorn. | Ruled 2026-10-20 (George, review of the Overview, points 1 to 8). Playground exceptions 31 to 37 and the changes to 20, 28 and 29 (`req-rampart-20x-playground-nongoals-5`); exits: a `label: hidden` display hint, the instance-level icon override (`req-grid-icon-instance`, Backlog in tap_grid, which is why a dimension and not a display icon hint carries the logo), a `label_scale` and `label_weight` hint, a `label_size` option of the scope-box helper, an `arrow: reversed` edge hint, an `align` of a nested member to the anchor's line, a `gap-before` of a named group. The Teleport icon file belongs to the `teleport` plugin (`/static/teleport/icons/`), which must be installed in the stack. |
| req-rampart-20x-playground-govcloud-layout-25 | Overview Nits, Round Three | Proposed | (1) The revealed interior programs (gunicorn, tap-web, the PostgreSQL program) carry their names INSIDE their boxes, centred, at `PROGRAM_FONT_FACTOR` of the usual size and wrapped to the box. (2) The flows' names are `FLOW_FONT_FACTOR` of the usual size and drop "traffic": `customer data` and `database`. (3) The names lose their "a": `customer`, `customer computer`, `developer`, `developer laptop`, `administrator`, `administrator workstation` (name upserts only; entity ids, handles and stable ids are unchanged). (4) The teleport VPC is named `Admin Access`. (5) It is snug around its subnet (`SLOT_PADDING` on the sides and bottom, `SLOT_TOP` above, so the two type badges do not overlap). (6) The `administration` flow ends on the teleport EC2 instance: the original flow (id `01a15a28-7763-727d-9425-a57a6568592e`, destination the boundary, whose endpoints are immutable) is retired by dropping its `overview: shown` dimension, and a NEW flow of the same name (own fixed id, `dataclass.infra: admin`, `icon_angle: 0`) runs from the administrator workstation to the teleport instance. (7) **`icon_angle` convention**: the dimension `icon_angle` of an application flow is a number of degrees, 0 = north / up, 90 = east, 180 = south, 270 = west (default 90). `landing.js` turns the flow's circle icon to it and puts the flow's one arrowhead on the end the angle points to (the destination line's target end when the destination lies on the angle's side of the flow, else the source line's source end). `source pull` and `code` are 270, `administration` 0, `customer data` and `database` 90; `arrow: reversed` is gone. A flow that points up or down has its name beside its circle. (8) The internet gateway is drawn as the load balancer is: a purple card (`#7B5EA7`) with a white glyph, from the playground's own icon `rampart_20x_playground/icons/internet-gateway-card.svg` named by the dimensions `icon` and `icon_form: solo`, above the customer data line. (9) The revealed RDS box is titled `RDS A` (the node's name; `db_instance_id` unchanged), smaller (`DB_TITLE_FACTOR`) and centred at its top; the administrator pair's names are as small as the other pairs'. | Ruled 2026-10-20 (George, Q91a, Q91b and Overview small nits 1 to 8). Playground exceptions 38 to 43 and the changes to 25, 26, 30 and 32 (`req-rampart-20x-playground-nongoals-5`); exits: a per-node `icon_angle` display hint read by the node's icon and its edge types' arrow shape; a `label_position: inside` and `label_scale` display hint; the instance-level icon override with a form chosen by a display hint; a `slot: bottom-center` of the nested layouts. The arrow into the teleport icon no longer crosses the instance's name: `req-rampart-20x-playground-govcloud-layout-26` hides it. |
| req-rampart-20x-playground-govcloud-layout-26 | Compact Admin Access | Proposed | The teleport EC2 instance carries `label: hidden` (its name is not drawn), and its logo card is drawn at the size of the Continuous Delivery icons (`DEPLOY_SCALE` of the solo icon size), not the standard card size. The Admin Access VPC and its `public` subnet are snug around it: the subnet is `SLOT_SUBNET_WIDTH` wide at least, has `SLOT_SUBNET_TOP` of room under its title and `SLOT_NAMELESS_BOTTOM` under the icon (a resident that keeps its name keeps the usual room), and the VPC is `SLOT_PADDING` / `SLOT_TOP` around the subnet as before. Both titles stay readable and the `administration` arrow still ends on the teleport icon, crossing no name. The retired old `administration` flow (id `01a15a28-7763-727d-9425-a57a6568592e`, destination the boundary) also loses its `dataclass.infra: admin` dimension (upsert), so the Data Classification page counts `admin` once (the new flow). | Ruled 2026-10-20 (George: 'hide the name, and shrink the size to match the CD icons ... shrink the subnet and vpc as well'; Q95c yes). Playground exception 44 and the changes to 30, 31, 32 and 43 (`req-rampart-20x-playground-nongoals-5`); exits as for 30, 31 and 32. |
| req-rampart-20x-playground-govcloud-layout-27 | Overview Nits, Round Four | Proposed | (1) The internet gateway's icon is a purple circle with the white glyph and nothing square around it (transparent outside the circle), still a solo icon above the customer data line. (2) The account hugs its content at the account elevation: the room under the Continuous Delivery pile for the front icon's name (`PILE_NAME_ROOM`) is dropped when that name is hidden (`PILE_NAMELESS_ROOM`), so the account, and the boundary around it, have no empty strip under the Admin Access VPC and the pile. (3) The VPC titles (Production, Admin Access) are `VPC_TITLE_FACTOR` (0.8) of the account title's size, between the subnets' (`SUBNET_LABEL_FACTOR`) and the account's, still bold. (4) The Continuous Delivery title has no background. (5) The flow formerly named `developer source code` is named `code` (a name upsert; its id, edges and dimensions do not change). (6) A flow's name is one line (`text-wrap: none`), so `customer data` does not wrap. | Ruled 2026-10-20 (George's six nits). Playground exception 45 (`req-rampart-20x-playground-nongoals-5`); exits as for 25, 28, 33, 34 and 40. |
| req-rampart-20x-playground-govcloud-layout-28 | Overview Nits, Round Five | Proposed | (1) The Route 53 zone icon is `DEPLOY_SCALE` of the solo icon size, like the Continuous Delivery icons, and the account's top room shrinks with it. (2) The Continuous Delivery title is the size of the VPC titles (`VPC_TITLE_FACTOR`). (3) The titles of the account, Production and Admin Access are `TITLE_DARKEN` (0.6) of their own box's border colour (the account's `#B89669` gives `#6E5A3F`, 5.09:1 against its `#EBE1D5` fill; the VPC border `#5A8A4D` gives `#36532E`, 6.17:1 against its `#D0DECD` fill), not black. (4) The Authorization Boundary's title is the size of the VPC titles and keeps its red. | Ruled 2026-10-20 (George's four more nits). Playground exception 46 (`req-rampart-20x-playground-nongoals-5`); exits as for 28, 33, 34 and 44. |
| req-rampart-20x-playground-govcloud-layout-22 | GitHub, The Laptop And The Developer Stand On The Delivery Line | Proposed | GitHub, the developer's laptop and the developer stand, in that order left to right after the authorization boundary, on one horizontal line: the delivery line through the middle of the Continuous Delivery pile (`req-rampart-20x-playground-govcloud-layout-8`), not on the load balancer's line of sight. The laptop and the developer stay a close horizontal pair. Which nodes stand there is data: the dimension `line: delivery` on the people and computers and the tag `layout:line: delivery` on GitHub (a type with a tagging system); the order is the existing `column` dimension and `layout:column` tag. | Ruled 2026-10-20 (George: 'move Github.com, the developer and the developer laptop off the main site-line and line them up instead with the continuous delivery entries'). Playground exception 29 (`req-rampart-20x-playground-nongoals-5`); exit: an `align-to-line` of a named group in the ranked natural layout of the roots. |
| req-rampart-20x-playground-govcloud-layout-20 | Four More Application Flows | Proposed | Four more `computing_core__application_flow` nodes (keyless, `overview: shown`, no `column` dimension) are drawn, each with its `APPLICATION_FLOW_SOURCE` and `APPLICATION_FLOW_DESTINATION` edges: the `database` flow (formerly database traffic) from the tap-web program to the PostgreSQL program (`dataclass.customer: data`); the administration from the administrator's workstation, first to the authorization boundary and, from `req-rampart-20x-playground-govcloud-layout-25`, to the teleport EC2 instance (`dataclass.infra: admin`); the developer's laptop to github.com and the terraform source puller to github.com (both `dataclass.infra: code`). A flow with no `column` is not in the nesting: it is hidden while the nesting runs and then stands in the gap between the two boxes its lines end on (the box that is a child of the lowest holder the two ends share), on the line that joins the ends, as drawn at the account elevation (the web task, not the program in it). The gap between the VPC's columns (`VPC_COLUMN_GAP`) and below the boundary (`BELOW_ACCOUNT_GAP`) is wide enough for a flow's circle and its name. At the account elevation the database traffic's source line is lifted onto the web task and its destination line onto the database. | Ruled 2026-10-20 (George). Playground exception 27 (`req-rampart-20x-playground-nongoals-5`); exit: a `place: between-endpoints` option of the nested layouts. The flows are stamped with ONE value of one `dataclass` sub-axis each (`req-rampart-20x-playground-govcloud-layout-15`). The perimeter is the boundary node, the only node that is the account's outer edge. |
| req-rampart-20x-playground-govcloud-layout-21 | The Database Has Two Forms | Proposed | The PostgreSQL program (`overview: shown`) is joined to the RDS instance by the official `RUNS_PROGRAM__computing_core` edge (the instance runs the program; its source is open in computing_core). At the account elevation the RDS instance is a solo icon and the program is hidden; past the reveal zoom (`ELEVATION_REVEAL_ZOOM`, with the web task's interior) the instance is a standard box of the size the layout reserved (light blue, its name upper-left, its type badge at the TOP-RIGHT corner) with the program drawn inside it. The layout sizes the box once; the two forms are restyles of one node. | Ruled 2026-10-20 (George: "technically it should be the postgres program inside the rds instance; when zooming in change the solo icon to a standard representation with the icon in the top-right and draw the postgres database inside the resulting box"). Playground exception 26; exit: per-elevation node forms in the Elevation definition and a `badge_corner` option. Every other type badge stays upper-left (the runtime's). |
| req-rampart-20x-playground-govcloud-layout-7 | Room For Agents | Proposed | A slot is left beside the developer and beside the administrator for agent actors, left empty for now. | See Deferred. |

### Product Account
----
RID: `req-rampart-20x-playground-govcloud-product`

Status: `Proposed`

The account where git-serious runs. It holds, from the customer side inward:

- **DNS:** a Route53 public hosted zone (public zones are supported in GovCloud as of April 2025, per the AWS announcement linked below).
- **Edge:** an internet gateway on the VPC, AWS WAF in front of the load balancer, an ACM certificate for TLS.
- **Network:** one VPC with public, private and database (isolated) subnet tiers across two availability zones. The load balancer sits in the public tier, the containers in the private tier, the database in the database tier.
- **Containers:** an ECS cluster running the one git-serious service, whose container runs the web server and the task queue together, as the product does today (ruled 2026-10-14: realism for what is deployed; a separate worker service is planned, see Recorded Gaps).
- **Data:** an RDS Postgres instance, Multi-AZ, replacing the database container of a development stack.
- **Secrets and keys:** Secrets Manager secrets the containers read, and KMS keys encrypting the database, the secrets and the logs.
- **Delivery:** an ECR repository and the deploy step (GitHub Actions through an OIDC trust), both inside the account.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-product-1 | Request Path Present | Proposed | The nodes of the request path (internet gateway, VPC, load balancer, ECS service) are shown in order by placement. | Connected only where an official edge exists. |
| req-rampart-20x-playground-govcloud-product-2 | Database Shows HA | Proposed | The RDS instance is shown as Multi-AZ at this elevation, without drawing the standby. | The standby is a zoom-level detail. |
| req-rampart-20x-playground-govcloud-product-3 | Secrets And Keys Shown | Proposed | Secrets Manager and KMS appear in the product account. | |
| req-rampart-20x-playground-govcloud-product-4 | Subnet Tiers Shown | Proposed | The public, private and database (isolated) tiers are visible as containers of their members, nested only through official edges (`HOSTS_SUBNET`, `RESIDES_IN_SUBNET`). | A member without the edge is not nested. |
| req-rampart-20x-playground-govcloud-product-5 | WAF And Certificate Shown | Proposed | A WAF and an ACM certificate appear on the load balancer. | The WAF has no node type yet; see Recorded Gaps. |

#### Future

Public-zone support in GovCloud should be re-checked when the demo environment is stood up; the
announcement is dated 2025.

### Deployment Path
----
RID: `req-rampart-20x-playground-govcloud-deploy`

Status: `Proposed`

Right to left toward the containers: developer, developer's laptop, GitHub.com (repository and workflow run),
GHCR, ECR in the product account, the deploy step, the ECS service. GHCR does not feed production directly:
a FedRAMP-shaped environment mirrors images into its own registry, which is why ECR is on the path.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-deploy-1 | Path Is Complete | Proposed | Every hop from developer to ECS service is shown as a node, in order by placement. | Connected only where an official edge exists. |
| req-rampart-20x-playground-govcloud-deploy-2 | ECR Is On The Path | Proposed | ECR sits between GHCR and the service. | |
| req-rampart-20x-playground-govcloud-deploy-3 | Deploy Lives In The Product Account | Proposed | The deploy step is inside the product account. | Ruled 2026-10-13. |
| req-rampart-20x-playground-govcloud-deploy-4 | Release Pull And Apply | Proposed | In the product account, outside the VPC: a Lambda function that holds a GitHub App token in Secrets Manager copies the Terraform source from GitHub into an S3 bucket; a CodePipeline pipeline with a human approval stage plans and applies it with CodeBuild, and Terraform state sits in a second S3 bucket. | Ruled 2026-10-14. Only the Lambda function, the secret and the two buckets can be drawn today; the pipeline and the build projects wait for `aws_core` types (aws-core-tap#96). |
| req-rampart-20x-playground-govcloud-deploy-5 | Names Are Plain | Proposed | Resource names carry no product prefix, and the product VPC is named Production. | Ruled 2026-10-14. The account, the Route 53 zone and the GitHub names keep theirs. |

### Support Accounts
----
RID: `req-rampart-20x-playground-govcloud-support`

Status: `Proposed`

Five accounts in a row beneath the product account. What each holds will grow as the hosting environment is
built; the first set is:

| Account | Holds |
| --- | --- |
| org / management | AWS Organizations, service control policies, Identity Center |
| security | GuardDuty, Security Hub, Config aggregator, Inspector |
| log archive | CloudTrail organization trail, flow logs, Config delivery, in storage the product account cannot alter |
| backup | AWS Backup vault receiving the database's backups |
| remote-access | Placeholder for Teleport; created now and left empty |

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-support-1 | Five Accounts In A Row | Proposed | The org/management, security, log archive, backup and remote-access accounts appear as one horizontal row. | |
| req-rampart-20x-playground-govcloud-support-2 | Evidence Reaches The Support Accounts | Proposed | The product account sits above the security, log archive and backup accounts, and is connected to them only where an official edge exists. | No flow is drawn for logs, findings or backups; see Recorded Gaps. |
| req-rampart-20x-playground-govcloud-support-3 | Remote-Access Is Named | Proposed | The remote-access account is present and named `remote-access`. | |

### Administrator
----
RID: `req-rampart-20x-playground-govcloud-admin`

Status: `Proposed`

A representative infrastructure administrator and their computer, below the support row. Console and identity
reach the accounts through Identity Center; sessions into the environment go through the remote-access
account. The product account is not reached by direct login.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-admin-1 | Administrator Shown | Proposed | An administrator and their computer appear below the support row. | |
| req-rampart-20x-playground-govcloud-admin-2 | Identity Center Link | Proposed | The administrator is linked toward the org/management account through the identity edges that exist. | The remote-access session path is a recorded gap. |

### Grid-True Edges
----
RID: `req-rampart-20x-playground-govcloud-grid-true`

Status: `Proposed`

Every line on the page is an edge the grid holds. An arrow that would need a new edge is not drawn. Per the
ruling of 2026-10-13, the view starts from the edges that exist, and anything that looks like a flow or an
action modelled as an edge is raised for discussion, not minted. The proposed general mechanism for flows,
the compound edge, is recorded in `tap_grid/specs/spec-grid-edge.md` (Future) in `unified-systems-com/tap`,
proposed in `unified-systems-com/tap#1021` and not yet merged.

Likely backed by existing edge types, from reading the edge definitions of each plugin's default branch.
The last column is the check against the release the `demo` record pins today:

| Drawn relationship | Existing edge | Plugin | In the pinned release |
| --- | --- | --- | --- |
| account contains VPC, subnets | `HOSTS_VPC`, `HOSTS_SUBNET` (from the account region) | aws_core | No: `aws_core` v0.5.0 does not have them |
| load balancer, service, database in a subnet | `RESIDES_IN_SUBNET` | aws_core | No |
| internet gateway on the VPC | `ATTACHED_TO_VPC` | aws_core | No |
| cluster runs the service | `RUNS_SERVICE` | aws_core | No |
| database, secrets, logs encrypted with a key | `ENCRYPTED_WITH_KEY` | aws_core | Yes |
| service writes logs; trail and Config deliver to buckets | `WRITES_LOGS` (being split, see below) | aws_core | Yes |
| Route53 zone points at CloudFront today | `ROUTES_TRAFFIC` (being split, see below) | aws_core | Yes |
| GuardDuty / Security Hub report to the delegated administrator | `REPORTS_TO_ADMINISTRATOR`, `DELEGATES_TO_ACCOUNT` | aws_core | No |
| Identity Center access to accounts | account assignment and permission set edges | aws_core | No |
| repository trusts AWS through OIDC | `FEDERATES_VIA_PROVIDER` | github_core | Not checked |
| repository, workflow, run, package version | `OWNS_REPO`, `DEFINES_WORKFLOW`, `EXECUTES_WORKFLOW`, `BUILDS_PACKAGE_VERSION`, `PUBLISHES_PACKAGE_VERSION` | github_core | Not checked |
| administrator is a person | `HELD_BY_HUMAN` | identity_core | Not checked |

`aws_core` v0.5.0 (commit `d93ca2ee`) declares ten edge types: `ASSUMES_ROLE`, `AUTHENTICATES_VIA_USER_POOL`,
`DIVIDED_INTO_AZ`, `ENCRYPTED_WITH_KEY`, `FEDERATES_INTO_ROLE`, `INVOKES_LAMBDA`, `RETRIEVES_CERT_FROM`,
`RETRIEVES_CONTENT_FROM`, `ROUTES_TRAFFIC` and `WRITES_LOGS` (read from the tag's file listing, not run).
`aws-core-tap` `main` declares 75. So the mapping above holds only on an `aws_core` release newer than
`v0.5.0`, and no such release exists yet. Which release to wait for, and whether the demo record is repinned
to it or to a commit, is open with the maintainer (the pin is the `demo` record's, `req-rampart-20x-playground-boot-2`).

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-grid-true-1 | Every Line Has An Edge | Proposed | Each line in the projection is rendered from an edge in the grid; the projection has no hand-drawn connectors. | |
| req-rampart-20x-playground-govcloud-grid-true-2 | Gaps Are Not Faked | Proposed | A relationship with no edge is absent from the page, not approximated with a different edge type. | |
| req-rampart-20x-playground-govcloud-grid-true-3 | Mapping Is Verified | Proposed | Before population, each row of the table above is confirmed against the loaded plugins, and any row that does not hold is moved to Recorded Gaps. | |
| req-rampart-20x-playground-govcloud-grid-true-5 | Nesting Uses Official Edges | Proposed | Containment on the page (subnet tiers in a VPC, resources in an account) is derived only from official edges; none is nested by position or by a minted edge. | Ruled 2026-10-14. |
| req-rampart-20x-playground-govcloud-grid-true-4 | Pinned Release Has The Edges | Proposed | The `demo` record pins an `aws_core` release that declares every edge in the table marked "No" above; until one does, the lines that need them are not drawn. | Depends on an `aws_core` release that does not exist yet. |

### Recorded Gaps
----
RID: `req-rampart-20x-playground-govcloud-gaps`

Status: `Proposed`

What the view wants and the grid does not yet have. These are inputs to other work and are not built by this
spec.

**Flows (wait for the compound edge, `spec-grid-edge.md` Future in `unified-systems-com/tap`):**

1. Customer computer to the internet gateway and the load balancer (the request path), and the DNS lookup from the customer to Route53.
2. Service to database.
3. Service reading secrets.
4. Image delivery: GHCR to ECR, and ECR to the running service.
5. Database backups to the backup vault.
6. Administrator sessions through remote-access into an account, and a developer's push from a laptop to GitHub.

**Node types missing in aws_core:** AWS Backup (vault and plan), AWS WAF (web ACL). The ACM certificate and
load balancer exist but nothing links a load balancer to its certificate; load balancer to target group to
service is also unmodelled (`ATTACHED_TO_TARGET` and `APPLIES_TO_TARGET` are Organizations and Control Tower
edges). Each is a finding against `aws-core-tap`, not a type created here.

**Edges being split, one specific edge per mechanism** (no previous deployments to support):

- `ROUTES_TRAFFIC` -> `unified-systems-com/aws-core-tap#93`, which includes the new Route53 alias to load balancer edge this view needs.
- `WRITES_LOGS` -> `unified-systems-com/aws-core-tap#92`, which separates function, container, audit-trail and Config delivery.

Until those land the view can use the existing types where they apply.

**Elsewhere:**

- Web-tier high availability: `unified-systems-com/tap#1020` (epic).
- A worker service split from the web container is part of that epic (`unified-systems-com/tap#1016`). It is not drawn until it ships.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-gaps-1 | Gaps Are Tracked | Proposed | Each gap above has a home (an issue, a spec section, or this list), and none is worked around inside the projection. | |
| req-rampart-20x-playground-govcloud-gaps-2 | No Ad Hoc Flow Edges | Proposed | No plugin or instance data mints an edge to stand for a flow while the compound edge is unbuilt. | |

### Population
----
RID: `req-rampart-20x-playground-govcloud-population`

Status: `Proposed`

The accounts, networks, services and people on the page are populated as **data**: nodes and edges of existing
types in `grift/mock-inventory.grift.json` (`req-rampart-20x-playground-mock-inventory`), plus the instance's
page, Searches, panel configuration and layout hints in `grift/pages.grift.json`. This spec adds no bundle and
no code. A gap in a plugin is fixed in that plugin's repository, not worked around here.

The data models a *declared* deployment; it is not read from a live GovCloud environment. It follows the v0
convention: every seeded entity carries `dcom: design`, and the pages are not adjusted to say the data is
mock (ruled 2026-10-13); the presenter says so. When the highbar-hosting environment exists, the same view
is the natural target for real collection.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-population-1 | Data Only | Proposed | Populating the view adds data and configuration, with no new Python in the plugin. | Follows `req-rampart-20x-playground-nongoals`. |
| req-rampart-20x-playground-govcloud-population-2 | Same Convention As The Mock Inventory | Proposed | Every node and edge for the view is in the mock inventory bundle (the running parts of web task a, its programs and the application flow are in the inventory entities and application flow bundles), and every node carries `dcom: design`. | `req-rampart-20x-playground-mock-inventory-2`. |
| req-rampart-20x-playground-govcloud-population-4 | No Collision With Observed Nodes | Proposed | No mock node shares a natural key with an observed node; the mock git-serious repository does not use `unified-systems-com/tap`. | Observed nodes hang findings off that key. |
| req-rampart-20x-playground-govcloud-population-3 | Idempotent | Proposed | Re-running the population produces the same grid, with no duplicate nodes or edges. | |

### People, Computers And Placement Hints
----
RID: `req-rampart-20x-playground-govcloud-actors`

Status: `Proposed`

The view shows the people around the system and their computers: one customer, a developer and an
infrastructure administrator, each with an end-computing device. A computer is a `computing_core` host that
defines a local account (`DEFINES_OS_USER`); the account is held by the person (`HELD_BY_HUMAN`, an
`identity_core` human). The developer's GitHub account is held by the same person. All of it uses edges that
exist; nothing is joined by name.

A human and a host carry no tags, so the layout reads where they go from two small dimension axes this
plugin ships in `grift/dimensions-actors.grift.json`: `actor` on the person and `device` on the computer, each
with the values `customer`, `developer` and `administrator`. They are kept as two axes because a person and
their computer are different things. They carry no access meaning. The row reads left to right: the
customer, the product account's machinery, GitHub, the developer, with the administrator beneath the
organization.

The GitHub side of the deploy path is in the data as `github_core` nodes: the platform, an organization account
and the developer's account, the repository, its workflow and a run, and the container package with a version.
The run builds the version (`BUILDS_PACKAGE_VERSION`); the repository federates into the product account's
GitHub Actions identity provider (`FEDERATES_VIA_PROVIDER`), which stands for the deploy step's trust. There is
no edge from the package version to the ECR repository or from the deploy step to the service, so those hops
are recorded gaps, not lines.

At this view the internet gateway, the load balancer, the database, the people, their computers, the Route 53
zone and the ECR repository are drawn as icon-centric-solo nodes (`spec-viz-icon-node.md` in `tap_viz`): the
icon and the name below it, no card. GitHub is an icon node with a card. An icon node is terminal, so a computer's local account and GitHub's accounts, repository, workflow, runs
and packages are not drawn, and neither are the edges that end in them. They come back when the node is opened
up, which is not built yet.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-actors-1 | People Have Computers | Proposed | The customer, the developer and the administrator each appear with a computer, a local account on it and the human who holds it. | Official edges only. |
| req-rampart-20x-playground-govcloud-actors-2 | Two Axes | Proposed | `actor` is stamped on people and `device` on computers, with the values `customer`, `developer`, `administrator`, as dimension nodes shipped by this plugin. | Ruled 2026-10-14. |
| req-rampart-20x-playground-govcloud-actors-3 | Placement From Facts | Proposed | The row reads customer, the product account's authorization boundary, GitHub, developer, with the administrator beneath the boundary. A person, a computer or the boundary carries its place in the `column` and `row` dimensions (their types have no tagging system); a type that has tags (GitHub) carries `layout:column` and `layout:order`. The layout holds no map from role or type to place. | No placement by label, id or type constant. |
| req-rampart-20x-playground-govcloud-actors-4 | Deploy Path Is In The Data | Proposed | The repository, workflow, run and package version are in the mock inventory, and the repository is joined to the product account's identity provider; the page shows GitHub as one icon node. | Ruled 2026-10-14; the internals are hidden by the icon node, ruled 2026-10-14. |
| req-rampart-20x-playground-govcloud-actors-5 | Mock Repository Is Not Observed | Proposed | The mock repository and accounts use names that no observed node uses, and the page selects only `dcom: design` nodes. | The observed `unified-systems-com/tap` repository stays off the page. |
| req-rampart-20x-playground-govcloud-actors-6 | Top-Most Pieces Are Icon Nodes | Proposed | The internet gateway, the load balancer, the database instance, the people, their computers, the Route 53 zone and the ECR repository are drawn as icon-centric-solo nodes (`solo: true`: the icon and the name, no card), at unchanged positions; GitHub is an icon node with a card; all are selected by entity type and nothing inside them is drawn. | Ruled 2026-10-14; solo for the people, computers, Route 53 and ECR ruled 2026-10-19. |
| req-rampart-20x-playground-govcloud-actors-7 | Running Parts Only | Proposed | The page is named Overview and shows the running parts of the system inside the product account, which stays as their parent: the organization, the other accounts, the ECS cluster and service and the identity provider are not selected by its Searches and stay on the grid. | Ruled 2026-10-14. The URL stays `/playground`. |
| req-rampart-20x-playground-govcloud-actors-8 | What The Page Shows Is Data | Proposed | The Overview's node and edge Searches select on the `overview` dimension value `shown`, stamped on each entity the page draws, and hand-list no entity types. | Ruled 2026-10-14; the Searches that match typed relations keep their types. |

### Deferred To The Zoom View
----
RID: `req-rampart-20x-playground-govcloud-deferred`

Status: `Proposed`

Not part of the top view; recorded so they are not lost.

- **High availability:** two or more web tasks in two availability zones, autoscaling, the database standby. Ruled to a lower zoom level on 2026-10-13. Tracked in `unified-systems-com/tap#1020`.
- **Egress and VPC endpoints:** the private paths to ECR, Secrets Manager and logging, so containers need no route to the public internet. A zoom-level cluster inside the VPC.
- **Agents:** how agents take part in day-to-day operations. They are expected to come in through the same doors as the developer (GitHub) and the administrator (remote-access) and to leave the same audit trail; the layout reserves a slot beside each.
- **Cross-region backup copies** (GovCloud East and West), and the standby database drawn explicitly.
- **Subnets, security groups, IAM roles** as zoomable detail of the VPC.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-govcloud-deferred-1 | Specified Before Built | Proposed | A requirement with ACIDs replaces each bullet before any work on it starts. | |

## Sources

- [Amazon Route 53 adds public authoritative DNS to AWS GovCloud (US) Regions, AWS announcement, April 2025](https://aws.amazon.com/about-aws/whats-new/2025/04/amazon-route-53-public-authoritative-dns-aws-govcloud-us-regions/)
