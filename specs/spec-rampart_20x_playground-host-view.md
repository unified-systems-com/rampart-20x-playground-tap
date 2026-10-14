# Rampart 20x Playground Host View Specification

**The second elevation of the playground's system visualization: zooming from the AWS account view into
the hosts, the containers on them, and the applications and libraries inside, with vulnerabilities
distributed to whatever owns them.**

This file follows `spec-rampart_20x_playground-govcloud-landing.md`, which fixes the account elevation.
It inherits the v0 rules (`spec-rampart_20x_playground-v0.md`): the plugin ships data only
(`req-rampart-20x-playground-nongoals`), the nodes and edges are fabricated for the demo from existing types
(`req-rampart-20x-playground-mock-inventory`), and every seeded entity carries `dcom: design`.

## Philosophy

The account view shows services as single boxes joined by single lines. The host view opens those boxes. A
viewer zooming into the ECS service sees the Fargate task, the container nested in it, and the TAP
application nested in the container as its primary program, with the network interfaces, open ports and
filesystem that belong to the host. A viewer zooming into the database sees the PostgreSQL instance.

The same zoom redistributes vulnerabilities. At the account elevation every finding on the web service sits
on the service. At the host elevation each finding moves to the most specific thing that owns it: the
container's base operating system packages, the TAP application, a Python library, the hand-built OpenSSL
FIPS provider. The totals do not change as the viewer zooms; only the place they sit does. That invariant is
checked on the page (`req-rampart-20x-playground-host-rollup`).

The nodes and edges do not exist in the grid yet. They are fabricated for the demo from the types that exist;
where a type or edge is missing, the gap is filed against the plugin that owns it and the view waits for the
release, the same rule as the account elevation.

**Provenance markers.**
*Observed* (read from the named source on 2026-10-14, not run): the models and edges of `computing-core-tap`
(v0.5.0), `aws-core-tap` (`main`), `compliance-core-tap` (`main`), `github-core-tap` (`main`) and
`fedramp-20x-ksi-tap` (`main`); the 71 open code-scanning alerts of `unified-systems-com/tap`; the tap_viz
specs for elevation, nesting and nested projection; the Gryphon multi-hop and aggregation spec; `Dockerfile`
and the `bump-openssl-fips` skill.
*Designed* (this spec's own claims, unbuilt and untried): every requirement below.

## Goals

| # | Name | Description |
| :---: | --- | --- |
| 1 | Zoom Opens The Boxes | Zooming from the account elevation reveals the task, container, application, libraries, interfaces, ports and filesystem of each host, nested in the box they belong to. |
| 2 | Findings Follow Ownership | Vulnerabilities sit on the most specific owner the data supports, and move deeper as the viewer does. |
| 3 | The Numbers Add Up | The count at any elevation equals the sum of what sits beneath it, and the page shows the check. |
| 4 | Compliance Core Only | Findings use `compliance_core` types and edges; `fedramp_20x_ksi` is not used yet. |
| 5 | Gaps Go To Their Owner | A missing type or edge is filed against the owning plugin, and nothing is minted here. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-host-view | [Host Elevation](#host-elevation) | Proposed | Zoom from the account view into hosts, with containers and applications nested |
| req-rampart-20x-playground-host-web | [Web Container](#web-container) | Proposed | The TAP web service on Fargate: task, container, application, OpenSSL provider, interfaces, ports, filesystem, secret mount |
| req-rampart-20x-playground-host-db | [Database Host](#database-host) | Proposed | The RDS PostgreSQL instance and its port and interface |
| req-rampart-20x-playground-host-findings | [Findings And Owners](#findings-and-owners) | Proposed | Findings attach to the most specific owner; the database carries none |
| req-rampart-20x-playground-host-rollup | [Roll-Up And Check](#roll-up-and-check) | Proposed | Counts roll up along the nesting chain; the page shows that they add up |
| req-rampart-20x-playground-host-attribution | [Version Attribution](#version-attribution) | Proposed | Scan results attach to the running build through version information carried as tags on the ECS deployment |
| req-rampart-20x-playground-host-compliance-core | [Compliance Core Only](#compliance-core-only) | Proposed | Which types the findings use, and where `fedramp_20x_ksi` duplicates them |
| req-rampart-20x-playground-host-gaps | [Recorded Gaps](#recorded-gaps) | Proposed | Types, edges and flows the view needs and the grid lacks |
| req-rampart-20x-playground-host-population | [Population](#population) | Proposed | Fabricated nodes and edges, with the findings dataset |

### Host Elevation
----
RID: `req-rampart-20x-playground-host-view`

Status: `Proposed`

The host elevation is the second elevation of the same projection as the account view. It becomes active at a
deeper zoom threshold and expands as the viewer zooms; the account-level structure stays visible around it.

#### Implementation

An Elevation entity in the landing projection, composing a layout whose module configures `projectNested`
(`spec-viz-elevation.md`, `spec-viz-nested-projection.md`). The layout declares the whole nesting chain for
the elevation, not just the new levels, and lists each level as a single-hop relationship over edges the grid
holds. Nesting is single-parent: each node is placed in exactly one box. Elevation switching is scene-wide in
v1, so crossing the threshold opens every host at once; per-host expansion is not available. The additive
elevations requirement of the viz spec is Approved for Development and not yet Implemented, so the first use
of it here is expected to expose defects. `create-layout` is the entry point for the layout.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-view-1 | Expands On Zoom | Proposed | Zooming past the elevation threshold from the account view shows the contents of the hosts, with the account view still visible around them. | |
| req-rampart-20x-playground-host-view-2 | Nesting From Edges | Proposed | Every nested placement comes from an edge or shared dimension the grid holds; none is hand-placed. | |
| req-rampart-20x-playground-host-view-3 | One Parent Each | Proposed | No node is placed in two boxes; the nesting resolver reports no multiple-parent or cycle warning on the demo data. | |

### Web Container
----
RID: `req-rampart-20x-playground-host-web`

Status: `Proposed`

The TAP web service, as deployed on ECS Fargate. Nested from the outside in:

- the ECS cluster and service (account-elevation nodes), and the Fargate task;
- the container, a `computing_core` host of kind `container`, running a Wolfi-based image;
- the TAP application, the container's primary program;
- the libraries and operating system packages the application and container use, including the hand-built
  OpenSSL FIPS provider as its own program-level item with its own story (see below);
- the host internals: the network interface and the address it uses, the open port, and the filesystem and
  mounted volumes;
- the secret mount and the secrets it carries, shown by name only. Secret values are never displayed.

The secret is pulled from AWS Secrets Manager. The pull itself is a flow and is not drawn until the compound
edge exists (`req-rampart-20x-playground-govcloud-gaps`).

**The OpenSSL FIPS provider.** TAP compiles the OpenSSL FIPS provider from pinned upstream source in a
dedicated build stage, installs the resulting module into the image, and activates it by editing the system
OpenSSL configuration; CPython, `cryptography` and `libpq` run against the same OpenSSL line, and the
application refuses to start if a FIPS self-check fails. The host view shows the provider as a separate item
from the operating system's own OpenSSL, because it is separate software with its own version, build and
findings. The relationships that tie it to the configuration file and to its consumers depend on gaps filed in
`req-rampart-20x-playground-host-gaps`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-web-1 | Chain Is Nested | Proposed | The service, task, container and application appear nested in that order. | |
| req-rampart-20x-playground-host-web-2 | Application Is Primary | Proposed | The TAP application is shown as the container's primary program. | |
| req-rampart-20x-playground-host-web-3 | OpenSSL Provider Separate | Proposed | The FIPS provider is a distinct node from the operating system's OpenSSL library. | |
| req-rampart-20x-playground-host-web-4 | Interface, Address, Port | Proposed | The container shows its network interface, the address the interface uses, and the open port. | Needs the host-internals edges. |
| req-rampart-20x-playground-host-web-5 | Filesystem And Volumes | Proposed | The container shows its filesystem and mounted volumes. | Needs the filesystem slice. |
| req-rampart-20x-playground-host-web-6 | Secret Mount By Name | Proposed | The secret mount and the secret names appear; no secret value is read, stored or shown. | |

### Database Host
----
RID: `req-rampart-20x-playground-host-db`

Status: `Proposed`

The database is an RDS PostgreSQL instance. Its host view shows the database instance, its engine and version,
and its open port and network interface where the existing types can express them. There is no container for
the database in this deployment.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-db-1 | Instance Shown | Proposed | The RDS instance appears with engine and version at the host elevation. | |
| req-rampart-20x-playground-host-db-2 | Port Shown If Expressible | Proposed | The open port and interface appear if existing types and edges can express them; if not, they are recorded as a gap, not approximated. | |

### Findings And Owners
----
RID: `req-rampart-20x-playground-host-findings`

Status: `Proposed`

A finding attaches to the most specific node that owns it. At the account elevation the owner shown is the web
service; at the host elevation it is one of: a base operating system package, the TAP application, a Python
library, or the OpenSSL FIPS provider. The database instance carries no findings, and the dataset contains none.

The real scanner output for `unified-systems-com/tap` shows the shapes to expect. Of 71 open alerts on
2026-10-14, 39 are against the web image (26 Trivy, 13 Grype), 30 against the database image (17 Trivy, 13
Grype) and 2 are SonarCloud code findings. The web image's findings fall on base packages (`glibc`,
`ld-linux`, `libcrypt1`, `python-3.14`, `gosu`), one Python library (`oauthlib`) and the OpenSSL FIPS
provider (Grype, declared through the supplemental SBOM). The 30 database-image alerts are dropped from the
dataset.

#### Implementation

Each finding is one generic `compliance_core__compliance_finding` with its detail node behind it, the shape
the sibling requirement `req-rampart-20x-playground-dependabot-pull-5` fixes: a `github_core`
`code_scanning_alert` linked by `DETAILS_FINDING__github_core`. The owner carries the finding through
`CARRIES_COMPLIANCE_FINDING__compliance_core`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-findings-1 | Most Specific Owner | Proposed | Each finding is carried by the most specific node the data identifies, and by no other. | A finding that cannot be pinned deeper stays on the container. |
| req-rampart-20x-playground-host-findings-2 | Database Carries None | Proposed | No finding in the dataset is carried by the RDS instance or by anything nested in it. | |
| req-rampart-20x-playground-host-findings-3 | Account View Shows The Service Total | Proposed | At the account elevation the web service shows the count of every finding beneath it. | See the roll-up requirement. |

### Roll-Up And Check
----
RID: `req-rampart-20x-playground-host-rollup`

Status: `Proposed`

Counts roll up along the same nesting chain the layout declares, so the layout's relationships say which node
a finding rolls into. Each elevation shows, on each box, the count of findings on it and on everything nested
in it, and the page shows a check that the count at the top equals the sum of the leaves plus anything not
pinned deeper.

#### Implementation

Gryphon first, projection code as the fallback (ruled 2026-10-14). From the multi-hop and aggregation spec
(read, not run): fixed-length multi-hop `MATCH` patterns, `COUNT` with implicit grouping, `NOT EXISTS` and
`OPTIONAL MATCH` are implemented; `COUNT` is the only aggregate, there is no `UNION`, and variable-length
paths are rejected. So one query per depth of the chain can count the findings carried at that depth, with
`NOT EXISTS` excluding findings covered by an active exception; the sum across depths and the equality check
are done in the projection module. If a depth cannot be expressed, that count moves into the module and the
reason is recorded here.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-rollup-1 | Totals Do Not Change | Proposed | The total finding count is the same at every elevation. | |
| req-rampart-20x-playground-host-rollup-2 | Check Is Visible | Proposed | The page shows the check that a parent's count equals the sum of its children's counts plus findings carried by the parent itself. | |
| req-rampart-20x-playground-host-rollup-3 | Gryphon First | Proposed | Each count is a Gryphon query unless this requirement records why it is computed in the projection module. | |
| req-rampart-20x-playground-host-rollup-4 | Failure Is Loud | Proposed | A mismatch is shown as a failed check, not hidden or corrected. | |

### Version Attribution
----
RID: `req-rampart-20x-playground-host-attribution`

Status: `Proposed`

A scan result attaches to a running component by name and version. The running build's identity is carried as
tags on the ECS deployment: the image name, the application version and, where useful, the commit. Until the
exact running versions can be collected, the values are set by hand (ruled 2026-10-14), and the tags are the
hook a real deployment would use in the field.

The scan rows (read 2026-10-14) carry the image in their `environment` field (`{"image":"tap-web"}`) and a
`category` such as `trivy-tap-web`; the package name, installed version, fixed version and CVE are in the
message text and the rule. They also carry a `commit_sha`, but it is the commit of the scan, and the two tools
scanned different commits (the Grype alerts one, the Trivy and SonarCloud alerts another), so the commit is not
a single join key for this data. The image name and package name and version are.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-attribution-1 | Tags Carry The Build | Proposed | The ECS deployment node carries tags for image name and application version, and a commit when one is needed. | Hardcoded for now. |
| req-rampart-20x-playground-host-attribution-2 | Match By Name And Version | Proposed | A finding attaches to the component whose name and version match the scan's package name and installed version, within the image the scan names. | |
| req-rampart-20x-playground-host-attribution-3 | Unmatched Stays Up | Proposed | A finding with no matching component stays on the container, and counts as unpinned in the check. | |

### Compliance Core Only
----
RID: `req-rampart-20x-playground-host-compliance-core`

Status: `Proposed`

At this stage the findings use `compliance_core` only. `fedramp_20x_ksi` is not used until vulnerability
detection and response analysis is performed; no `fedramp_20x_ksi` node or edge type appears in the host view
or its data.

`compliance_core` (read 2026-10-14) provides `compliance_finding`, `compliance_exception`,
`compliance_evidence`, `compliance_boundary`, `compliance_context` and `compliance_artifact`, with the edges
`CARRIES_COMPLIANCE_FINDING`, `COVERS_COMPLIANCE_FINDING`, `CITES_COMPLIANCE_EVIDENCE`,
`CONCERNS_COMPLIANCE_CONTROL` and `SCOPED_TO_COMPLIANCE_BOUNDARY`. Its finding is deliberately thin: name,
summary, description, open or resolved. Severity, CVE and dates live on the detail node.

**Duplication with `fedramp_20x_ksi`, recorded for resolution:**

| `fedramp_20x_ksi` | `compliance_core` | Overlap |
| --- | --- | --- |
| `vdr_finding` | `compliance_finding` | Both are a finding with a title, description and status; `vdr_finding` adds PAIN, SLA and KEV fields. |
| `AFFECTS_RESOURCE` (finding to resource, wildcard target) | `CARRIES_COMPLIANCE_FINDING` (any source to finding) | The same fact in opposite directions. |
| `vdr_finding.resource` (string) | the carrying edge | A name where `compliance_core` has an edge. |

The playground's own v0 spec still builds its mock findings and VDR reports page on `fedramp_20x_ksi` types
(`req-rampart-20x-playground-mock-findings`, `req-rampart-20x-playground-page-vdr-reports`). That is
unchanged by this file and outside the host view; it is where the tension will surface.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-compliance-core-1 | No Ksi Types | Proposed | The host view's data contains no `fedramp_20x_ksi__*` node and no edge from that plugin. | |
| req-rampart-20x-playground-host-compliance-core-2 | Duplicates Recorded | Proposed | Each overlap found between `fedramp_20x_ksi` and `compliance_core` is listed in the table above. | |

### Recorded Gaps
----
RID: `req-rampart-20x-playground-host-gaps`

Status: `Proposed`

What the host view needs and the grid does not have. Each is filed against its owner; none is worked around
here.

| Gap | Filed |
| --- | --- |
| Host to interface (`CONTAINS_NETWORK_INTERFACE`), interface to address (`USES_IP_ADDRESS`), `OPENS_PORT`, `LISTENS_ON_PORT`, `RUNS_PROGRAM` | `unified-systems-com/computing-core-tap#32` |
| `package` and `library` node types; `INSTALLS_PACKAGE`, `LINKS_LIBRARY` and the OpenSSL provider's relationships | `unified-systems-com/computing-core-tap#33` |
| `filesystem` and `storage_volume`; `MOUNTS_FILESYSTEM`, `CONTAINS_FILE` | `unified-systems-com/computing-core-tap#34` |
| ECS service to task, task to container, task to secret | `unified-systems-com/aws-core-tap#95` |
| The pinned `aws_core` release lacks most of its own edges | `req-rampart-20x-playground-govcloud-grid-true-4` |

Flows wait for the compound edge: the pull of a secret from Secrets Manager, the connection from the load
balancer to the container, and the container's connection to the database.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-gaps-1 | Each Gap Has An Issue | Proposed | Every row above links an open issue or a requirement. | |
| req-rampart-20x-playground-host-gaps-2 | Nothing Minted Here | Proposed | No type or edge is created in this repository to fill a gap. | `req-rampart-20x-playground-nongoals`. |

### Population
----
RID: `req-rampart-20x-playground-host-population`

Status: `Proposed`

The nodes and edges of the host view are fabricated for the demo, from existing types, in the mock inventory
bundle. The findings dataset is derived from the real scanner rows for `tap`, with the 30 database-image
alerts dropped, and held as data. No code is added to the plugin.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-host-population-1 | Existing Types | Proposed | Every fabricated node and edge uses a type declared by an installed plugin; a missing type waits for its release. | |
| req-rampart-20x-playground-host-population-2 | Design Axis | Proposed | Every fabricated entity carries `dcom: design`. | `req-rampart-20x-playground-mock-inventory-2`. |
| req-rampart-20x-playground-host-population-3 | No Database Findings | Proposed | The dataset holds no alert from the database image. | |
| req-rampart-20x-playground-host-population-4 | Data Only | Proposed | Populating adds data and configuration, with no Python. | |

## Sources

- `unified-systems-com/computing-core-tap#32`, `#33`, `#34`; `unified-systems-com/aws-core-tap#95`
- `tap_viz/specs/spec-viz-elevation.md`, `spec-viz-nested-projection.md`, `spec-viz-nesting.md` in `unified-systems-com/tap`
- `tap_grid/specs/spec-grid-gryphon-multihop-aggregation.md` in `unified-systems-com/tap`
