# Rampart 20x Playground Plugin Specification

**A data-only TAP instance plugin that puts a mocked FedRAMP 20x story on the grid — a TAP deployment
designed for AWS GovCloud, its inventory, its vulnerabilities, and VDR reports of vulnerabilities against
remediation SLAs — so the approach to Vulnerability Detection and Response (and later Key Security
Indicators) can be shown on screen.**

## Plugin Identity

| Field | Value |
| --- | --- |
| Slug | `rampart_20x_playground` |
| Display name | TAP Rampart 20x Playground |
| Description | A data-only instance plugin: the keystone, mocked GovCloud inventory and findings, and the pages that show a deployment design, an inventory, vulnerabilities and VDR reports. |
| Kind | Instance (anchor) plugin, data only — consumes `identity_core`, `administrivia`, `dcom`, `aws_core`, `computing_core`, `github_core` (with `git_core`), `compliance_core`, `fedramp_20x_ksi` and `rampart_20x`; consumed by nothing. |

**Default dimensions.** Not applicable: the plugin owns no TAP-managed types (`req-rampart-20x-playground-nongoals`).
The page and panel nodes it seeds are core entities and carry core's defaults. Entities seeded by the two
data bundles carry `dcom: design`, per the convention in `req-rampart-20x-playground-mock-inventory`; pages,
panels, Searches and the keystone carry no `dcom` value (ruled 2026-10-13). Inventory items also carry one
`inventory` value (`req-rampart-20x-playground-dimensions`).

## Philosophy

The playground exists to make one argument visible: that a FedRAMP 20x VDR process is a query over a
graph, not a spreadsheet. It is a "make it work" artefact for a podcast demo, built from the models that
already exist, so the pieces get on the board before anyone decides where more vocabulary should live.

It follows `git_serious_double_tap`: an instance plugin holds only what is specific to the instance — which
pages, over which data, in what arrangement — and every capability a second instance would want is built
in the plugin that owns the concept (the `*_core` substrates, `fedramp_20x_ksi`, `rampart_20x`, `tap_viz`,
`tap_web`) by reviewed PR and then used from here as data. v0 builds the whole demo, including the
vulnerabilities-against-SLA view, inside the playground as seed bundles, Searches, pages and panel
configurations. When a VDR ranking process arrives it is expected to need its own plugin; where it lives is
decided then, not now. Compliance vocabulary — exceptions in particular — is expected to grow in
`compliance_core`; the playground consumes what lands there.

The inventory and findings are **mock data**. They are never presented as collected. The design draws one
authorization boundary, around the git-serious account (ruled 2026-10-19; it supersedes the earlier "never an
authorization boundary" wording); it is a drawn scope, and no authorization is claimed. The presenter says the data is
mock; the pages and panels are not adjusted to say it (ruled 2026-10-13).

**Provenance markers.**
*Observed* (read from the named source on 2026-10-13, not run): `fedramp_20x_ksi` v0.3.1 `vdr_finding`
carries `pain`, `internet_reachable`, `likely_exploitable`, `is_kev`, `remediation_sla_days` and
`remediation_due_at`; `github_core` declared `code_scanning_alert` and no Dependabot model (v0.12.2); *Observed* again 2026-10-14: v0.13.0 declares `dependabot_alert` (released from `github-core-tap#68`);
`rampart-20x-tap` and `highbar-tap` carry no release tags; `tap` had 48 Dependabot alerts (2 open) and 71 open code scanning alerts (43 Trivy, 26 Grype, 2 SonarCloud).
*Documented* (a spec says so): `dcom` stamps through default dimensions on types a plugin owns
(`req-dcom-inheritance`); an instance plugin composes by edge and ships no vocabulary
(`req-git-serious-double-tap-scope`).
*Designed* (this spec's own claims, unbuilt and untested): every route, page arrangement, seed bundle,
the demo boot record's passkey loading.

## Goals

| # | Name | Description |
| :---: | --- | --- |
| 1 | Show The Approach | A viewer sees a GovCloud deployment design, its inventory, its vulnerabilities and their SLA position without being told how the graph works. |
| 2 | Data Only | Everything the playground ships is bundles, Searches, pages, panel configurations, tags and layout hints. |
| 3 | Pieces On The Board | Use the models that exist now; gaps become findings against the plugin that owns the concept, not code here. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-nongoals | [v0 Non-Goals](#v0-non-goals) | Proposed | No models, edges, collectors or code; no live AWS; mock data, one drawn boundary |
| req-rampart-20x-playground-boot | [Boot Records](#boot-records) | Proposed | The in-package `ci` record and a demo record, every plugin pinned by commit SHA, local passkeys |
| req-rampart-20x-playground-keystone | [Keystone](#keystone) | Proposed | One keystone node: project name and description |
| req-rampart-20x-playground-dimensions | [Dimensions](#dimensions) | Proposed | Twenty-six dimension nodes: ten `inventory` (the axis and nine categories) and sixteen `dataclass` (the axis, three branches and twelve values) |
| req-rampart-20x-playground-mock-inventory | [Mock Inventory](#mock-inventory) | Proposed | Mocked GovCloud resources from existing `aws_core` / `computing_core` types, on the `design` position |
| req-rampart-20x-playground-mock-findings | [Mock Findings](#mock-findings) | Proposed | Mocked `vdr_finding` and `vdr_report` rows carrying PAIN, SLA and due date |
| req-rampart-20x-playground-dependabot-pull | [Dependabot Pull](#dependabot-pull) | Proposed | One-off pull of `tap`'s Dependabot alerts, via a new model in `github-core-tap`; shapes the finding entry |
| req-rampart-20x-playground-page-landing | [Landing Page](#landing-page) | Proposed | Opens on the system visualization: the GovCloud design as a graph |
| req-rampart-20x-playground-page-inventory | [Inventory Page](#inventory-page) | Proposed | System inventory |
| req-rampart-20x-playground-page-vulnerabilities | [Vulnerabilities Page](#vulnerabilities-page) | Proposed | Four cards, three charts and three searchable tables, each row drilling in to a CVE page that explains one vulnerability or a component page |
| req-rampart-20x-playground-page-data-classification | [Data Classification Page](#data-classification-page) | Proposed | An introduction, one card per data classification key, each describing the classification and its values and counting components by value and entity type, and under the cards the four classification-mapping tables |
| req-rampart-20x-playground-classification-mapping | [Classification Mapping](#classification-mapping) | Proposed | The mapping of entity types to the data classifications they should carry, held in four Searches, and the hourly snapshot of its summary |
| req-rampart-20x-playground-inventory-coverage | [Inventory Coverage](#inventory-coverage) | Proposed | Responsibility and data classification coverage by inventory category, a row of four live status cards and, below it, one line chart over time on each page: responsibility on the inventory page, data classification on the Data Classification page |
| req-rampart-20x-playground-coverage-seed | [Coverage History Seed](#coverage-history-seed) | Proposed | Mock data: the stamps that bring the coverage figures to a high end state, and four days of snapshots, every four hours, that climb to it |
| req-rampart-20x-playground-coverage-panel | [Coverage Panel](#coverage-panel) | In Development | The coverage figures and both histories in one plain report panel on the landing page |
| req-rampart-20x-playground-page-reporting | [Reporting Page](#reporting-page) | Proposed | The overall status report: an agency part and, below a cut line, an internal part, as two plain print-ready `report` panels |
| req-rampart-20x-playground-teams | [Teams And Responsibility](#teams-and-responsibility) | Proposed | Four teams (three under `git-serious`), a generic roster, and a `team.responsible` stamp on the systems each team answers for |
| req-rampart-20x-playground-page-teams | [Teams Page](#teams-page) | Proposed | The teams, their leaders and their members, under the teams graph |
| req-rampart-20x-playground-teams-viz | [Teams Graph](#teams-graph) | Proposed | A full-width graph at the top of the Teams page: each person (a solo icon) inside their team, each team inside its parent, the child teams in a row, the people of a team stacked with the leader first |
| req-rampart-20x-playground-teams-parent-column | [Parent Team Column](#parent-team-column) | Backlog | The Teams table's parent team column, blocked on a Gryphon left-outer join that returns the optional side's fields |
| req-rampart-20x-playground-component-team | [Responsible Team On The Component Page](#responsible-team-on-the-component-page) | Backlog | A `Responsible Team` line in the component page's hero, blocked on reading a dimension value and joining it to a team |
| req-rampart-20x-playground-teams-findings | [Findings By Responsible Team](#findings-by-responsible-team) | Backlog | Open findings grouped by the team answerable for the component that carries them |
| req-rampart-20x-playground-ownership-coverage | [Ownership Coverage](#ownership-coverage) | Backlog | The share of entities with a `team.responsible` stamp, by the mapping runners |
| req-rampart-20x-playground-pain-profiles | [Program Stamps And Reach](#program-stamps-and-reach) | Proposed | The profile stamp for each program (a node and an edge), the `RUNS_PACKAGE` root packages, and the two PAIN Searches that name the `stackarmor_vdr` runners |
| req-rampart-20x-playground-page-pain | [PAIN Page](#pain-page) | Superseded | PAIN for every finding on every owner (program or container), and each asset's roll-up of its programs' profiles |
| req-rampart-20x-playground-page-vdr-reports | [VDR Reports Page](#vdr-reports-page) | Proposed | VDR reports: vulnerabilities against SLA |
| req-rampart-20x-playground-page-internals | [Web And DB Internals Page](#web-and-db-internals-page) | Backlog | TAP's web and db applications, internal processing |
| req-rampart-20x-playground-page-dataflows | [Data Flow Pages](#data-flow-pages) | Backlog | Management, user interaction and deployment flows |
| req-rampart-20x-playground-page-ksi | [KSI Page](#ksi-page) | Backlog | KSI implementation view |
| req-rampart-20x-playground-ranking | [VDR Ranking](#vdr-ranking) | Backlog | Ranking process; likely its own plugin |

### v0 Non-Goals
----
RID: `req-rampart-20x-playground-nongoals`

Status: `Proposed`

The playground contributes no TAP-managed entity types: no models, no edges, no collectors, no panel
types, and no Python beyond what the plugin package requires to install. It makes no AWS calls and holds no
credential other than the local passkey login. It draws one authorization boundary around the git-serious account,
as data (a compliance_core boundary node and one scoped-to edge); it claims no authorization for it.

#### Implementation

The manifest declares no `[models]` or `[edges]`. `pyproject.toml` lists no dependencies and the
manifest's `depends_on` is empty, because nothing here imports another plugin's Python and the two bundles
written so far use core entity types only; the composed plugins are installed by the `demo` record, not by
pip resolution (the `dcom` shape, whose `ci` record installs itself alone). When the mock inventory and
findings land they seed other plugins' types by string, which is a vocabulary dependency, so `depends_on`
gains those plugins (with a `note`) in the same change (`new-plugin` Tier 1b). The one permitted code path is a programmatic JavaScript
layout, written through the `create-layout` skill, if a page cannot be drawn from data.

**Standing exception (George, 2026-10-19, the "make it work" phase).** Custom tweaks are permitted in the
playground's layout JavaScript (`landing.js` and its sibling modules), and only there. This relaxes, for the
playground only, the part of the `create-layout` skill that says a plugin layout module holds configuration and no
helper. It does not touch the Python, vocabulary or data rules: no Python, vocabulary declared in its owning
plugin, data through GRIFT, no placement by label, id or type constant. Each tweak is marked in a comment as a
"playground exception" and names the tap_viz runtime form it should become. Exit: fold into tap_viz when the
concepts settle; the tweaks then become runtime configuration and the markers are removed.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-nongoals-1 | No Vocabulary | Proposed | `manage.py plugins` reports `models=0/0 edges=0/0` for the plugin. | |
| req-rampart-20x-playground-nongoals-2 | No Network | Proposed | The plugin's `ci` record contains no collector and no credential, and boots offline. | |
| req-rampart-20x-playground-nongoals-3 | Mock Data, One Drawn Boundary | Proposed | The keystone description says the data is mock, that no authorization has been granted, and that the design draws one authorization boundary around the git-serious account; its `authorization_boundary` context flag is true. | Ruled 2026-10-19 (Overview Wave 2); replaces "Mock Is Not A Boundary". The boundary is a `compliance_core__compliance_boundary` node in the mock inventory (`req-rampart-20x-playground-govcloud-layout-12`). |
| req-rampart-20x-playground-nongoals-4 | No Dcom On App Entities | Proposed | The keystone, page, panel and Searches seeded by this plugin carry no `dcom` key. | The axis describes the system under design, not the app showing it. |
| req-rampart-20x-playground-nongoals-5 | Layout Tweaks Are A Marked Exception | Proposed | Custom geometry exists only in the playground's layout JavaScript, each tweak is marked "playground exception" with the runtime form it should become, and this spec records the exit: fold into tap_viz when the concepts settle. | Ruled 2026-10-19. Today: the deploy row's members and room, the gateway's alignment, the person-computer pairs and the wait before the scope box is drawn and the boundary's growth with the account (`req-rampart-20x-playground-govcloud-layout-8`, `-9`, `-12`), the application flow's place below the line of sight and its click window, a node-tap handler reading the node's own data (`-14`, `-15`; Overview Waves 3 and 7). Each remains marked in `landing.js` with the tap_viz form it should become. Overview Wave 8 adds the edge lift and the two elevations (9), the interior's font and size scale (10), the pinned badge size (12) and the edge layering (13), `req-rampart-20x-playground-govcloud-layout-16`, `-17`; Wave 9 adds the interior's fade (15), the type badges applied again at the reveal (16), the program on the line (17) and the container's colour (18), `-18`. Overview zoom polish adds the text base size (19), the data-flow arrowhead size (20), the web task label per elevation (21), the subnet labels inside the box (22) and the badges following the settle icon class (23), `req-rampart-20x-playground-govcloud-layout-19`. The database's two forms (26) and the placing of the flows that are not ranked (27) are `req-rampart-20x-playground-govcloud-layout-20` and `-21`; the delivery pile (28) and the delivery line (29) are `-8` and `-22`; the slotted teleport VPC (30) is `-23`. Overview nits, round three adds a flow's `icon_angle` direction (38), the interior programs' names inside their boxes (39), the flows' smaller names (40), the database title (41), the gateway drawn as its own card (42) and the snug Admin Access VPC (43), `req-rampart-20x-playground-govcloud-layout-25`. The compact Admin Access VPC and its half-size nameless logo card are 44, `req-rampart-20x-playground-govcloud-layout-26`. Overview nits, round seven adds the Wolfi OS box laid out by hand (51), the flows' colour by the data they carry (52), the pile window (53) and the badge removal when the interior is hidden again (54), `req-rampart-20x-playground-govcloud-layout-32` to `-35`. |

### Boot Records
----
RID: `req-rampart-20x-playground-boot`

Status: `Proposed`

Two records ship in the package. `ci` is the reserved name (`req-boot-bootstrap-ci-record`): the stack the
plugin's own tests run in. `demo` is the stack George boots on screen.

#### Implementation

`tap_plugin/rampart_20x_playground/boot/ci.boot.json` installs the plugin and the plugins whose Python it
imports (none), and seeds only this plugin's bundles plus the dependency bundles its pages mount.
`boot/demo.boot.json` installs `identity_core`, `administrivia`, `dcom`, `aws_core`, `computing_core`,
`github_core` (with `git_core`), `compliance_core`, `fedramp_20x_ksi` (v0.4.2), `fedramp_20x_vdr`,
`vuln_mosaic` (v0.6.0), `rampart_20x` and this plugin, and seeds, in dependency order, `administrivia`,
`dcom`, the `dimension` bundle of `aws_core`, `computing_core` and `fedramp_20x_ksi`, the `ksi_schedule`
bundle of `fedramp_20x_ksi` (the KSI catalog collector, hourly at minute 17), `vuln_mosaic` (its refresh
Schedule, hourly at minute 41) and this plugin; those plugins' pages, regions and KSI seed stay out until a
page mounts them. `vuln_mosaic` is in the demo record because the CVE page mounts its panel; it is still not
a `depends_on` entry of this plugin (nothing here imports it) and the `ci` record does not carry it. Its
operator settings (`settings.json`) and wanted-ids file are files on the operator's filesystem, not grid
data, and no boot step type writes them, so a fresh stack starts on vuln_mosaic's defaults with an empty
wanted list until the operator sets them; the record cannot declare them. Every plugin is pinned by the **peeled commit SHA** beside its
tag (`git ls-remote <url> 'refs/tags/<tag>*'`, the `^{}` line). `rampart_20x` has no tag, so it is pinned
by the SHA of its `main` at the time the record is written, and the record says so in a `note`. This
plugin's own entry pins its release tag (`v0.1.0`), which the release script cuts after the scaffold merges:
a record cannot carry the commit that introduces it, and the validator exempts a self entry from `commit`
only when `rev` is its own release tag. Until then a development spawn uses a copy of the record whose self
entry names a branch. Login uses the local passkey that `spawn-session.sh` replays into the stack
(`req-tap-auth-passkey-dev-bootstrap`); the record carries no passkey setting.
Okta, Duo and Teleport are not in either record.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-boot-1 | CI Record Present | Proposed | `boot/ci.boot.json` exists, is named `ci`, and is declared under `[[boot.records]]` with its `sha256`. | |
| req-rampart-20x-playground-boot-2 | Pinned By Commit | Proposed | Every `install.plugins` entry in `demo` carries a 40-hex commit SHA that equals the `^{}` line of its tag, or, for `rampart_20x`, the `main` SHA with an "untagged" note. | A tag-object SHA is a defect. |
| req-rampart-20x-playground-boot-3 | Demo Boots And Logs In | Proposed | `spawn-session.sh <label> --from <demo record>` stands up healthy, and a locally stored passkey logs in. | Designed; not yet tried. |
| req-rampart-20x-playground-boot-4 | No Excluded Plugins | Proposed | Neither record installs `okta`, `duo`, `teleport` or `highbar`. | |
| req-rampart-20x-playground-boot-5 | Installed In Dependency Order | Proposed | In `demo`, every entry comes after the sibling plugins its distribution requires (for example `compliance_core` and `git_core` before `github_core`). | Each entry is installed on its own, so an unmet sibling dependency aborts pre-boot. Proved by booting the record. |
| req-rampart-20x-playground-boot-6 | Vuln Mosaic In The Demo | Proposed | `demo` installs `vuln_mosaic` at v0.6.0 pinned by its peeled commit and seeds it before this plugin; the manifest's `depends_on` and the `ci` record do not name it. | Ruled 2026-10-21. Settings and wanted ids are operator files and are not declared by the record. |
| req-rampart-20x-playground-boot-7 | KSI Catalog Hourly | Proposed | `demo` pins `fedramp_20x_ksi` at v0.4.2 and seeds its `ksi_schedule` bundle before this plugin, and the record's description names the three hourly schedules and their egress hosts without claiming more. | Ruled 2026-10-21. |

### Keystone
----
RID: `req-rampart-20x-playground-keystone`

Status: `Proposed`

A small GRIFT bundle seeds one `keystone` node, the first thing anyone landing cold reads.

#### Implementation

`grift/keystone.grift.json`: `name` is `rampart-20x-playground`; `description` is the plugin's purpose and
the mock-data statement of `req-rampart-20x-playground-nongoals-3`; `context_json` and
`context_schema_json` start minimal, per `tap_grid/specs/spec-grid-keystone.md`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-keystone-1 | One Keystone | Proposed | `MATCH (k:keystone) RETURN k` returns exactly one node on a booted `demo` stack. | |

### Dimensions
----
RID: `req-rampart-20x-playground-dimensions`

Status: `Proposed`

Two axes of dimension nodes, created up front: `inventory`, which sorts what the inventory page lists into
seven categories, and `dataclass`, which classifies kinds of data. Both follow `dcom`'s pack shape
(`req-dcom-naming`): flat `dimension` nodes, no edges, the hierarchy carried by the dotted name. They live in
this plugin for now, as the "build it all here, break it out later" phase allows; `inventory` and `dataclass`
are neutral keys that more than one plugin could use, so extraction into a vocabulary plugin is expected
(ruled 2026-10-13, Q4a).

**The `inventory` axis** (descriptions as given by the owner):

| Node | Label it defines | Meaning |
| --- | --- | --- |
| `inventory` | axis | The category an inventory item belongs to. |
| `inventory.applications` | `inventory: applications` | Applications: running applications inside the environment. |
| `inventory.libraries` | `inventory: libraries` | Libraries: software libraries. |
| `inventory.packages` | `inventory: packages` | Packages: packages a package manager installed, one row per ecosystem, name and version. |
| `inventory.os` | `inventory: os` | Operating Systems. |
| `inventory.containers` | `inventory: containers` | Containers: container images, one row per class of identical image. |
| `inventory.crypto` | `inventory: crypto` | Crypto: cryptographic implementations found in the deployment's artifacts, with the reviewed decision about each. |
| `inventory.secrets` | `inventory: secrets` | Secrets: secret material, keys, certificates, secrets. |
| `inventory.cloud` | `inventory: cloud` | Cloud Services: internal AWS capabilities such as Route 53, Secrets Manager, IAM and VPCs that come from the cloud but are not an application, library, OS or container. |
| `inventory.saas` | `inventory: saas` | Third-Party SaaS: interconnected cloud systems, including AWS where all of this is hosted and GitHub where the code comes from. |

**The `dataclass` axis.** Names as given by the owner; the meanings are this spec's proposal and are for review.

| Node | Label it defines | Meaning (proposed) |
| --- | --- | --- |
| `dataclass` | axis | The class of data an item holds or handles. |
| `dataclass.customer` | axis (child) | Data that belongs to customers. |
| `dataclass.infra` | axis (child) | Data that belongs to running the infrastructure. |
| `dataclass.customer.data` | `dataclass.customer: data` | Customer data. |
| `dataclass.customer.creds` | `dataclass.customer: creds` | Customer credentials. |
| `dataclass.customer.logs` | `dataclass.customer: logs` | Customer logs. |
| `dataclass.customer.sanitized` | `dataclass.customer: sanitized` | Customer data that has been filtered to remove untrusted content. |
| `dataclass.infra.code` | `dataclass.infra: code` | Infrastructure code. |
| `dataclass.infra.secrets` | `dataclass.infra: secrets` | Infrastructure secrets. |
| `dataclass.infra.logs` | `dataclass.infra: logs` | Infrastructure logs. |
| `dataclass.infra.admin` | `dataclass.infra: admin` | Infrastructure administration: administrator access to the infrastructure. |
| `dataclass.action` | axis (child) | What an item does with data: holds it at rest, works on it, or moves it. |
| `dataclass.action.store` | `dataclass.action: store` | Data at rest: the item persists data (a volume, an instance's storage, a bucket). |
| `dataclass.action.process` | `dataclass.action: process` | Data in process: the item computes on data (a program, a container, a function). |
| `dataclass.action.transmit` | `dataclass.action: transmit` | Data in flight: the item carries data between places (an application flow). |
| `dataclass.action.none` | `dataclass.action: none` | The item is present but does nothing with data: it neither holds, works on nor moves it. |

**The `dataclass.action` axis (ruled 2026-10-20, George).** `customer` and `infra` say *what kind* of data; `action`
says *what the item does with it*, in the three states data can be in: at rest (`store`), in process (`process`) and in
flight (`transmit`). It replaces the earlier `dataclass.customer.reader`, `.writer` and `.storage` values, which mixed a
component's role into the kind-of-data axis; those three nodes are removed. The axis is independent of the other two and
takes **one value per entity**: nothing is both a processor and a store. A fourth value, `none`, is the acknowledged "nothing": a component that is on the host but does not touch data (a text editor installed on a server, where a cryptographic library is `process`). It is a stamp like the others, `dataclass.action = none`, and it is different from an entity with no `dataclass.action` key at all, which means not yet observed. (Ruled 2026-10-20, George.) The rule that makes this hold is that persistence
belongs to the thing that persists, not to the program in front of it. A cache is a program that `process`es; the disk
holding its output `store`s. A database is a program that `process`es; its volume `store`s. So an item that stores and
computes is modeled as two items, or carries the value of what it is, never both. `transmit` applies to application flows
and any other flow where data is in transit. `read` and `write` were not kept: they are directions of a flow, not states of
data.

By `req-dcom-naming` the label a value node defines is everything before its last dot as the key, and the last
segment as the value, so an entity can carry one `dataclass.customer` value, one `dataclass.infra` value and one
`dataclass.action` value.
That rule says names deeper than axis-and-value "carry no defined meaning"; `dataclass` is two levels deep, so
it leans on that undefined territory. That is flagged for the `dcom` owner's review and is not decided here. The nodes exist so
classification needs no vocabulary change; the entities stamped with a `dataclass` value are those named in
`req-rampart-20x-playground-dimensions-8` and the application flows' existing `customer` and `infra` stamps.

**The `sanitized` value (ruled 2026-10-20, George).** `dataclass.customer.sanitized` is customer data that has been filtered to remove untrusted content, which matters for VDR processing later. It is a value of `dataclass.customer`, one of the existing single-valued kinds of data, not a dotted refinement such as `data.sanitized`. The only item stamped with it is the flow from the web application to the database, the one place the demo's customer data is filtered before storage.

**Stamping (ruled 2026-10-20, George).** The mock data has no volume entity, so the RDS instance stands in for the
database's volume.

| Item | Value |
| --- | --- |
| The five stamped `computing_core__application_flow` rows (customer data, database, administration, code, source pull; the retired administration flow stays unstamped) | `dataclass.action: transmit` |
| The `database` application flow (web application to the PostgreSQL program) | `dataclass.customer: sanitized`, replacing its `data` stamp |
| The five `computing_core__program` rows and the two `aws_core__aws_ecs_container` rows | `dataclass.action: process` |
| The `aws_core__aws_rds_instance` and the two `aws_core__aws_s3_bucket` rows | `dataclass.action: store` |

Anything not listed stays unstamped, which is "not observed", not a claim of `none`.

**Inventory category of the containers and buckets (ruled 2026-10-21, George).** The two `aws_core__aws_ecs_container` rows and the two `aws_core__aws_s3_bucket` rows are cloud services and carry `inventory: cloud`, the category the RDS instance and the other AWS types already carry. They carried no `inventory` value, and grouped coverage (`req-compliance-core-dimension-mapping-18`) counts only entities that carry the group key, so they were in no chart line and no Summary row. The inventory page's Cloud Services table lists them once stamped.

#### Implementation

`grift/dimensions.grift.json`, one batch of twenty-six `inventory` and `dataclass` `dimension` nodes (ten `inventory`, sixteen `dataclass`),
no edges. Each carries `tap.meta: dimension` and no `dcom` value (dictionary nodes carry no axis value,
`req-dcom-stamping` rule 6). Entity ids are minted once with `scripts/uuid7` and never change. Every node and
the batch carry a description. Queries use the bracketed key form, `n.dimensions["inventory"]`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-dimensions-1 | Twenty-Six Nodes | Proposed | Importing the bundle yields exactly twenty-six `inventory` and `dataclass` `dimension` nodes, with the names in the two tables above. | Was twenty-three: the action axis (five nodes: the branch and four values) and `sanitized` (one) were added and the reader, writer and storage values (three) removed. |
| req-rampart-20x-playground-dimensions-2 | Inventory Enumerates | Proposed | `MATCH (d:dimension) WHERE d.name STARTS_WITH "inventory." RETURN d` returns exactly the nine category nodes. | |
| req-rampart-20x-playground-dimensions-3 | No Dot In A Value | Proposed | No value node's last segment contains a dot. | Same constraint as `req-dcom-naming-3`. |
| req-rampart-20x-playground-dimensions-4 | Dictionary Carries No Axis Value | Proposed | None of the twenty-six nodes carries an `inventory`, `dataclass` or `dcom` key; each carries `tap.meta: dimension`. | |
| req-rampart-20x-playground-dimensions-5 | Every Node Described | Proposed | Every node and the batch has a non-empty description. | |
| req-rampart-20x-playground-dimensions-6 | Action Axis Enumerates | Proposed | `MATCH (d:dimension) WHERE d.name STARTS_WITH "dataclass.action." RETURN d` returns exactly the four value nodes `store`, `process`, `transmit` and `none`. | |
| req-rampart-20x-playground-dimensions-7 | Role Values Removed | Proposed | No node named `dataclass.customer.reader`, `dataclass.customer.writer` or `dataclass.customer.storage` is in the bundle, and no entity in the seed data carries those values. | The three nodes are removed from this plugin's seed and purged from any live grid that holds them. Purge approved by George 2026-10-20 (relayed by rampart-pg); the importer cannot delete, so the purge is a separate sanctioned step. |
| req-rampart-20x-playground-dimensions-8 | Action Stamping | Proposed | Each item in the stamping table carries exactly its `dataclass.action` value, and no other item in the seed carries one except the rows the coverage seed stamps (`req-rampart-20x-playground-coverage-seed-1`). | The RDS instance stands in for the database volume. Ruled 2026-10-20 (George). |
| req-rampart-20x-playground-dimensions-9 | One Action Per Entity | Proposed | No seed entity carries more than one `dataclass.action` value, and no seed entity carries a `dataclass.action.<value>` key. | The key is `dataclass.action`; the value is one of the three. |
| req-rampart-20x-playground-dimensions-10 | Sanitized Value | Proposed | The bundle holds the node `dataclass.customer.sanitized` with the description in the table above, and the `database` application flow carries `dataclass.customer: sanitized` and no `data` stamp; the `customer` application flow still carries `data`. | Replaces the unspecced `data.filtered` idea. |
| req-rampart-20x-playground-dimensions-11 | None Is A Declared Value | Proposed | `dataclass.action.none` is in the bundle with a description, so an entity stamped `dataclass.action = none` is counted as declared by `dimension-coverage`; no seed entity is stamped `none` yet. | The value exists so libraries and packages that do nothing with data can be marked. A missing key is still "not observed". |
| req-rampart-20x-playground-dimensions-12 | Containers And Buckets Are Cloud Services | Proposed | The two `aws_core__aws_ecs_container` rows and the two `aws_core__aws_s3_bucket` rows each carry `inventory: cloud`, and the Cloud Services table of the inventory page lists them. | Ruled 2026-10-21 (George). They were counted in no coverage category before. |

### Mock Inventory
----
RID: `req-rampart-20x-playground-mock-inventory`

Status: `Proposed`

A seed bundle of mocked AWS GovCloud resources — the account, a GovCloud region and zones, and the compute,
network and database resources a TAP deployment needs — drawn only from node and edge types that already
exist in `aws_core` and `computing_core`. A resource that needs a type that does not exist is a finding
against the owning plugin, not a type created here.

#### Implementation

`grift/mock-inventory.grift.json`. The nodes sit on the `dcom` `design` position (convention below).
`aws_core` v0.5.0 and its handling of the `aws-us-gov` partition were not exercised in drafting.

A mock node must not share a natural key with an observed node. The grid holds the real
`unified-systems-com/tap` repository (the Dependabot findings hang off it), so a mock git-serious repository takes a
different `full_name`.

**Convention (ruled by George, 2026-10-13).** Every entity seeded through one of this plugin's two data
bundles (`mock-inventory`, `mock-findings`) carries `dcom: design` in its `dimensions`, written per entity in
the GRIFT batch. This is the playground's own convention for seeded entries, not the type-default stamping
`req-dcom-inheritance` describes, since the plugin owns no types. `aws_core` does not stamp `dcom` (ruled), so
on those nodes the per-entity value is the only one. Untried: how the grid merges the value with a type
default that says otherwise, and whether `fedramp_20x_ksi` stamps `dcom` on its types (not checked).

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-mock-inventory-1 | Existing Types Only | Proposed | Every mock node's `entity_type` is declared by an installed plugin's manifest; the bundle imports with no unknown-type warning. | |
| req-rampart-20x-playground-mock-inventory-2 | On The Design Axis | Proposed | Every mock inventory node carries `dcom: design` and none carries another `dcom` value. | Per-entity convention above; `aws_core` stamps nothing, so no merge is in play. |
| req-rampart-20x-playground-mock-inventory-3 | GovCloud Region | Proposed | At least one mock region is a GovCloud region (`us-gov-east-1` or `us-gov-west-1`). | |
| req-rampart-20x-playground-mock-inventory-4 | One Category Or None | Proposed | Every mock inventory item carries exactly one `inventory` value from the seven categories; a node that fits none (for example pure topology) carries no `inventory` key. | The mapping of existing `aws_core`, `computing_core` and `github_core` types to categories was not checked. A category with no existing type (libraries is the likeliest) is a finding for the owning plugin. |

### Mock Findings
----
RID: `req-rampart-20x-playground-mock-findings`

Status: `Proposed`

A seed bundle of mocked `vdr_finding` and `vdr_report` rows, attached to the mock inventory, with enough
spread in severity, reachability, KEV status and age that the SLA view has something to show.

#### Implementation

`grift/mock-findings.grift.json`, using `fedramp_20x_ksi`'s `vdr_finding` and `vdr_report` as they are.
Findings fill `pain`, `internet_reachable`, `likely_exploitable`, `is_kev`, `first_detected`,
`remediation_sla_days` and `remediation_due_at`. At least
one finding past its due date and one comfortably inside it, so both sides of "vulnerabilities against
SLA" appear.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-mock-findings-1 | Existing Types Only | Proposed | Every row is a `fedramp_20x_ksi__vdr_finding` or `fedramp_20x_ksi__vdr_report`; the bundle imports clean. | |
| req-rampart-20x-playground-mock-findings-2 | Both Sides Of SLA | Proposed | The seed holds at least one finding past `remediation_due_at` and one not yet due, on a fixed reference date stated in the bundle. | A fixed date keeps the demo repeatable. |
| req-rampart-20x-playground-mock-findings-3 | On The Design Axis | Proposed | Every mock `vdr_finding` and `vdr_report` carries `dcom: design` and no other `dcom` value. | Same convention; merge with any `fedramp_20x_ksi` default untried. |

### Landing Page
----
RID: `req-rampart-20x-playground-page-landing`

Status: `Proposed`

The first screen is the system visualization, not the keystone: a layout of the GovCloud deployment design,
drawn as a graph of the mock inventory. Later versions add zooming into other elevations and layouts of the
same system; those are not v0 and are not yet requirements (ruled 2026-10-13).

#### Implementation

Route `/playground`. What the projection shows and where is elaborated in
`spec-rampart_20x_playground-govcloud-landing.md`. One `page` node mounting existing panel types by `USES_PANEL`
edge, one Search over the mock inventory, and a projection through `create-layout` if the arrangement needs one.
Lines and nesting in the projection come only from official edges the grid holds; no edge is minted to draw a
flow (ruled 2026-10-14). Graph chrome is
`node_style: icon-badge`. Links to the three pages below. The page does not mount the keystone.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-landing-1 | Route Serves | Proposed | `GET /playground` returns 200 on a booted `demo` stack and renders the design graph. | |
| req-rampart-20x-playground-page-landing-2 | Official Edges Only | Proposed | Every line and every nesting in the projection is rendered from an edge type declared by an installed plugin; none is invented for the picture. | Ruled 2026-10-14. Explicit data flows are later work. |

### Inventory Page
----
RID: `req-rampart-20x-playground-page-inventory`

Status: `Proposed`

The system inventory, in nine categories: applications, libraries, packages, operating systems, containers, crypto, secrets,
cloud services and third-party SaaS. Each category is a section listing the items stamped with that
`inventory` value, each row linking to its entity page, except the crypto section, which lists one row per cryptographic provider (`req-rampart-20x-playground-page-inventory-9`). The columns and row rules of each table are in
`spec-rampart_20x_playground-inventory.md`.

#### Implementation

Route `/playground/inventory`; above the tables, a row of four coverage cards and one coverage chart, `Responsibility Coverage` (`req-rampart-20x-playground-inventory-coverage`); nine Searches, one per `inventory` value, each filtering on
`n.dimensions["inventory"]`; an existing table panel per section.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-inventory-1 | Route Serves | Proposed | `GET /playground/inventory` returns 200 and renders nine sections, one per `inventory` category. | The page as built has nine tables (packages and crypto were added after this row was written). |
| req-rampart-20x-playground-page-inventory-2 | Section Matches Dimension | Proposed | Each section lists exactly the entities whose `inventory` value is that section's category, except crypto (`-9`). | |
| req-rampart-20x-playground-page-inventory-3 | Data Classification Column | Proposed | Every table on the page except Crypto ends with one joined column titled `Data Classification` (width 200) that reads the node's `dataclass.customer`, `dataclass.infra` and `dataclass.action` dimensions by `field_paths`, joined with `, `, with `empty_text: not classified`, so no cell is blank. | Ruled 2026-10-20 (George, Q90a, then nit 9). Replaces the two `Customer data` and `Infra data` columns. Uses the Table panel's `field_paths`, `joiner` and `empty_text` column options. |
| req-rampart-20x-playground-page-inventory-4 | Title Case Headings | Proposed | Every table's panel name and column titles are in Title Case (`Cloud Services`, `Operating Systems`, `Third-Party SaaS`). | Ruled by George. |
| req-rampart-20x-playground-page-inventory-5 | Icon Column, No ID Column | Proposed | Every table's first column is `Icon`, an `entityType` column (`show: icon`) over `entity_type`: the glyph is the type's own published icon (the `ENTITY_ICON` of each model), resolved by the server from the entity-type catalog, with no map in the page; the ID column is gone. | Ruled Q102c. The full id as a Name tooltip is not possible: `tooltip: full_value` shows the cell's own value. |
| req-rampart-20x-playground-page-inventory-6 | Published Type Names | Proposed | Each `entity_type` column (Service or Kind) is an `entityType` column (`show: name`) that shows the type's published display name (`ENTITY_NAME`) from the entity-type catalog, with no `labels` map in the page; the Cloud Services table has no Scheme column. | |
| req-rampart-20x-playground-page-inventory-7 | Third-Party SaaS Holds AWS And GitHub | Proposed | The Third-Party SaaS table holds the AWS organization (named `AWS`) and `github.com`; the `ghcr.io git-serious image` package is stamped `inventory: containers`. | Ruled Q101. |
| req-rampart-20x-playground-page-inventory-8 | Teleport Programs | Proposed | `teleport proxy`, `teleport auth` and `teleport ssh` are `computing_core__program` entities stamped `inventory: applications` and `dataclass.action: process`, not on the Overview, each joined by a `RUNS_PROGRAM` edge from the `teleport` EC2 instance. | The edge source is open in `computing_core`; the three edges are in the application flow bundle. |
| req-rampart-20x-playground-page-inventory-9 | Crypto Lists Providers | Proposed | The Crypto table has one row per cryptographic provider, not one per file the scan found it in: on the seed, exactly three rows, `openssl-system`, `openssl-fips-provider` and `rust-aws-lc-rs`. | Ruled by George, 2026-10-21. The 31 `crypto_provider` nodes stay in the grid, one per provider and file, stamped `inventory: crypto`; the table groups them. |
| req-rampart-20x-playground-page-inventory-10 | Crypto Columns | Proposed | The Crypto table's columns are Icon, Provider, Provider Kind, Boundary, FIPS Validation, Rationale and Files (the number of files the provider was found in), with no Data Classification column. | Every provider's nodes agree on kind, boundary, validation and rationale in the seed (read 2026-10-21), so one row can show them. A provider whose nodes disagree is a defect to report, not a row to merge silently. |
| req-rampart-20x-playground-page-inventory-11 | Crypto Search Groups By Provider | Proposed | The Crypto section reads a Search that groups the provider nodes by `provider`. If Gryphon cannot express the grouping, the builder stops and reports it, and no `module` runner or code is written for this table. | The choice between a Gryphon capability and a `module` Search is George's. Built 2026-10-21 as a plain Gryphon Search (`MATCH (n:computing_core__crypto_provider) WHERE n.dimensions["inventory"] = "crypto" RETURN ... COUNT(n) AS files ORDER BY provider ASC`): a labelled node aggregate grouped by the non-aggregate columns needs no capability and no runner. |

### Vulnerabilities Page
----
RID: `req-rampart-20x-playground-page-vulnerabilities`

Status: `Proposed`

The vulnerabilities page tells a story to someone who has just arrived: how much is open, how severe it is,
what carries it, and what is already done. It is four cards, three charts, a table of the open vulnerabilities,
a table of the components that carry them and a table of the components that carry embedded malicious code (CWE-506), over the `compliance_core` vulnerability and finding nodes and
the `computing_core` components they concern. Each row drills in: a vulnerability page shows as much context as
the grid holds, the components that carry it and the systems where it was found; a component page shows its
type and every vulnerability it carries.

The CVE page explains one vulnerability to two readers: an analyst deciding how urgent it is and an engineer
deciding what to change. It reads top to bottom in the order those readers ask: a headline card (the CVE id large,
the plain-language title, the CVSS score and who assigned it, the publication time, and the CISA KEV state as the
card's tone word); then four answer cards, CVSS score first and widest (the severity word and tone follow the score
band), whether CISA lists it as exploited (the tone word is the answer; the figure is CISA's fix-by date; the lines
add the date added, ransomware use and the required action), how likely exploitation is (the EPSS probability, its
percentile spelled out in the line label, and CISA's SSVC exploitation, automatable and technical-impact
assessments) and the exposure here (open findings on components); then what it is (the full description in a card
line and the CWE weakness types); then where it affects us (the components that carry a finding, linked to their
pages, and the systems that install them); then, last, the vuln-mosaic dashboard as "Details and sources" for the
affected version ranges and fixed versions, the references and the data freshness. Each band after the first sits
under a short heading panel. To be narrowed to `sections: [...]` once vuln-mosaic ships that config key: the panel
then stops drawing its own header, cards and CVSS row, which this page now draws; until then it is mounted with its
current config and repeats them. The spelled-out CVSS metric explanation (attack vector and the like) is vuln-mosaic's
and is not built here.

#### Implementation

Route `/playground/vulnerabilities`, three bands. The first band is four equal columns, each one Stat Cards card:
findings on CISA's KEV catalog, open findings, closed findings and the vulnerabilities classed CWE-506 (Embedded
Malicious Code; green at zero). The second band is three equal columns, each a Chart panel: the CVSS score of the open findings (the count printed in each bar), the most open findings (the ten
components carrying most, each bar stacked High, Medium and Low in the CVSS colours), and severity by age, a scatter of
publication time against CVSS score whose white bubble counts carry no outline. A card shows its figure
and the tone's left edge, with no unit, no secondary line and no tone word. The three charts share one height.
The third band is full width: a table of the open vulnerabilities (id, title, CVSS, KEV, publication time and
the number of components that carry it), a table of the components with an open vulnerability (name, type,
open findings and highest CVSS) and `Components With Embedded Malicious Code` (component, type, vulnerability, state
and findings, for each finding of a vulnerability whose CWE list contains CWE-506; empty, it shows its table-level `empty_text`, `No component carries a CWE-506 vulnerability.`). All three search and page, with alternating row shading, and their vulnerability and component links draw in the cell's own
text colour with no underline or hover highlight. Every heading, panel name and column title is in Title Case. A row opens `/playground/vulnerabilities/vulnerability`
or `/playground/vulnerabilities/component`; the id is a query parameter that the page forwards to its Searches
as a declared input. Every panel is bound by `USES_SEARCH` to one Search; the Searches reach vulnerabilities,
findings and components by edge and none names a tool, a vulnerability or a node id. The component type is the
node's own type, so a library, a package or anything else that carries a finding appears in the same table. The
vulnerability and findings in the bundle that supplies the compliance_core nodes are demo data until the CI SBOM
delivers enriched vulnerabilities.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-vulnerabilities-1 | Routes Serve | Proposed | `GET /playground/vulnerabilities`, `/playground/vulnerabilities/cve?vuln_id=...`, `/playground/vulnerabilities/vulnerability?vuln_id=...` and `/playground/vulnerabilities/component?component_id=...` return 200. | |
| req-rampart-20x-playground-page-vulnerabilities-2 | Cards Over Charts | Proposed | The first band is four equal columns of one card each; the second is three equal columns of one chart each; the cards carry no unit, secondary line or tone word. | The cards were each over a chart in three columns until the fourth card (`page-vulnerabilities-22`) made the page a row of cards over a row of charts. |
| req-rampart-20x-playground-page-vulnerabilities-3 | No Tool In A Search | Proposed | No Search names a scanner, a vulnerability or a node id. | The scanner is reached by edge, the vulnerability by a parameter. |
| req-rampart-20x-playground-page-vulnerabilities-4 | Standard Vocabulary Only | Proposed | The Searches read only `compliance_core`, `computing_core` and `github_core` types. | |
| req-rampart-20x-playground-page-vulnerabilities-5 | Config Names Returned Fields | Proposed | Every field a column, chart or row link names is a RETURN alias of its Search; every `$parameter` a Search uses is declared in its input schema. | |
| req-rampart-20x-playground-page-vulnerabilities-6 | Charts Describe Themselves | Proposed | The three charts share a height; each carries an accessible label and says what an empty result means; the score chart prints its counts. | |
| req-rampart-20x-playground-page-vulnerabilities-7 | Two Searchable Paged Tables | Proposed | A full-width band holds the open-vulnerability table and the per-component table, each with a quick filter, paging and a row link to its drill-in. The open-vulnerability table's id cell is a link and its row click goes to the CVE dashboard (`/playground/vulnerabilities/cve?vuln_id={id}`), as does a click on the severity-age chart; nothing on the overview opens the older vulnerability page. | The CVE page replaces the vulnerability links on the overview. |
| req-rampart-20x-playground-page-vulnerabilities-8 | Older Vulnerability Page | Proposed | The older vulnerability page shows its score, vector, KEV and exploitation signals, publication time and description in two tables; its components and systems tables moved to the CVE page, and nothing links to it. | The page is a retirement candidate; it stays until that is decided. |
| req-rampart-20x-playground-page-vulnerabilities-9 | Component Drill-In | Proposed | The component page shows its type, open findings, highest CVSS, every vulnerability it carries and the hosts that install it; a vulnerability's id link and row click open the CVE page. | |
| req-rampart-20x-playground-page-vulnerabilities-10 | CVE Page Names Itself | Proposed | The CVE page node is named exactly `CVE` (the breadcrumb shows it) and is hidden from navigation; its description says what it explains and where it is opened from. The visible heading is the headline card: the CVE id and the plain-language title, not the page name. | A page's description is not rendered. |
| req-rampart-20x-playground-page-vulnerabilities-11 | CVE Page Reading Order | Proposed | The CVE page runs in nine bands: headline card; heading and four answer cards; heading, description and weakness; heading, components and systems; heading and the vuln-mosaic panel last, with its current config. Each band after the first sits under a heading panel of its own. | The vuln-mosaic panel is to be narrowed to `sections: [...]` once it ships that key. |
| req-rampart-20x-playground-page-vulnerabilities-12 | CVSS Is The First, Widest Card | Proposed | The first answer card is the CVSS score, wider than the other three, out of 10; its tone and word (Low, Medium, High or critical) follow the score band (below 4, 4 to 6.9, 7 and up) for every score of one decimal; an unscored vulnerability is neutral with no word. | Critical folds into High because a stat card has three words (good, warn, bad). |
| req-rampart-20x-playground-page-vulnerabilities-13 | Exploited, Likely, Exposed | Proposed | The exploited card's tone word answers yes, no or not checked from the CISA KEV flag and its figure is the CISA fix-by date; the likelihood card shows the EPSS probability with the percentile and the SSVC exploitation, automatable and technical impact; the exposure card counts open findings on components and is green at zero. | |
| req-rampart-20x-playground-page-vulnerabilities-14 | Whole Description And Weakness | Proposed | The description is shown whole as a card line, never as a clipped table cell; the CWE weakness types are a one-row list. | CWE ids are plain text: a link needs the number alone, which the record keeps as `CWE-n`. |
| req-rampart-20x-playground-page-vulnerabilities-15 | Components And Systems On The CVE Page | Proposed | The components table (linked to the component pages) and the systems table moved from the older vulnerability page to the CVE page with their Searches unchanged. | |
| req-rampart-20x-playground-page-vulnerabilities-16 | Missing Data Reads As Not Recorded | Proposed | Every answer card carries a `not recorded` null text and an empty text saying the vulnerability is not in the grid; none draws a blank. | |
| req-rampart-20x-playground-page-vulnerabilities-17 | Title Case Everywhere | Proposed | Every panel name, panel title, chart axis name, column title and card line label on the vulnerability pages is in Title Case (each word capitalised, hyphenated parts both, acronyms kept), including `CVSS Score`, `Most Open Findings` and `Severity By Age`. | Ruled by George. |
| req-rampart-20x-playground-page-vulnerabilities-18 | Plain Links And Striped Tables | Proposed | The two overview tables are striped, and each of their `link` and `linkList` columns sets `formatter_params.style` to `plain`. | Cells are vertically centred by default in tap_web. |
| req-rampart-20x-playground-page-vulnerabilities-19 | Severity Bubbles Have No Outline | Proposed | The severity-by-age series label is white and bold with `textBorderWidth` 0 and no `textBorderColor`. | White on the yellow Medium bubbles has a low contrast ratio. |
| req-rampart-20x-playground-page-vulnerabilities-20 | Most Open Findings Is Stacked By Band | Proposed | The chart is a stacked bar of one series each for High, Medium and Low in `#c0392b`, `#d9a400` and `#2f9e6b` (the CVSS scheme), sorted by `total` and limited to ten, reading the `component-severity` runner; it keeps its click-through to the component page and shows a legend. | The `top-components` Search became a `module` Search because a panel's `USES_SEARCH` edge cannot be repointed. |
| req-rampart-20x-playground-page-vulnerabilities-21 | Component Page Is A Hero, A Systems Table And A Vulnerabilities Table | Proposed | The component page is one full-width column of three rows. (1) A hero stat card (`stat_card_panel`, `layout: figure_right`): the component's name as the bold title, the count of its open findings as the figure with the unit `open findings`, its type as the header line and its highest CVSS as a line; the same `comp-identity` Search rows, no new code. (2) The `Systems Where It Runs` table, full width and striped. (3) The `Vulnerabilities` table, full width, striped, its id links `style: plain`. Backlog, not built: the people or team responsible for the component belong in the hero card; the teams bundle now exists and the line is blocked on Gryphon (`req-rampart-20x-playground-component-team`); no blank line stands in for them. | Ruled 2026-10-20 (George, component page nits 1 to 4); item 4 is Backlog (`req-rampart-20x-playground-component-team`). |
| req-rampart-20x-playground-page-vulnerabilities-22 | Embedded Malicious Code Card And Table | Proposed | The overview holds a stat card `Embedded Malicious Code (CWE-506)` (Search `MATCH (v:compliance_core__compliance_vulnerability) WHERE v.data.cwes CONTAINS "CWE-506" RETURN COUNT(v) AS malicious`; tone `bad`, `zero_tone` `muted`, so it greys out at zero like the CISA KEV card) as the second card of the first band, right after the KEV card; the Overview carries the same card (`govcloud-layout-37`), and a striped, searchable, paged table `Components With Embedded Malicious Code` (Search over components that carry a finding concerning such a vulnerability, excluding repositories) as the third table of the full-width band; a row click opens the component page. Component and vulnerability cells are plain links to the component and CVE pages; the type cell is a badge. | Authored in cve-tap and dropped in. The seed carries no CWE-506 vulnerability, so the card reads 0 and the table shows its table-level `empty_text` (`No component carries a CWE-506 vulnerability.`), an option of the core table panel. |

### Data Classification Page

RID: `req-rampart-20x-playground-page-data-classification`

Status: `Proposed`

The page answers "what kinds of data does this deployment hold, and where?". Route `/playground/data-classification`;
the page is named `Data Classification`, which is also its breadcrumb. It starts with that title and carries no
explanatory prose. Under the title, three equal columns hold one stat card each, one card per classification key (`dataclass.customer`, `dataclass.infra` and `dataclass.action`). Each
card has the key in bold at the top left and the number of components carrying any value of it at the top right, large,
with `components` under the number; then the classification's description as plain text with no caption; then a
borderless table with one row per value it can take: the value, its description, and the number of components
carrying it (0 when none does). There is no breakdown by entity type.

Under the cards, four standard table panels show how much of the inventory carries the classification it should and what is missing or wrong (George, 2026-10-21: there is no separate Classification Mapping page; its tables live here). Each is bound by `USES_SEARCH` to one of the four Searches of `req-rampart-20x-playground-classification-mapping`: a summary table with one row per inventory category (columns `label`, `denominator`, `mapped`, `unmapped`, `mapped_incorrectly`, `no_rule` and `percent_mapped`), then three entity tables named `Mapped Incorrectly`, `Unmapped` and `Mapped` (columns `group`, `label`, `name`, `found_text` and `allowed_text`, titled in Title Case), in the runner's order. The entity tables have a quick filter and paging, because the unmapped table holds hundreds of rows.

All three cards read a `module` Search over the `compliance_core` runner `dimension-coverage` (compliance_core
`req-compliance-core-dimension-coverage`); the Search's input `dimension_key` is the only thing that differs. Gryphon
cannot write the query (a labelless aggregate grouped by entity type and by a dimension value taken from a Search
input), which each Search's description records. The values come from the dimension dictionary rows, so a value added to
the dictionary appears on its card with no change to this page.

The cards are the standard Stat Cards panel (`tap_web`). The product-and-plugin cards of `git-serious-double-tap`
(a coloured left edge, title, outlined pill, status sentence, compact table) were examined: that is the plugin-private
panel type `double-tap-demo-strip`, which runs inline Gryphon queries for pull requests and checks and is not bound to a
Search, so it cannot be reused here.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-data-classification-1 | Route Serves | Proposed | `GET /playground/data-classification` returns 200 and is in navigation. | |
| req-rampart-20x-playground-page-data-classification-2 | Title Then One Card Per Key | Proposed | Band one is a text panel whose header is the page title and whose text is empty; band two is three equal columns, one stat card per classification key. | Was two columns before the action axis. |
| req-rampart-20x-playground-page-data-classification-3 | Each Card Reads A Module Search | Proposed | Each card is bound by `USES_SEARCH` to a `module` Search whose runner is `dimension-coverage` and whose `dimension_key` default is its key; the Search description names the missing Gryphon capability. | |
| req-rampart-20x-playground-page-data-classification-4 | Values From The Dictionary | Proposed | No panel, Search or test names a classification value; the values table reads the runner's `values` array, so an added value renders unchanged. | |
| req-rampart-20x-playground-page-data-classification-5 | Config Names Returned Fields | Proposed | Every card field names a row field of the runner (`key`, `total`, `description`, `values`) and every table column a key of its `values` elements (`value`, `description`, `count`). | |
| req-rampart-20x-playground-page-data-classification-6 | Card Layout | Proposed | Each card uses the Stat Cards `figure_right` layout with a bold title, the unit `components`, a description line placed in the card header directly under the title (`placement: header`), and a `table` line of `value`, `description`, `count` captioned `Inventory` above the table (`label_placement: above`). | Ruled 2026-10-20 (George, Q90). The card title is still the dimension key (`dataclass.customer`): the dictionary nodes carry no plain-English name, so the title is open for a ruling. |
| req-rampart-20x-playground-page-data-classification-7 | Named Data Classification, No Prose | Proposed | The page and its title panel are named `Data Classification`, and no panel carries explanatory prose; the only caption is `Inventory` above each values table (`-6`). | |
| req-rampart-20x-playground-page-data-classification-14 | Summary Headings And Centred Numbers | Proposed | The `Summary` table's columns are titled `Category` (field `label`), `Total`, `Mapped`, `Unmapped`, `Incorrect` (field `mapped_incorrectly`), `No Rule` and `%` (field `percent_mapped`), and its six numeric columns carry `align: center` so each value sits centred under its heading. | The `Unmapped` table sets `show_all_rows` to `false`, so its page-size selector offers 25, 50, 100 and 200 and no `All`; the default stays 25 a page. |
| req-rampart-20x-playground-page-data-classification-8 | Action Card | Proposed | The third card is bound by `USES_SEARCH` to a `module` Search over `dimension-coverage` with `dimension_key` default `dataclass.action`; its values table lists `store`, `process`, `transmit` and `none` with their counts, and it adds no page code. | The runner already reads values from the dictionary, so this is a Search, a panel and a panel edge. |
| req-rampart-20x-playground-page-data-classification-9 | Four Mapping Tables Under The Cards | Proposed | Under the three cards the page has four table panels: the summary, `Mapped Incorrectly`, `Unmapped` and `Mapped`, each bound by `USES_SEARCH` to its own Search of the classification mapping, and no `/playground/classification-mapping` route exists. | Ruled by George, 2026-10-21. The old page and its entity are purged. |
| req-rampart-20x-playground-page-data-classification-10 | Mapping Tables Name Returned Fields | Proposed | The summary table's columns are `label`, `denominator`, `mapped`, `unmapped`, `mapped_incorrectly`, `no_rule` and `percent_mapped`; each entity table's are `group`, `label`, `name` (a link to the entity's page), `found_text` and `allowed_text`; every title is in Title Case. | |
| req-rampart-20x-playground-page-data-classification-11 | Entity Tables Filter And Page | Proposed | The three entity tables have a quick filter and paging, are striped, the name cell is a link and the row click opens the entity's page. | |
| req-rampart-20x-playground-page-data-classification-12 | Mapping Tables Carry No Prose | Proposed | No mapping table panel holds text written to orient the reader. | `no-explanatory-text-on-pages`, ruled 2026-10-20. |
| req-rampart-20x-playground-page-data-classification-13 | Coverage Chart Above The Cards | Proposed | Directly under the title the page has the row of four coverage cards and then the `Data Classification Coverage` chart panel of `req-rampart-20x-playground-inventory-coverage`; the three classification cards and the four mapping tables follow unchanged. | Ruled by George, 2026-10-21. |

### Classification Mapping
----
RID: `req-rampart-20x-playground-classification-mapping`

Status: `Proposed`

Which entities carry the data classification they should, which carry none, and which carry the wrong one. The comparison is compliance_core's `dimension-mapping-summary` and `dimension-mapping-entities` runners (`req-compliance-core-dimension-mapping`); the mapping they compare against is data held here, in the `mappings` input of four Searches. A fifth piece, an hourly Schedule, records the summary over time as a `compliance_search_snapshot` (`req-compliance-core-search-snapshot`) through the `coverage_snapshot` collector of `fedramp_20x_vdr` (`req-fedramp-20x-vdr-coverage-snapshot`).

#### Implementation

`grift/classification-mapping.grift.json`, one batch.

**Four Searches**, all `search_type: module`, `root: node`, each with the same `mappings` default (below):

| Search name | runner | `status` default | entity id |
| --- | --- | --- | --- |
| `playground — classification mapping summary` | `dimension-mapping-summary` | none | `01a15b2f-df3b-7569-bf22-9ead3f816b84` |
| `playground — classification mapping: mapped incorrectly` | `dimension-mapping-entities` | `mapped_incorrectly` | minted once with `scripts/uuid7` |
| `playground — classification mapping: unmapped` | `dimension-mapping-entities` | `unmapped` | minted once |
| `playground — classification mapping: mapped` | `dimension-mapping-entities` | `mapped` | minted once |

The summary Search's entity id is fixed because `fedramp_20x_vdr`'s collector names it in code (`req-fedramp-20x-vdr-coverage-snapshot`); the id here and there must never differ. Each Search's description says why it is a module Search (Gryphon cannot write a count grouped by a dimension value taken from an input) and where its mapping is also written, because the four copies must agree.

**The mapping** (groups of entity types; the assignment is proposed for review). Each row reads "an entity of one of these types should carry this key with one of these values", and the value check is the group's: a value is right when the group allows it (ruled by George, 2026-10-21). The Searches work in grouped mode, `group_by` `inventory` (`req-compliance-core-dimension-mapping`), so each entity is judged by the first row that names its type and is counted in its inventory category.

| group | entity types | key and allowed values | match |
| --- | --- | --- | --- |
| Data Flows | `computing_core__application_flow` | `dataclass.action`: `transmit` | `all` |
| Programs | `computing_core__program` | `dataclass.action`: `process` | `all` |
| AWS Services | `aws_core__aws_route53_zone`, `aws_core__aws_internet_gateway`, `aws_core__aws_alb`, `aws_core__aws_ecs_cluster`, `aws_core__aws_ecs_service`, `aws_core__aws_ecs_container`, `aws_core__aws_rds_instance`, `aws_core__aws_s3_bucket`, `aws_core__aws_secrets_manager_secret`, `aws_core__aws_kms_key`, `aws_core__aws_ecr_repository`, `aws_core__aws_iam_oidc_provider`, `aws_core__aws_codepipeline_pipeline`, `aws_core__aws_codebuild_project`, `aws_core__aws_ec2_instance` | `dataclass.action`: `store`, `process`, `transmit`, `none` | `all` |
| Containers | `computing_core__host`, `github_core__github_package`, `github_core__github_package_version` | `dataclass.action`: `process`, `store` | `all` |
| Packages | `computing_core__package` | `dataclass.action`: `process`, `none` | `all` |
| Libraries | `computing_core__library` | `dataclass.action`: `process`, `none` | `all` |
| Operating Systems | `computing_core__operating_system` | `dataclass.action`: `process` | `all` |
| Secrets | `computing_core__file`, `computing_core__public_key`, `computing_core__private_key`, `aws_core__aws_acm_certificate` | `dataclass.action`: `store` | `all` |
| Third-Party SaaS | `aws_core__aws_organization`, `github_core__github_platform` | `dataclass.action`: `store`, `process`, `transmit`, `none` | `all` |

These are the types the seed stamps into the inventory categories, as read on 2026-10-21. Two things are deliberate. The application flows carry no `inventory` stamp, so grouped mode never counts them in a category; the row is kept for the group George named and for a flow that is later stamped. And `computing_core__crypto_provider` has no row: it is a finding about the code that carries it (`CARRIES_CRYPTO_PROVIDER`), and the carrier is classified instead (ruled by George, 2026-10-21), so the Searches leave the `crypto` category out with `exclude_groups`, and their descriptions say so. A type with no row is not hidden: grouped mode counts it `unmapped` and `no_rule`.

**Four table panels.** `Summary`, `Mapped Incorrectly`, `Unmapped` and `Mapped`, each a standard table panel bound by `USES_SEARCH` to the Search of the same name above. They are shown on the Data Classification page (`req-rampart-20x-playground-page-data-classification-9`); the bundle holds no page.

**The Schedule.** One `schedule` node, `playground — classification mapping snapshot`, `enabled: true`, `cron_expression: "0 * * * *"` (hourly, UTC), `max_active_runs: 1`, and one `SCHEDULED_TARGET` edge to the entity id of the collector `fedramp_20x_vdr:coverage_snapshot`, which is `uuid5(NAMESPACE_COLLECTOR, "fedramp_20x_vdr:coverage_snapshot")`, `41611294-9c37-5013-8175-3b1c2c4a3908`. The guard `schedule-grift-targets` (`req-tap-cares-collector-model-10`) fails the build if that id does not resolve to a registered collector, so the plugin's `depends_on` gains `fedramp_20x_vdr` (with a `note`), the `demo` record installs it pinned by commit like the others, and the `compliance_core` entry's floor rises to the first release that ships the mapping runners and `SearchSnapshotCollector`. The `ci` record, which installs this plugin alone, needs the same plugins for the guard to resolve.

#### Development

The mapping and the grouping are stated four times because a module Search receives its inputs from its own `input_schema` defaults and there is no way for one Search to read another's. That is the duplication George accepted for the demo sprint; the fix is for the runners to read the mapping from one place, which is a change to the runners. A test pins the four `mappings` defaults as equal so they cannot drift.

The seed ships no wrong stamp, so the mapped-incorrectly table is empty until something is stamped with a value its row does not allow. That is the honest state of the data.

On the seed the summary lists the nine inventory categories (`crypto` left out), and the packages and libraries are unmapped because nothing stamps them: the gap the table is there to show. The mapped-incorrectly table stays empty because nothing is stamped with a value its group does not allow. The counts are not fixed here, because the inventory-software batch is regenerated.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-classification-mapping-1 | Four Module Searches | Proposed | The bundle holds four `search` nodes with `search_type` `module`, the runners and `status` defaults in the table above, and the summary Search carries the entity id `01a15b2f-df3b-7569-bf22-9ead3f816b84`. | |
| req-rampart-20x-playground-classification-mapping-2 | Same Mapping Four Times | Proposed | The `mappings` default is identical in all four Searches, and a test pins it. | |
| req-rampart-20x-playground-classification-mapping-3 | Rows Name Declared Values | Proposed | Every allowed value in the mapping has a `dimension` node `<key>.<value>` in this plugin's dimension bundle, so a run reports no undeclared-name warning. | `dataclass.action.none` and `dataclass.customer.sanitized` are in `req-rampart-20x-playground-dimensions`. |
| req-rampart-20x-playground-classification-mapping-4 | No Tool Or Id In The Code | Proposed | No Search names an entity id or a stamped value other than in the mapping default. | |
| req-rampart-20x-playground-classification-mapping-5 | Hourly Schedule | Proposed | One enabled `schedule` node with cron `0 * * * *` and `max_active_runs` 1 has one `SCHEDULED_TARGET` edge to `41611294-9c37-5013-8175-3b1c2c4a3908`. | |
| req-rampart-20x-playground-classification-mapping-6 | Target Resolves | Proposed | The `schedule-grift-targets` guard passes on a stack that installs this plugin and `fedramp_20x_vdr`. | |
| req-rampart-20x-playground-classification-mapping-7 | Dependencies Declared | Proposed | `depends_on` gains `fedramp_20x_vdr`, the `demo` record installs it, and the `compliance_core` floor names the release that ships the mapping runners and the snapshot base class. | |
| req-rampart-20x-playground-classification-mapping-8 | A Run Writes A Snapshot | Proposed | On a booted `demo` stack, one manual run of `coverage_snapshot` (the Run button on the collector's administrivia page) writes one `compliance_search_snapshot` whose `rows` are the summary rows, with an edge to the summary Search. | The demo's first data point; the schedule adds one an hour. |
| req-rampart-20x-playground-classification-mapping-9 | Every Seeded Type Has A Rule | Proposed | After the action stamps apply, the summary reports `no_rule` 0 for every category except `crypto`, which is excluded, and `warnings` lists no type without a rule. | A new type in the seed with no row shows here as a gap. The package count follows the inventory-software batch. |
| req-rampart-20x-playground-classification-mapping-10 | Id Pinned In This Repository | Proposed | A test in this repository asserts the summary Search's entity id is the literal `01a15b2f-df3b-7569-bf22-9ead3f816b84`, so a change to the seed shows here as well as in `fedramp_20x_vdr`. | The collector in `fedramp_20x_vdr` names this id in code and pins it in its own tests (`req-fedramp-20x-vdr-coverage-snapshot-5`); a pin on one side cannot see a change on the other. |
| req-rampart-20x-playground-classification-mapping-11 | Grouped And Excluded | Proposed | All four Searches declare `group_by` `inventory`, and `exclude_groups` `["crypto"]` with a description that says the crypto category is left out and why. | |

### Inventory Coverage
----
RID: `req-rampart-20x-playground-inventory-coverage`

Status: `Proposed`

Coverage is the measure teams use to show progress toward the December 7 date. For the inventory it answers two yes-or-no questions about every entry: does it have a responsible team, and is its data classification right. Each question gives a percentage for each of the nine inventory categories, recorded every hour and drawn as a line chart with a plain-average line on top. There is one coverage chart per page (George, 2026-10-21): the responsibility chart sits at the top of the inventory page, which is about who owns what, and the data classification chart sits at the top of the Data Classification page, above its cards.

#### Implementation

**Six Searches**, all `search_type: module`, `root: node`, in `grift/inventory-coverage.grift.json`:

| Search name | runner | entity id | what it does |
| --- | --- | --- | --- |
| `playground — responsibility coverage` | `dimension-mapping-summary` | `01a15fdf-61ef-710d-b5d3-e3a7ae238a40` | `group_by` `inventory`; one mapping row, `entity_types` `["*"]`, one key `team.responsible` with no `allowed`, so any set value counts; no group excluded |
| `playground — classification mapping summary` | `dimension-mapping-summary` | `01a15b2f-df3b-7569-bf22-9ead3f816b84` | the existing summary Search of `req-rampart-20x-playground-classification-mapping`, grouped, `crypto` excluded |
| `playground — responsibility coverage history` | `search-snapshot-series` | minted once | `search_id` the responsibility Search's id, `series_field` `label`, `value_field` `percent_mapped` |
| `playground — classification coverage history` | `search-snapshot-series` | minted once | `search_id` `01a15b2f-df3b-7569-bf22-9ead3f816b84`, `series_field` `label`, `value_field` `percent_mapped` |
| `playground — responsibility coverage totals` | `dimension-mapping-totals` | minted once | `summary_search_id` the responsibility Search's id; one live row for the cards |
| `playground — classification coverage totals` | `dimension-mapping-totals` | minted once | `summary_search_id` `01a15b2f-df3b-7569-bf22-9ead3f816b84`; one live row for the cards |

**Responsibility** is the `team.responsible` dimension stamped on each node (George, 2026-10-21; the Teams section stamps it, `req-rampart-20x-playground-teams`). An entry is covered when the stamp is set. An unstamped entry is uncovered, so a category with no stamps reads 0 percent; the seed's real stamps decide the starting figure, whatever it is.

**Data classification** is the grouped rulebook of `req-rampart-20x-playground-classification-mapping`: an entry is covered when it carries a `dataclass.action` its group allows.

**Recording.** The existing hourly Schedule runs `fedramp_20x_vdr:coverage_snapshot`, which records both summary Searches (`req-fedramp-20x-vdr-coverage-snapshot`, two ids). Nothing new is scheduled. The history is what the snapshots hold from the first run: the collector back-fills nothing. The mock history of `req-rampart-20x-playground-coverage-seed` is seed data, written once and labelled as mock.

**The charts.** Two `chart` panels (`req-web-panels-chart-panel-type`), one per page: `Responsibility Coverage` at the top of the inventory page and `Data Classification Coverage` at the top of the Data Classification page, below its row of cards and above the three classification cards, each bound by `USES_SEARCH` to its history Search. Each is a line chart on a time axis, with `series_by` `{category: observed_at, series: series, value: value}`, `types` `{observed_at: time, value: number}`, a 0 to 100 value axis, and `order` listing the categories in the order of the Summary table's rows (the runner's order: the dictionary's declared values in name order, then any other found) with the aggregate last, so it draws on top. The aggregate is named `Overall`. The classification chart has eight category lines and `Overall`; the responsibility chart has nine and `Overall`. Lines are independent, not stacked (George, 2026-10-21).

**Naming the lines (ruled 2026-10-21, George).** There is no legend. Each line carries its own name at its right end: the one template series sets `endLabel` to show the series name (formatter `{a}`) and `labelLayout` `moveOverlap` `shiftY`, which `series_by` copies onto every line, and the grid keeps a right margin wide enough for the longest name. The chart has an axis-triggered tooltip that names every line at a time. Colours are explicit and quiet (George, 2026-10-22): `color_map` maps every category name to the one token `muted` and `Overall` to `accent-1`; the template series draws lines at width 1.5 and opacity 0.55, and `series_by.overrides` restores `Overall` to width 6, opacity 1 and `z` 10, so `Overall` stands out and the rest are background. End labels follow each line's colour (`inherit`), so the category names are muted too. Whether the chart panel's validation accepts `endLabel` and `labelLayout` is not known from the spec; if it refuses either, that is a question for the chart panel in core (the Backlog row `-chart-end-labels`), not a bespoke script here.

**Titles.** Series names come from the dimension dictionary: a category's label is its description up to the first colon, so each `inventory.*` description starts with the Title Case name (`Operating Systems`, `Cloud Services`, `Third-Party SaaS`), and the chart shows those. The panels are named `Responsibility Coverage` and `Data Classification Coverage`. The page carries no explanatory text.

**The cards.** Above the chart on each page, a horizontal row of four standard Stat Cards panels (`req-web-stdpanel-statcards`), each its own panel bound by `USES_SEARCH` to that page's totals Search, so the figures are live: the Search runs on every page load and reads the grid as it is now, while the chart's last point is up to an hour old (George, 2026-10-21). The totals come from `dimension-mapping-totals`, so the page does no arithmetic and the mapping is stated once, in the summary Search. A card's figure is a field of the totals row:

| page | card (Title Case) | field | unit |
| --- | --- | --- | --- |
| Inventory | `Overall Coverage` | `percent_overall` | `%` |
| Inventory | `Entries` | `denominator` | `entries` |
| Inventory | `With A Team` | `mapped` | `entries` |
| Inventory | `Without A Team` | `unmapped` | `entries` |
| Data Classification | `Overall Coverage` | `percent_overall` | `%` |
| Data Classification | `Mapped` | `mapped` | `entries` |
| Data Classification | `Unmapped` | `unmapped` | `entries` |
| Data Classification | `Incorrect` | `mapped_incorrectly` | `entries` |

`Overall Coverage` is the plain average of the categories, the same figure the chart's `Overall` line shows (ruled by George, 2026-10-21); the other cards are the pooled counts. A card has no page-specific configuration: it is a panel node, a Search edge and nothing else, so any page mounts it with a `USES_PANEL` edge and no change (the overview will, and the consolidated coverage panel (`req-rampart-20x-playground-coverage-panel`) gathers the same figures from the same totals Searches).

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-inventory-coverage-1 | Six Searches | Proposed | The bundle holds the six `module` Searches of the table, with the runners and ids shown; the history Searches' `search_id` and the totals Searches' `summary_search_id` equal the two summary Searches' ids. | |
| req-rampart-20x-playground-inventory-coverage-2 | Responsibility Is Presence | Proposed | The responsibility Search's only mapping row names `*` and the key `team.responsible` with no `allowed`, and excludes no group. | |
| req-rampart-20x-playground-inventory-coverage-3 | One List Of Groups, Not Two | Proposed | The classification summary reads the grouped rulebook of the classification mapping and no other mapping, and its description says the crypto category is left out and why. | |
| req-rampart-20x-playground-inventory-coverage-4 | Both Recorded Hourly | Proposed | One run of `coverage_snapshot` writes one snapshot for each summary Search, each with an edge `CAPTURES_SEARCH` to its Search. | Depends on the two-id change in `fedramp_20x_vdr`. |
| req-rampart-20x-playground-inventory-coverage-5 | One Chart Per Page | Proposed | The inventory page has one `chart` panel above the tables, `Responsibility Coverage`, and the Data Classification page has one, `Data Classification Coverage`, below its row of cards and above the three classification cards; each is bound by `USES_SEARCH` to its history Search, and neither page has a second coverage chart. | Ruled by George, 2026-10-21. The inventory tables keep their Data Classification column. |
| req-rampart-20x-playground-inventory-coverage-6 | Independent Lines, Aggregate Last | Proposed | Each chart is a line chart with `series_by`, a time axis, a 0 to 100 value axis and no `stack`; `Overall` is last in `order`. | |
| req-rampart-20x-playground-inventory-coverage-7 | Series Named From The Dictionary | Proposed | The `label` of each series equals the Title Case name that begins its `inventory.*` description, and the three descriptions that were not Title Case are. | |
| req-rampart-20x-playground-inventory-coverage-8 | Empty Is Stated | Proposed | Before the first snapshot a chart shows the chart panel's empty state, not a zero line. | `req-web-panels-chart-render`. |
| req-rampart-20x-playground-inventory-coverage-9 | Rows Fit The Chart | Proposed | The chart config's `max_rows` is 5000, the panel's largest value, and each history Search's `max_snapshots` default is 500, so that the ten lines of 500 snapshots fit within it and no point is silently cut. | The runner's own default of 720 snapshots times ten lines is 7200 rows, above the panel's cap of 5000, so the Searches set 500; found while building, not as ruled. |
| req-rampart-20x-playground-inventory-coverage-10 | No Prose | Proposed | A coverage chart's band carries the chart only; no panel holds text written to orient the reader. | `no-explanatory-text-on-pages`, ruled 2026-10-20. |
| req-rampart-20x-playground-inventory-coverage-11 | Dependencies Declared | Proposed | `depends_on` and the `compliance_core` floor name the releases that ship grouped mapping and `search-snapshot-series`, and the `fedramp_20x_vdr` floor the release that records both Searches. | |
| req-rampart-20x-playground-inventory-coverage-12 | Four Live Cards Above The Chart | Proposed | Each page has a horizontal row of four Stat Cards panels above its coverage chart, with the titles, fields and units of the cards table, each bound by `USES_SEARCH` to the page's totals Search. | Ruled by George, 2026-10-21. |
| req-rampart-20x-playground-inventory-coverage-13 | Cards Are Live | Proposed | A card reads the totals Search at page load and no `compliance_search_snapshot`, so its figure reflects the grid now. | |
| req-rampart-20x-playground-inventory-coverage-14 | Overall Agrees With The Chart | Proposed | After a snapshot is taken and nothing changes, a page's `Overall Coverage` card equals the last point of its chart's `Overall` line. | Both use `plain_mean`. |
| req-rampart-20x-playground-inventory-coverage-15 | Cards Are Standalone | Proposed | A card panel carries no page-specific config and is mounted on a page by `USES_PANEL` alone; mounting one of the cards on a second page changes no card. | The overview will mount them. |
| req-rampart-20x-playground-inventory-coverage-16 | The Page Does No Arithmetic | Proposed | No card, Search or page code computes a mean or a sum; each figure is a field of the totals row. | The rule that arithmetic stays in the runner. |
| req-rampart-20x-playground-inventory-coverage-17 | Names At The Line Ends | Proposed | Neither chart has a `legend`; the template series has `endLabel` showing the series name, flat and in its line's colour (`color` `inherit`, `textBorderWidth` 0, `textBorderColor` `transparent`, `textShadowBlur` 0, because ECharts outlines an end label by default and the panel's theme flattens only `label`, and a fixed colour cannot follow light and dark), and a `labelLayout` that shifts overlapping labels apart, and the grid has room on the right for them. | Ruled by George, 2026-10-21. |
| req-rampart-20x-playground-inventory-coverage-18 | Order Follows The Summary | Proposed | Each chart's `order` lists the categories in the row order of the Summary table of the same page, `Overall` last. | Ruled by George, 2026-10-21. |
| req-rampart-20x-playground-inventory-coverage-19 | Explicit Colours And A Tooltip | Proposed | Each chart has an axis-triggered tooltip and a `color_map` giving every category line the one token `muted` and `Overall` the token `accent-1`. | Muted and neutral are near-identical slate tones, so `Overall` takes a categorical accent that reads in both themes (ruled 2026-10-22, George). The responsibility chart's ninth category no longer repeats a colour. |
| req-rampart-20x-playground-inventory-coverage-chart-end-labels | End Labels In The Chart Panel | Backlog | If the chart panel refuses `endLabel` or `labelLayout` in its config, the chart panel accepts them. | A core decision; core is held. |
| req-rampart-20x-playground-inventory-coverage-views | Other Views Of The History | Backlog | A table with a small trend line in each row, or a heat grid of category by time. | Considered 2026-10-21 and deferred; each needs a core panel capability. The line chart with end labels is the view for the demo. |
| req-rampart-20x-playground-inventory-coverage-overall-weight | Overall Line Thick, Opaque, On Top | Proposed | The template series draws every category line at `lineStyle` width 1.5 and opacity 0.55; `series_by.overrides` gives `Overall` width 6 (about four times), opacity 1 and `z` 10. | Needs tap with `series_by.overrides` (tap PR 1103). Ruled 2026-10-22, George. |
| req-rampart-20x-playground-inventory-coverage-overview | Cards On The Overview | Backlog | The same cards mounted on the Overview page. | The cards and the totals calculation are built to be reused for this (`-15`). The consolidated panel is `req-rampart-20x-playground-coverage-panel`. |

### Coverage History Seed
----
RID: `req-rampart-20x-playground-coverage-seed`

Status: `Proposed`

MOCK DATA, never collected from a live system. Ruled by George, 2026-10-21, so that the two coverage charts show the figures going up and to the right: the seed stamps more entities, so the coverage figures end high, and a four-day history of snapshots climbs to those figures. Both parts are seed data in `grift/`; no code, no collector. The real hourly snapshots of `fedramp_20x_vdr` continue from the last mock point.

#### Implementation

**End state, classification.** The stamps below bring the data classification coverage to the end state of the waypoint table (a mean of 77.6 percent over the eight categories). A value is always one its type's group allows (`req-rampart-20x-playground-classification-mapping`), except the one wrong stamp on purpose. Stamps already made (the five flows, the programs, the RDS instance, the S3 buckets and the ECS containers) stay.

| Category | Stamp, `dataclass.action` | Left unstamped |
| --- | --- | --- |
| Cloud Services | `route53_zone`, `internet_gateway`, `alb`: `transmit`. `ecs_cluster`, `ecs_service`, `kms_key`, `codepipeline_pipeline`, `ec2_instance`: `process`. `secrets_manager_secret`, `ecr_repository`: `store`. `iam_oidc_provider`: `none` | the two `codebuild_project` rows |
| Containers | `computing_core__host`: `process`. `github_package`: `store` | the `github_package_version` row |
| Libraries | the first three `computing_core__library` rows in file order: `process` | the fourth |
| Operating Systems | `Wolfi`: `process` | none |
| Packages | every `computing_core__package` row: `process` | the rows at positions 10, 20, and so on to 180 in file order (18 rows) |
| Secrets | the container TLS certificate (a file) and the TLS certificate (ACM): `store`. The container TLS public key: `transmit`, which the group does not allow, so it reads as mapped incorrectly | the container TLS private key |
| Third-Party SaaS | `github.com`: `transmit` | the `AWS` organization |

**End state, responsibility.** The `team.responsible` stamp (`team` ids as in the Teams section) is added to `github.com` (`devops`), the container TLS certificate and the container TLS private key (`infra`). The container TLS public key stays unowned. Every other entity that carries an `inventory` value already has an owner, so the end state is 100 percent in every category but Secrets, which is 3 of 4 (a mean of 97.2 over the nine).

**The snapshots.** For each of the two summary Searches (`01a15fdf-61ef-710d-b5d3-e3a7ae238a40` and `01a15b2f-df3b-7569-bf22-9ead3f816b84`), one `compliance_search_snapshot` node every four hours from 2026-10-17 00:00Z to 2026-10-21 20:00Z inclusive: 30 per Search, 60 in all, each with one `CAPTURES_SEARCH` edge to its Search. `source` is `rampart_20x_playground`, so a mock snapshot can never share a key with a real one (`fedramp_20x_vdr`) and every mock snapshot is found by that one value; `snapshot_key` is `<search entity id>@<observed_at>` as the snapshot spec states; `name` is `<search_name> @ <observed_at>`; `truncated` is false and `row_count` is the length of `rows`; `inputs_text` is the canonical JSON of the Search's inputs, taken from the Search. Every snapshot's batch description says MOCK DATA, never collected.

**The rows of a snapshot** are what the Search's runner returns: one row per `inventory` value the dictionary declares, in the runner's order (name order), with `group`, `label`, `denominator`, `mapped`, `unmapped`, `mapped_incorrectly`, `no_rule`, and `percent_mapped`. The classification Search has no `crypto` row. A category with `denominator` 0 has `percent_mapped` `null` and is no point on the chart. `mapped_incorrectly` is 0 except the Secrets row of the last classification snapshot, which is 1; `no_rule` is 0 throughout; `unmapped` is `denominator` less `mapped` less `mapped_incorrectly`; `percent_mapped` is `mapped` over `denominator` times 100 to one decimal. The labels are the Title Case names of the inventory dictionary (`Cloud Services`, `Operating Systems`, `Third-Party SaaS`).

**The waypoints.** Five times: T0 2026-10-17 00:00Z, T1 2026-10-18 12:00Z, T2 2026-10-19 12:00Z, T3 2026-10-20 12:00Z and T4 2026-10-21 20:00Z. Each cell is `mapped/denominator`; a dash is denominator 0 (the category does not exist yet). Between waypoints, `mapped` and `denominator` each move in a straight line from one to the next and are rounded to whole numbers, so counts rise a few at a time and no step is a cliff. The story: owners were assigned team by team (infrastructure first, then applications), the 180 packages arrived on 10-19 and the cryptographic scan on 10-20, and the action axis (ruled 2026-10-20) began to be stamped on 10-19 and reached the cloud services today.

Responsibility:

| Category | T0 | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- | --- |
| Applications | 2/5 | 3/5 | 5/6 | 8/8 | 8/8 |
| Cloud Services | 3/12 | 8/12 | 11/14 | 14/14 | 18/18 |
| Containers | 0/2 | 1/2 | 2/3 | 3/3 | 3/3 |
| Crypto | - | - | - | 12/31 | 31/31 |
| Libraries | 1/4 | 2/4 | 3/4 | 4/4 | 4/4 |
| Operating Systems | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 |
| Packages | - | - | 90/180 | 150/180 | 180/180 |
| Secrets | 0/4 | 1/4 | 1/4 | 2/4 | 3/4 |
| Third-Party SaaS | 0/2 | 0/2 | 1/2 | 1/2 | 2/2 |

Data classification:

| Category | T0 | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- | --- |
| Applications | 0/5 | 0/5 | 2/6 | 5/8 | 8/8 |
| Cloud Services | 0/12 | 0/12 | 0/14 | 1/14 | 16/18 |
| Containers | 0/2 | 0/2 | 0/3 | 0/3 | 2/3 |
| Libraries | 0/4 | 0/4 | 0/4 | 1/4 | 3/4 |
| Operating Systems | 0/1 | 0/1 | 0/1 | 0/1 | 1/1 |
| Packages | - | - | 0/180 | 45/180 | 162/180 |
| Secrets | 0/4 | 0/4 | 0/4 | 0/4 | 2/4 |
| Third-Party SaaS | 0/2 | 0/2 | 0/2 | 0/2 | 1/2 |

**Order of landing.** The stamps land before the first real snapshot after the build, or the real line would drop to today's figures and climb back. The last mock point (T4) is the live summary's figures after the stamps; the real snapshots then continue at those values.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-coverage-seed-1 | Classification Stamps | Proposed | The seed carries the `dataclass.action` stamps of the table above, each value one its type's group allows except the container TLS public key's `transmit`, and carries none on the rows left unstamped. | Ruled by George, 2026-10-21. |
| req-rampart-20x-playground-coverage-seed-2 | Responsibility Stamps | Proposed | `github.com` carries `team.responsible` of `devops`; the container TLS certificate and private key carry `infra`; the container TLS public key carries none. | |
| req-rampart-20x-playground-coverage-seed-3 | End State Is The Live Summary | Proposed | After the stamps, the responsibility summary Search's per-category `mapped` and `denominator` equal the T4 column of the responsibility table, and the classification summary's equal the T4 column of the classification table, with one `mapped_incorrectly` (Secrets). | Checked against the Searches, not against this spec's arithmetic. |
| req-rampart-20x-playground-coverage-seed-4 | Wrong On Purpose | Proposed | The `Mapped Incorrectly` table of the Data Classification page lists the container TLS public key, and no other entity. | |
| req-rampart-20x-playground-coverage-seed-5 | Thirty Snapshots Per Search | Proposed | Each of the two summary Searches has exactly 30 mock snapshots, observed every four hours from 2026-10-17 00:00Z to 2026-10-21 20:00Z, each captured by one `CAPTURES_SEARCH` edge to that Search. | |
| req-rampart-20x-playground-coverage-seed-6 | Mock And Findable | Proposed | Every mock snapshot has `source` `rampart_20x_playground`, a `snapshot_key` of the form `<search id>@<observed_at>`, and a batch description that says MOCK DATA, never collected; deleting every snapshot of that source removes the mock history and nothing else. | A mock snapshot cannot collide with a real key. |
| req-rampart-20x-playground-coverage-seed-7 | Rows As The Runner Writes Them | Proposed | Each snapshot's rows have the fields, the order and the labels of the summary runner's rows, the classification rows omit `crypto`, `unmapped` equals `denominator` less `mapped` less `mapped_incorrectly`, and `percent_mapped` is `mapped` over `denominator` to one decimal, `null` when `denominator` is 0. | `req-compliance-core-dimension-mapping-9`, `-10`. |
| req-rampart-20x-playground-coverage-seed-8 | Counts Follow The Waypoints | Proposed | At each of the five waypoint times a snapshot's `mapped` and `denominator` equal the table; between them each is a straight line rounded to whole numbers. | |
| req-rampart-20x-playground-coverage-seed-9 | Up And To The Right | Proposed | In each chart no line's value falls from one snapshot to the next, except where its category's denominator grows faster than its mapped count; and each chart's last `Overall` is higher than its first. | The classification chart's first `Overall` is 0.0. |
| req-rampart-20x-playground-coverage-seed-10 | Charts Show It | Proposed | With the seed, both charts draw one line per category with a figure, plus `Overall`, from 2026-10-17 to 2026-10-21, and the `Overall` card of each page equals the last point of its chart. | `req-rampart-20x-playground-inventory-coverage-14`. |
| req-rampart-20x-playground-coverage-seed-remove | Retire The Mock History | Backlog | Delete the mock snapshots once the real history is long enough to carry the charts. | A separate step; the one `source` value finds them. |

### Coverage Panel
----
RID: `req-rampart-20x-playground-coverage-panel`

Status: `In Development`

Every coverage figure of the playground at once, in one panel on the front page: the four figures of each coverage card and the trend of both coverage histories, in the plain report style. Ruled by George, 2026-10-24 (a consolidated coverage panel for the front page, to be built by the `fedramp_20x_vdr` session). It is the coverage section of the Reporting page (`req-rampart-20x-playground-page-reporting`) on its own, so a reader of the front page sees the same figures an agency report carries.

#### Implementation

One `panel` node of the `report` type of `compliance_core` (`req-compliance-core-panel-report`, released in v0.8.10), `title` `Coverage`, `show_as_of` on, no `cut_line`, no `page_break_before`. It is data only: no code, no template and no script is added to this plugin. It is linked by `USES_SEARCH` to the four Searches its lines name and to no other: the two totals Searches and the two history Searches of `req-rampart-20x-playground-inventory-coverage`. The landing page mounts it with one `USES_PANEL` edge, as a band under the design graph; nothing already on the landing page changes. All figures are live except the trend, which reads the recorded snapshots; all arithmetic stays in the runners (`req-compliance-core-dimension-mapping-totals`), and the panel only formats.

| section | item | source Search | field |
| --- | --- | --- | --- |
| Responsibility | `Overall Coverage`, `percent` | `playground — responsibility coverage totals` | `percent_overall` |
| Responsibility | `Entries`, `count` | the same | `denominator` |
| Responsibility | `With A Team`, `count` | the same | `mapped` |
| Responsibility | `Without A Team`, `count` | the same | `unmapped` |
| Data Classification | `Overall Coverage`, `percent` | `playground — classification coverage totals` | `percent_overall` |
| Data Classification | `Mapped`, `count` | the same | `mapped` |
| Data Classification | `Unmapped`, `count` | the same | `unmapped` |
| Data Classification | `Incorrect`, `count` | the same | `mapped_incorrectly` |
| Coverage Over Time | one `trend`, two lines: `Responsibility` and `Data Classification`, each the series `Overall` (`series_field` `series`) | the two history Searches | `percent` of `value` over `observed_at` |

The labels are the titles of the cards table of `req-rampart-20x-playground-inventory-coverage`, so a figure on the front page reads the same as on its own page. Headings and labels are in Title Case. A figure whose Search fails or returns `null` shows `Not observed`, and a trend with no snapshots shows `No data yet` (`req-compliance-core-panel-report-6`, `-11`).

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-coverage-panel-1 | One Report Panel | In Development | The bundle holds one `panel` node of the `report` type titled `Coverage`, with no `cut_line`, whose sections and items are exactly those of the table above. | Data only; no template or script is added. |
| req-rampart-20x-playground-coverage-panel-2 | Linked To The Four Searches | In Development | The panel has a `USES_SEARCH` edge to each of the two totals Searches and the two history Searches, and to no other Search. | `req-compliance-core-panel-report-2`. |
| req-rampart-20x-playground-coverage-panel-3 | On The Landing Page | In Development | The landing page has a `USES_PANEL` edge to the panel, and `GET /playground` returns 200 with the panel under the design graph. | The graph and its projection are unchanged. |
| req-rampart-20x-playground-coverage-panel-4 | Figures Match The Cards | In Development | Each figure equals the card of the same title on its own page, and the `Overall Coverage` of each section equals the last point of that page's chart `Overall` line when nothing has changed since the last snapshot. | One mean, `plain_mean`. |
| req-rampart-20x-playground-coverage-panel-5 | Same Figures As The Agency Report | In Development | The two `Overall Coverage` figures and the trend equal the Coverage section of the Reporting page's `Agency Report`. | Both read the same Searches. |
| req-rampart-20x-playground-coverage-panel-6 | The Panel Does No Arithmetic | In Development | No figure of the panel is computed in the panel, a Search added for it, or page code; each is a field of a totals row or a history series. | The rule that arithmetic stays in the runner. |
| req-rampart-20x-playground-coverage-panel-7 | Not Observed Is Shown | In Development | A figure whose Search fails or returns `null` shows `Not observed`, not 0, and a trend with no snapshots shows `No data yet`. | `req-compliance-core-panel-report-6`, `-11`. |
| req-rampart-20x-playground-coverage-panel-8 | No Prose | In Development | The panel carries a title, headings and figures only; no text written to orient the reader. | `no-explanatory-text-on-pages`, ruled 2026-10-20. |
| req-rampart-20x-playground-coverage-panel-9 | Dependencies Declared | In Development | The `compliance_core` floor names v0.8.10, the release that ships the `report` panel. | |

### Reporting Page
----
RID: `req-rampart-20x-playground-page-reporting`

Status: `Proposed`

The overall status of the system under management, in the form leadership reads and agencies are sent: a plain, print-ready report with a few figures and trend lines. Route `/playground/reporting`; the page is named `Reporting`, which is also its breadcrumb. It has two parts, divided by a cut line (George, 2026-10-21): the top part is written to be sent to agencies, and everything below the line is for internal use only. The VDR Reports page is the drill-down below this summary (`req-rampart-20x-playground-page-vdr-reports`). The look is low-key and minimal: no boxes, no cards, no colour; something you could print and send, or screenshot into a presentation.

#### Implementation

Two `panel` nodes of the `report` type of `compliance_core` (`req-compliance-core-panel-report`), one per part, in two bands under the page's title, and nothing else on the page. They are separate nodes, not one panel with a divider, so an export or a print of the agency part cannot include the internal part. Each is linked by `USES_SEARCH` to every Search its lines name, as the panel requires. All figures are live: the Searches run on every page load. All arithmetic stays in the runners (`req-compliance-core-dimension-mapping-totals`, `req-fedramp-20x-vdr-deadlines`); the panel only formats. Names and headings are in Title Case.

**Agency Report** (the first panel; no cut line; `title` `Status Report`, as-of line on):

| section | item | source Search | state |
| --- | --- | --- | --- |
| Coverage | `Responsibility Coverage`: `percent_overall`, `of` `denominator` entries | `playground — responsibility coverage totals` | in `req-rampart-20x-playground-inventory-coverage` |
| Coverage | `Data Classification Coverage`: `percent_overall`, `of` `denominator` entries | `playground — classification coverage totals` | in `req-rampart-20x-playground-inventory-coverage` |
| Coverage | a trend, `Coverage Over Time`: two lines, `Responsibility` and `Data Classification`, each the series `Overall` | the two coverage history Searches | in `req-rampart-20x-playground-inventory-coverage` |
| Vulnerabilities | `Open Vulnerabilities` and one figure per severity (`Critical`, `High`, `Medium`, `Low`) | `playground — report open vulnerabilities` | new |
| Vulnerabilities | `Known Exploited` (open findings whose vulnerability is on the CISA list) | `playground — report known exploited` | new |
| Timeline | `Days To December 7` | `playground — report days to december 7` | new; uses Gryphon's date arithmetic |

**Internal Report** (the second panel; `cut_line` `Internal`; `page_break_before` true):

| section | item | source Search | state |
| --- | --- | --- | --- |
| Deadlines | `Evaluation Overdue`, `Remediation Overdue`, `Acceptance Reached`, `Detection Time Unobserved`, each a count | the four views of `vdr-deadlines` | runner released in `fedramp_20x_vdr` v0.1.3; Search nodes are new |
| Coverage Gaps | `Entries Without A Team`, `Unmapped Classification Entries`, `Incorrect Classification Entries` | the two totals Searches | in `req-rampart-20x-playground-inventory-coverage` |
| Teams | a list of teams with entries owned, open findings and past due | `playground — report teams` | Backlog (`req-rampart-20x-playground-reporting-teams`) |
| Data Freshness | `Last Vulnerability Data Refresh`, `Last Coverage Snapshot` | `playground — report last refresh`, `playground — report last snapshot` | new |

**The deadline figures are a worst-case bound** (`req-fedramp-20x-vdr-deadlines`: in v0 every finding is counted from detection under the worst-case row, 12 hours for class D, and no evaluation is complete), so they read as nearly everything overdue. They are stated as such in their labels, and they sit in the internal part: an agency copy would overstate the position until evaluations exist. Moving them above the line is a ruling for George after the evaluation work (`req-rampart-20x-playground-reporting-deadlines-up`).

**Not on the page yet.** The open-vulnerabilities trend (a count Search the snapshot collector would record), the burn-down of opened against closed, the PAIN breakdown (it waits on `stackarmor_vdr` and its playground wiring), and a KSI figure (the KSI plugin is a catalog only, with no evidence to count) are Backlog.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-reporting-1 | Route Serves | Proposed | `GET /playground/reporting` returns 200 and the page is in navigation, named `Reporting`. | |
| req-rampart-20x-playground-page-reporting-2 | Two Report Panels, Nothing Else | Proposed | The page's bands are two `report` panels, `Agency Report` then `Internal Report`, under the title; it holds no card, table or chart panel. | The charts are drawn inside the panels. |
| req-rampart-20x-playground-page-reporting-3 | Separate Nodes | Proposed | The two parts are two `panel` nodes with different entity ids, so a print or export of one cannot contain the other. | Ruled by George, 2026-10-21. |
| req-rampart-20x-playground-page-reporting-4 | Cut Line Above The Internal Part | Proposed | The internal panel's config has `cut_line` `Internal` and `page_break_before` true; the agency panel has no `cut_line`. | |
| req-rampart-20x-playground-page-reporting-5 | Linked To Every Search It Names | Proposed | Each panel has a `USES_SEARCH` edge to every Search named by a line of its config, and to no other. | `req-compliance-core-panel-report-2`. |
| req-rampart-20x-playground-page-reporting-6 | Agency Items | Proposed | The agency panel holds exactly the sections and items of the agency table, with the stated fields and `of` counts. | |
| req-rampart-20x-playground-page-reporting-7 | Internal Items | Proposed | The internal panel holds the sections and items of the internal table, and the deadline items say in their labels that they are a worst-case bound. | |
| req-rampart-20x-playground-page-reporting-8 | Nothing Internal Above The Line | Proposed | No team name, person, finding detail or deadline figure appears in the agency panel's config. | The agency copy is safe to send. |
| req-rampart-20x-playground-page-reporting-9 | Overall Matches The Cards And Chart | Proposed | Each coverage figure equals the matching `Overall Coverage` card of its page and the last point of its coverage trend's `Overall` line, when nothing has changed since the last snapshot. | One mean, `plain_mean`. |
| req-rampart-20x-playground-page-reporting-10 | Days To December 7 | Proposed | `Days To December 7` is the whole days from now to 2026-12-07 as computed by its Search's date arithmetic, and is shown as `Not observed` if the Search fails; the date is in the Search, not in the panel. | |
| req-rampart-20x-playground-page-reporting-11 | Not Observed Is Shown | Proposed | A figure whose Search fails or returns `null` shows `Not observed`, not 0. | `req-compliance-core-panel-report-6`. |
| req-rampart-20x-playground-page-reporting-12 | Plain And Printable | Proposed | The page has no panel header chrome, box, colour or shadow beyond the report panel's own style, and a browser print of the page puts the agency part on the first page and the internal part on the next. | `req-compliance-core-panel-report-13` and `-14`. |
| req-rampart-20x-playground-page-reporting-13 | No Prose | Proposed | The page and panels carry a title, headings and figures only; no panel holds text written to orient the reader. | `no-explanatory-text-on-pages`, ruled 2026-10-20. |
| req-rampart-20x-playground-page-reporting-14 | Dependencies Declared | Proposed | `depends_on` and the floors name `compliance_core` v0.8.10, the release that ships the `report` panel (the totals runner and the series reader shipped before it), and `fedramp_20x_vdr` v0.1.3 or later, the release that ships `vdr-deadlines`. | |
| req-rampart-20x-playground-reporting-teams | Teams List | Backlog | The internal list of teams with entries owned, open findings and past due. | Needs a findings-by-responsible-team Search (the `req-rampart-20x-playground-teams-findings` Backlog row). |
| req-rampart-20x-playground-reporting-deadlines-up | Deadlines In The Agency Part | Backlog | Moving the deadline figures above the cut line once evaluations exist and the bound is exact. | A ruling for George. |
| req-rampart-20x-playground-reporting-trends | More Trends | Backlog | Open vulnerabilities over time, opened against closed, and the PAIN breakdown. | Each needs a recorded Search or the StackArmor wiring. |

### Teams And Responsibility
----
RID: `req-rampart-20x-playground-teams`

Status: `Proposed`

The vulnerability story needs its last link: a vulnerability sits on a component, the component belongs to a system, and a team answers for the system. This requirement seeds the teams, a roster of people in them, and the stamp that says which team is responsible for what. The vocabulary is identity_core's (`req-identity-core-team`, `req-identity-core-team-edges`, `req-identity-core-responsible`); this plugin seeds data only.

#### Implementation

`grift/teams.grift.json`, one batch.

**Four teams**, `identity_core__team`, each with a description:

| handle | name | description |
| --- | --- | --- |
| `git-serious` | `git-serious` | The whole git-serious product team; the other three belong to it. |
| `devops` | `DevOps` | Continuous delivery: the build, the pipeline and the release of the product. |
| `engineering` | `Engineering` | The code: the application and the libraries it ships. |
| `infra` | `Infra` | The AWS infrastructure the product runs on, and access to it (Teleport). |

`BELONGS_TO_TEAM` edges run from `devops`, `engineering` and `infra` to `git-serious`, and no other team-to-team edge.

**The roster**, `identity_core__human`, generic names only. Each of `devops`, `engineering` and `infra` has one lead and three members; `git-serious` has a lead and no direct members.

| handle | name |
| --- | --- |
| `<team>-lead` | `<Team Name> Team Lead` (for example `DevOps Team Lead`) |
| `<team>-member-1`, `-2`, `-3` | `<Team Name> Member 1`, `2`, `3` (for example `DevOps Member 1`) |
| `git-serious-lead` | `git-serious Team Lead` |

Each lead has a `LEADS_TEAM` edge to their team and also a `BELONGS_TO_TEAM` edge to it, so the roster shows the whole team; each member has a `BELONGS_TO_TEAM` edge. That is thirteen people. No real person, email address or account appears in the bundle.

Each of the four teams also has one `ANSWERS_FOR_DIMENSION` edge to the `team.responsible` dictionary node (identity_core v0.1.6), which records that the team's entity id appears under the key.

**The stamp.** The key `team.responsible` has a dictionary node (`dimension`, name `team.responsible`, with a description) and no value nodes, because the values are team ids (`req-identity-core-responsible`). It is stamped on entities already in the seed, by type (proposed for review; a type listed carries the team's entity id on every instance unless noted):

| team | types |
| --- | --- |
| `devops` | `github_core__github_workflow`, `github_core__github_actions_run`, `github_core__github_package`, `github_core__github_package_version`, `aws_core__aws_ecr_repository`, `aws_core__aws_lambda`, `aws_core__aws_s3_bucket`, `aws_core__aws_codepipeline_pipeline`, `aws_core__aws_codebuild_project`, `aws_core__aws_iam_oidc_provider`; the application flows `code` and `source pull` |
| `engineering` | `github_core__github_repository`, `github_core__github_account`, `computing_core__program`, `computing_core__library`, `computing_core__package`, `computing_core__source_package`, `computing_core__sbom_document`, `computing_core__crypto_provider`, `computing_core__operating_system`, the container `computing_core__host` of the web image, the developer laptop; the application flows `customer data` and `database` |
| `infra` | `aws_core__aws_organization`, `aws_core__aws_account`, `aws_core__aws_vpc`, `aws_core__aws_subnet`, `aws_core__aws_internet_gateway`, `aws_core__aws_alb`, `aws_core__aws_ecs_cluster`, `aws_core__aws_ecs_service`, `aws_core__aws_ecs_task`, `aws_core__aws_ecs_container`, `aws_core__aws_rds_instance`, `aws_core__aws_secrets_manager_secret`, `aws_core__aws_kms_key`, `aws_core__aws_route53_zone`, `aws_core__aws_acm_certificate`, `aws_core__aws_ec2_instance` (Teleport), the administrator workstation; the two `administration` application flows |
| `git-serious` | `compliance_core__compliance_boundary` |

The customer's computer, the operating-system users and the three people are not stamped: the customer's machine is outside what the team answers for, and a person is not a system. Those, and anything not listed, stay unstamped, which means not yet assigned.

#### Development

A system is stamped by its type here because the demo's questions are about systems; the packages an image carries follow the image they are installed on, and a later traversal can derive a package's team from its host rather than stamping every package. The software types are stamped to `engineering` for the demo so the coverage table has a complete column, and a real deployment would stamp the image and derive the rest.

The generic roster is deliberate: the page must read as a demonstration of the structure, and a plausible name invites a question about who the person is.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-teams-1 | Four Teams | Proposed | The bundle holds four `identity_core__team` nodes with the handles, names and descriptions above. | |
| req-rampart-20x-playground-teams-2 | Nesting | Proposed | `devops`, `engineering` and `infra` each have one `BELONGS_TO_TEAM` edge to `git-serious`, and the bundle holds no other team-to-team edge. | |
| req-rampart-20x-playground-teams-3 | Thirteen People | Proposed | The bundle holds thirteen `identity_core__human` nodes with the handles and names above; each lead has a `LEADS_TEAM` and a `BELONGS_TO_TEAM` edge to their team and each member a `BELONGS_TO_TEAM` edge. | |
| req-rampart-20x-playground-teams-4 | Generic Only | Proposed | No node in the bundle carries a real person's name, an email address or an account name. | |
| req-rampart-20x-playground-teams-5 | Key Documented, Values Open | Proposed | A `dimension` node named `team.responsible` with a description is seeded, and no node named `team.responsible.<value>` is. | `req-identity-core-responsible`. |
| req-rampart-20x-playground-teams-6 | Stamps By Type | Proposed | Every instance of a type in the table carries `team.responsible` equal to the entity id of that row's team, and no other seed entity carries the key. | The customer's computer is left unstamped on purpose. |
| req-rampart-20x-playground-teams-7 | Ids Are Team Ids | Proposed | Every `team.responsible` value in the seed equals the entity id of one of the four seeded teams. | |
| req-rampart-20x-playground-teams-8 | Dependency Floor | Proposed | The `identity_core` entry in `depends_on` names the first release that ships `team`, `BELONGS_TO_TEAM`, `LEADS_TEAM` and `ANSWERS_FOR_DIMENSION` (v0.1.6), the ci and demo boot records pin that release by tag and commit, and the manifest lists the bundle. | |
| req-rampart-20x-playground-teams-9 | Teams Answer For The Stamp Key | Proposed | Each of the four teams has one `ANSWERS_FOR_DIMENSION__identity_core` edge to the `team.responsible` dimension node, so a page can walk from a team to the key whose values are its entity id. | `req-identity-core-responsible`. |

### Teams Page
----
RID: `req-rampart-20x-playground-page-teams`

Status: `Proposed`

Route `/playground/teams`; the page is named `Teams`, which is also its breadcrumb. It shows the teams and who is in them, under a title, with no explanatory prose.

#### Implementation

The graph panel (`req-rampart-20x-playground-teams-viz`) under the title panel, then three table panels, each bound by `USES_SEARCH` to its own Gryphon Search:

1. `Teams`: one row per team: `name` and `description`. The name of the parent team is not a column yet (`req-rampart-20x-playground-teams-parent-column`).
2. `Leaders`: one row per `LEADS_TEAM` edge: the team name and the leader's name.
3. `Members`: one row per `BELONGS_TO_TEAM` edge from a human: the team name and the member's name.

The name cell of each row is a link to the entity's page. Each table has a quick filter.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-teams-1 | Route Serves | Proposed | `GET /playground/teams` returns 200 and is in navigation. | |
| req-rampart-20x-playground-page-teams-2 | Title, Graph, Then Three Tables | Proposed | Under the title panel the page holds the teams graph, then the Teams, Leaders and Members tables in that order. | |
| req-rampart-20x-playground-page-teams-3 | Rows Match The Seed | Proposed | On a booted `demo` stack the Teams table has four rows, Leaders has four and Members has thirteen: every person, leaders included, has one `BELONGS_TO_TEAM` edge to their team. | |
| req-rampart-20x-playground-page-teams-4 | No Prose | Proposed | The page carries a title, the graph and tables only. | `no-explanatory-text-on-pages`. |

### Teams Graph
----
RID: `req-rampart-20x-playground-teams-viz`

Status: `Proposed`

A graph panel, full width, a thin banner (`40vh`) between the title and the Teams table of `/playground/teams`. A person is drawn inside their team and a team inside its parent team; the people of a team with no child teams stand in one horizontal row with the leader first; in a team that holds child teams the leader stands alone at the top centre, above one row of the child teams; and a leader's name is set apart in bold teal text. Every person is a solo icon: the type icon and the name, no card. The panel has no header, legend or prose.

#### Implementation

Nesting is the standard TAP nesting, configured and not coded: the layout module `static/rampart_20x_playground/js/projections/teams.js` calls `projectNested` with two single-hop relationships over `BELONGS_TO_TEAM__identity_core` (`(parent:identity_core__team)<-[:BELONGS_TO_TEAM__identity_core]-(child:identity_core__human)` and the same with a team child), `baseSizes` per type, `padding`, the `ranked` inner layout (`sort: "order"`), then `applyStandardChrome` and `placeParentLabels` (anchored top-centre, clear of the team's type-icon badge), and `cy.fit` on `initial_load` (the runtime then re-fits with 50 px padding, so the banner's usable height is 100 px less than the slot). The slot height is `40vh`, ruled by George (2026-10-21): the 60% cut of `75vh` (30vh) is not in core's page-layout `height` enum, and `25vh`, the nearest value below it, was too small to read. It holds configuration and data reads only; no geometry of its own.

Order is stamped from facts on the graph. A team with only people takes the projection's layout: each person its own `_stage` (and `_order` 0), so the people are the columns of one row, the leader (below) first, the others by typed `name` field. A team that holds child teams (the target of a `BELONGS_TO_TEAM__identity_core` edge from a team) stamps its people `_stage` 0 (the leader `_order` 0, the others 1) and every child team `_stage` 1 with `_order` its name rank, and sets `_inner_layout` on itself to `{name: "ranked", axis: "rows", sort: "order", columnGap: 56, rowGap: 44}`, a tap_viz option that overrides the inner layout for that one container: the leader alone at the top centre, one row of child teams below, left to right by name. The decision is the graph fact, never a label or a handle. Every person is made a solo icon by `applyIconNodes(cy, {members, solo: true})` (`req-viz-icon-node-solo`); a team stays a box, because an icon node is terminal and would hide what the team holds. Solo is a layout primitive, not a `node_style` value: the projection keeps `icon-badge`, which gives each team its type-icon badge.

A leader is a data read: the source of a `LEADS_TEAM__identity_core` edge in the scene is ordered first and its name takes the leader label style (bold deep teal text, `#0f5c70`, no background). The solo icon is a fixed background image, so no node style recolours it; the name carries the difference. The edge is hidden because the leader is already inside the team. The palette is chosen for the fixed `#f1f0ec` canvas, which is the same in light and dark.

The Layout, Elevation and Projection are data in `grift/teams.grift.json`, joined by `USES_PROJECTION`, `USES_ELEVATION`, `USES_DEFAULT_ELEVATION` and `USES_LAYOUT`. The panel reads three Gryphon Searches by `USES_SEARCH`: a person and their team, a team and its parent, and a leader and their team.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-teams-viz-1 | Graph Above The Tables | Proposed | The page's second slot is a full-width `tap_viz/panels/graph_panel.html` panel with no header, above the Teams table. | |
| req-rampart-20x-playground-teams-viz-2 | Nesting From The Edge | Proposed | The layout module nests with two `projectNested` relationships over `BELONGS_TO_TEAM__identity_core`, one with a human child and one with a team child, and names no entity by label or id. | |
| req-rampart-20x-playground-teams-viz-3 | Leaders From The Edge | Proposed | The module sets the name of the source of every `LEADS_TEAM__identity_core` edge in the leader style and hides that edge. | |
| req-rampart-20x-playground-teams-viz-4 | Declarative Wiring | Proposed | The panel, its projection, elevation and layout and three Gryphon Searches are in the teams bundle, with the hotlink edges the importer requires. | |
| req-rampart-20x-playground-teams-viz-5 | Counts On A Booted Stack | Proposed | On a booted `demo` stack the graph draws four teams, three of them inside `git-serious`, thirteen people, and four leaders with their names in the leader colour, in light and dark, with no console error. | |
| req-rampart-20x-playground-teams-viz-6 | No Prose | Proposed | The panel has no header, legend or text. | `no-explanatory-text-on-pages`. |
| req-rampart-20x-playground-teams-viz-7 | Children In A Row | Proposed | The module uses the `ranked` inner layout. A team with only people stamps each person its own `_stage` (leader first, the others by typed name), one horizontal row. A team that holds child teams (a `BELONGS_TO_TEAM` team-to-team edge) stamps its people `_stage` 0 and all its child teams `_stage` 1 with `_order` their name rank, and sets `_inner_layout` on itself to `ranked` with `axis: "rows"` and `sort: "order"`: the people above, one row of child teams below, left to right by name. No stage or order comes from a label or an id. | `_inner_layout` and the `rows` axis are tap_viz options (core PR 1091). |
| req-rampart-20x-playground-teams-viz-8 | Leader First In The Row | Proposed | A leader (the source of a `LEADS_TEAM__identity_core` edge) is stamped `_order` 0 in its team's top stage, so in a team with only people the leader stands first in the row, and in a team that holds child teams the leader stands alone at the top centre, above the row of child teams. | The `git-serious` leader stands above the row of its three child teams (the known gap, above, is closed). |
| req-rampart-20x-playground-teams-viz-9 | Leader Set Apart | Proposed | A leader's name takes a style of its own, bold deep teal text (`#0f5c70`) with no background, that an ordinary person's name does not. | George asked for a text or icon colour in place of the coloured background. The solo icon is a background image that no node style recolours, so the name carries the difference. |
| req-rampart-20x-playground-teams-viz-10 | People As Solo Icons | Proposed | Every person is made an icon-centric-solo node by `applyIconNodes` with `solo: true`; a team stays a box with its type-icon badge. | `req-viz-icon-node-solo`. |
| req-rampart-20x-playground-teams-viz-11 | A Thin Banner | Proposed | The graph's page slot is `40vh`, and the module fits the graph with 12 px padding on `initial_load`. | `40vh` was chosen by George over `25vh` and `33vh` for legibility. |

### Parent Team Column
----
RID: `req-rampart-20x-playground-teams-parent-column`

Status: `Backlog`

The Teams table should show, for each team, the name of the team it belongs to, blank for `git-serious`. Gryphon cannot: a plain match on `BELONGS_TO_TEAM` drops `git-serious`, which has no parent, and `OPTIONAL MATCH` keeps it but can only `COUNT` the optional variable, not return its `name` (`req-grid-gryphon-optional-match`, out-of-scope list). The missing capability is projecting the fields of an optional match. Until it ships, the Teams Search returns `name` and `description` only, and its description says so.

### Responsible Team On The Component Page
----
RID: `req-rampart-20x-playground-component-team`

Status: `Backlog`

The component page's hero should carry a `Responsible Team` line: the name of the team in the component's `team.responsible` stamp, and `not assigned` for a component with no stamp. Gryphon cannot answer it as data: a stamp is a dimension whose value is a team's entity id, `RETURN` cannot project a dimension value (`<var>.dimensions[...]` in `RETURN` is refused, `req-grid-traversal-lang-envelope-paths-7`), and a `MATCH` cannot join a team to the entity whose dimension holds its id. Showing the id is not an option, and a Search chained on another Search's output is not something a panel does. The missing capabilities are returning a dimension value and joining on it; either lets the line be a Gryphon Search with the stat card's empty text set to `not assigned`.

### Findings By Responsible Team
----
RID: `req-rampart-20x-playground-teams-findings`

Status: `Backlog`

The payoff of the stamp: for each team, the open findings on the components it answers for, with the count of those that have a fix available. A team reaches its systems through the stamp, not an edge, so the existing `findings-reached-*` runners (which follow edges from a root) do not give the answer; it needs a runner that starts from the entities carrying a team's id and follows the carrier edges from there. Not specified until the stamps exist and a design is chosen.

### Ownership Coverage
----
RID: `req-rampart-20x-playground-ownership-coverage`

Status: `Backlog`

How many entities carry a `team.responsible` stamp, by the mapping runners (`req-compliance-core-dimension-mapping`). Two limits to resolve first: a mapping row takes a fixed list of allowed values, so "points at a live team" cannot be written until the allowed list can come from nodes; and covering every entity means one row per type or a wildcard type in the runner.

### Program Stamps And Reach
----
RID: `req-rampart-20x-playground-pain-profiles`

Status: `Proposed`

PAIN is scored by the `stackarmor_vdr` plugin on top of `fedramp_20x_vdr`'s finding reach. Both plugins own their machinery. This requirement is the instance's half, which is data only: a stamp for each program, the package each program is, and the two Searches that name the runners. A stamp is a node of `stackarmor_vdr` that points at the program, so no existing node or edge that describes the system changes (ruled by George, 2026-10-21), and the profile is stamped on the **program** and nowhere else (ruled by George, 2026-10-20). A host or container takes no stamp; its profile is computed from its programs on read.

#### Implementation

**Program stamps.** One `stackarmor_vdr__asset_profile` node per program the inventory seeds, with `source` `playground-seed`, `scheme` `stackarmor`, a `rationale`, a `PROFILES_PROGRAM` edge to the program and a `USES_ARCHETYPE` edge to the archetype node of the table (the plugin seeds the sixteen archetype nodes). The stamps follow the memo's control-plane-first rule: an asset that holds credentials or can actuate access is classified by that function, not by the data it stores. This table is the assignment, confirmed by George, 2026-10-21:

| Program | Archetype | Why (the stamp's `rationale`) |
| --- | --- | --- |
| `tap-web`, `tap-web (web task b)` | `app_tier` | The stateless application. |
| `gunicorn`, `gunicorn (web task b)` | `app_tier` | The application server of the same service. |
| `PostgreSQL database instance` | `data_sensitive` | The datastore holding customer data. |
| `teleport proxy`, `teleport auth`, `teleport ssh` | `identity_secrets` | They hold access credentials and certificates and actuate administrative access. |

**Root packages.** `RUNS_PACKAGE` (`computing_core` 0.10.2) from each program to its root package, so the program owns that package and everything it requires: `tap-web` and `tap-web (web task b)` to the pypi package `tap`, `gunicorn` and `gunicorn (web task b)` to the pypi package `gunicorn`, `PostgreSQL database instance` to its apk package. A package outside every closure belongs to the container that runs its image, with all the container's programs involved (the base's reach). The builder confirms each target package exists in the seed; a target that does not is left out, and its findings stay on the container.

**The Searches.** Two `module` Searches bound to the `stackarmor_vdr` runners by key: `PAIN Findings` (`tap_plugin.stackarmor_vdr.searches.pain:stackarmor-pain`) and `PAIN Assets` (`tap_plugin.stackarmor_vdr.searches.pain:stackarmor-assets`). The weights, thresholds, EPSS thresholds and scheme are left at the runners' defaults, which is where the memo's governed calibration lives; the Searches override only the class (`d`, assumed).

**The plugins.** The instance's boot profile installs `stackarmor_vdr` and `fedramp_20x_vdr` at releases that ship the runners.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-pain-profiles-1 | Every Program Stamped | Proposed | Every program the inventory seeds has one `asset_profile` stamp per the table, with a `PROFILES_PROGRAM` edge to it and one `USES_ARCHETYPE` edge, and no host, container or instance has a stamp. | The roll-up is computed. |
| req-rampart-20x-playground-pain-profiles-2 | Stamps Name Catalog Archetypes | Proposed | Every stamp's `USES_ARCHETYPE` edge targets an archetype node that `stackarmor_vdr` seeds. | The playground seeds no archetype of its own. |
| req-rampart-20x-playground-pain-profiles-3 | No Override Stamped | Proposed | No seeded stamp carries `cr`, `ir` or `ar`. | |
| req-rampart-20x-playground-pain-profiles-4 | Root Packages Seeded | Proposed | Each program in the table above has a `RUNS_PACKAGE` edge to its root package, and each edge's target exists in the seed. | A missing target is left out and reported. Built: the four edges of `inventory-software` only. The PostgreSQL edge (to `postgresql-18` 18.6-r5, which exists) is left out because it would draw an apk package on the Overview graph, which `req-rampart-20x-playground-govcloud-layout-36` pins to the two Python roots; its findings stay on the container. |
| req-rampart-20x-playground-pain-profiles-5 | Two Searches, Runner Keys Exact | Proposed | `PAIN Findings` and `PAIN Assets` are `module` Searches with the runner keys above, and each declares only inputs the runner's schema declares. | |
| req-rampart-20x-playground-pain-profiles-6 | Plugins Installed | Proposed | The boot profile installs `stackarmor_vdr` and `fedramp_20x_vdr`, and the seed imports against the releases that ship the runners. | The demo record pins `stackarmor_vdr` v0.1.0 by commit with the install credential `stackarmor_vdr` (the repository is private) and seeds `fedramp_20x_vdr` and `stackarmor_vdr` before this plugin. The ci record installs neither and seeds one step per bundle, every bundle but `pain`; `stackarmor_vdr` is therefore not in `depends_on`, because the ci record's coherence check demands every declared dependency, optional or not. |
| req-rampart-20x-playground-pain-profiles-7 | Reach Is Recorded | Proposed | The build report records, read from a run of `PAIN Findings`, the number of rows by `owner_kind` and by `profile_source` (`override`, `archetype`, `container`, `unclassified`). The bundle stores no count. | A stored count goes stale on every re-import. The expected result is mostly `container`, and the root packages move some to `archetype`. |
| req-rampart-20x-playground-pain-profiles-8 | The System Is Unchanged | Proposed | Adding the stamps changes no existing node or edge: a program has the same fields and dimensions with or without them, and a stamp adds no team or dataclass (a program keeps its `dataclass.action`). | Ruled by George, 2026-10-21. |

### PAIN Page
----
RID: `req-rampart-20x-playground-page-pain`

Status: `Superseded`

The page `/playground/pain` is deleted; its two tables (`Findings` over `PAIN Findings`, `Assets` over `PAIN Assets`) sit on `/playground/stackarmor` (`req-rampart-20x-playground-page-stackarmor-6`). The rows below that concern the tables still hold there; rows 1, 2 and 6 are about the page and are superseded.

The page shows PAIN for each finding on each owner (a program, or the container that runs its image), and the roll-up of programs' profiles for each asset. Route `/playground/pain`; the page is named `PAIN`, also its breadcrumb. It carries a title and tables only (`no-explanatory-text-on-pages`, ruled 2026-10-20).

#### Implementation

Two bands under the title panel, each a standard table panel bound by `USES_SEARCH` to one Search of `req-rampart-20x-playground-pain-profiles`:

1. `Findings`, over `PAIN Findings`: the fields `vuln_id`, `component`, `owner`, `owner_kind`, `pain`, `word`, `c`, `i`, `a`, `cr`, `ir`, `ar`, `profile_source`, `column` and `deadline_hours`, titled Vuln ID, Component, Owner, Owner Kind, PAIN, Word, C, I, A, CR, IR, AR, Profile Source, Exposure Column and Deadline Hours, with the vulnerability id a link to the CVE page (`/playground/vulnerabilities/cve?vuln_id=...`) and the owner's name a link to its page when it has one.
2. `Assets`, over `PAIN Assets`: the asset's name as a link, the maximum `cr`, `ir` and `ar` of its programs, the program count and the classified count, titled Asset, CR, IR, AR, Programs and Classified.

Both tables have a quick filter and paging. Every heading and column title is in Title Case.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-pain-1 | Route Serves | Superseded | `GET /playground/pain` returns 200 and the page is in navigation. | |
| req-rampart-20x-playground-page-pain-2 | Title Then Two Tables | Superseded | Under the title panel, band one is the findings table and band two the assets table. | |
| req-rampart-20x-playground-page-pain-3 | Each Table Reads Its Search | Proposed | Each table panel is bound by `USES_SEARCH` to its own Search, and its config names only fields the runner returns. | |
| req-rampart-20x-playground-page-pain-4 | Links Open Their Pages | Proposed | In the findings table the Vuln ID column shows the CVE id and opens the CVE page, and the Component and Owner columns open the object page of the entity, the link template filling the entity type from the row's `component_type` and `owner_type`. | `PAIN Findings` returns `cve`, `component_type`, `owner_type` and `container_type` from `stackarmor_vdr` v0.3.2. The assets table links nothing: `PAIN Assets` returns no entity type. |
| req-rampart-20x-playground-page-pain-5 | Filter And Paging | Proposed | Both tables have a quick filter and paging. | |
| req-rampart-20x-playground-page-pain-6 | No Prose | Superseded | The page carries a title and tables only. | |
| req-rampart-20x-playground-page-pain-7 | Title Case | Proposed | Every panel name, panel title and column title is in Title Case. | |

#### Future

A PAIN-by-level chart and a count of findings on unclassified programs; an hourly snapshot of the findings table through the search-snapshot collector pattern once the table is worth tracking over time.

### VDR Reports Page
----
RID: `req-rampart-20x-playground-page-vdr-reports`

Status: `Proposed`

The VDR reports, showing vulnerabilities against their remediation SLA: what is past due, what is due soon,
what is comfortably inside.

#### Implementation

Route `/playground/vdr-reports`; Searches that filter on `remediation_due_at` against a stated reference
date and group by `pain`; existing table and summary panels. No arithmetic outside Gryphon.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-vdr-reports-1 | Route Serves | Proposed | `GET /playground/vdr-reports` returns 200 and lists each seeded `vdr_report`. | |
| req-rampart-20x-playground-page-vdr-reports-2 | Past Due Visible | Proposed | The page separates findings past due from those not yet due, on the bundle's reference date. | |

### Web And DB Internals Page
----
RID: `req-rampart-20x-playground-page-internals`

Status: `Backlog`

The internal processing of TAP's web and db applications. Deferred until the v0 pieces are on the board.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-internals-1 | Specified Before Built | Backlog | A requirement with ACIDs replaces this row before any work starts. | |

### Data Flow Pages
----
RID: `req-rampart-20x-playground-page-dataflows`

Status: `Backlog`

Data flows for management, user interaction and deployment. Deferred.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-dataflows-1 | Specified Before Built | Backlog | A requirement with ACIDs replaces this row before any work starts. | |

### KSI Page
----
RID: `req-rampart-20x-playground-page-ksi`

Status: `Backlog`

A KSI implementation view over `fedramp_20x_ksi`. Deferred until after VDR.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-ksi-1 | Specified Before Built | Backlog | A requirement with ACIDs replaces this row before any work starts. | |

### VDR Ranking
----
RID: `req-rampart-20x-playground-ranking`

Status: `Backlog`

A ranking process over VDR findings. Likely needs its own plugin; where it lives is decided when it is
reached, and not before.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-ranking-1 | Home Decided First | Backlog | The owning plugin is chosen before any ranking logic is written; none is written in this plugin. | |

### Dependabot Pull
----
RID: `req-rampart-20x-playground-dependabot-pull`

Status: `Proposed`

Pull the live Dependabot alerts for `unified-systems-com/tap` up front, and use what they contain to decide what
a vulnerability or finding entry carries. Scope is `tap` only (ruled 2026-10-13); other repositories and
organizations are later. The playground adds no collector and no model: the alert model belongs in
`github-core-tap` (`#68`), by a reviewed PR that is a prerequisite of this requirement, in the shape of its
`code_scanning_alert`. The pull is then run from `github_core`'s own collector with its existing credential.

**Observed 2026-10-13** (read-only sample through the GitHub API; the first run loaded the grid): 48 alerts,
all in `tap`, 46 fixed and 2 open, all Python (`pip`) packages, every alert with a CVE. Each alert carries the
GHSA and CVE ids, a summary, `severity` and a CVSS vector and score, CWEs, the package and its ecosystem, the
manifest path, runtime or development scope, direct or transitive, the vulnerable range and first patched
version, created, fixed and dismissed times and state, and an EPSS value. It does **not** carry the VDR
evaluation fields (`pain`, `internet_reachable`, `is_kev`) or an SLA; an evaluation step would have to supply
those. The sample holds no OpenSSL alert: OpenSSL arrives through code scanning (see the vulnerabilities page).

#### Implementation

Prerequisite, in `github-core-tap` (its own PR, not this repository): the Dependabot alert model and collector
already specified there as `req-github-core-dependabot-alerts` (Proposed) and tracked by
`unified-systems-com/github-core-tap#68`, open and unassigned as of 2026-10-13. That requirement keys the model on
repository and alert number and does not yet say how it links to a finding. Ruled 2026-10-13: every source drops in
behind one generic finding, the shape `github-core-tap#89` gives code scanning. One `compliance_core__compliance_finding`
is minted per alert; the source-specific alert (`github_core__dependabot_alert`, as `code_scanning_alert` is for
code scanning) is a detail node linked to it by `DETAILS_FINDING__github_core`; the repository is placed on the finding by
the `compliance_core` edge `CARRIES_COMPLIANCE_FINDING__compliance_core`. One query then spans Dependabot, Trivy, Grype and SonarCloud. The generic finding
is thin (name, summary, description, open or resolved), so severity, CVE and dates live on the detail node and the VDR
evaluation fields on `vdr_finding`. Ruled 2026-10-13: the placement edge is `CARRIES_COMPLIANCE_FINDING`, the name the `github_core` manifest and
`compliance_core` already use; `#89`'s body says `HAS_COMPLIANCE_FINDING` and is the one to correct. Here: the
collector run is by hand, against `tap`, and its output is the data the finding-entry decision is made from.

**Decided from the pulled data (2026-10-14).** `github_core` v0.13.0 mints one `compliance_core__compliance_finding`
per alert with `source` `github_core`, `source_key` `<owner/repo>#dependabot#<n>` and status open exactly when the
alert is open; the `dependabot_alert` detail node (keyed on `full_name` and `number`, every state kept) hangs off it
by `DETAILS_FINDING`; the repository carries it by `CARRIES_COMPLIANCE_FINDING`, and the workflow whose manifest
holds the dependency, or the action the package is, carries it too. Severity, CVSS, CWEs, versions and dates stay on
the detail node. EPSS is not a column; it survives only inside the stored raw alert (`configuration`).

**How the pull ran (2026-10-13).** The collector's configuration is one shared envelope that names the owner and no
repositories, so the run covered the whole organization (34 repositories, about 14,000 nodes, 12 minutes) and was then
purged down to the examples. Until partial collections exist (`github-core-tap#216`), every refresh is organization-wide.
The code scanning alerts of `tap` are part of what the demo keeps from such a run (ruled 2026-10-14); they were purged
in the first cleanup by mistake and are pulled again.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-dependabot-pull-1 | Model Exists First | Proposed | The Dependabot alert model of `github-core-tap#68` is released before any pull is run. | Prerequisite, other repository. Met: released as `github_core` v0.13.0. |
| req-rampart-20x-playground-dependabot-pull-2 | Tap Only | Proposed | After the pull and its cleanup, the grid holds Dependabot and code scanning alerts for `unified-systems-com/tap` and no other repository's alerts or data. | A pull is organization-wide until `github-core-tap#216`; the cleanup is what makes this true. |
| req-rampart-20x-playground-dependabot-pull-3 | Entry Decided From Data | Proposed | The fields a finding entry carries are recorded in this spec, from the pulled alerts, before `mock-findings` is built. | The mapping of alert fields to `vdr_finding` is the open decision. |
| req-rampart-20x-playground-dependabot-pull-4 | No Code Here | Proposed | The playground package contains no collector and no script that loads alerts. | |
| req-rampart-20x-playground-dependabot-pull-5 | One Generic Finding | Proposed | Each pulled alert is one `compliance_core__compliance_finding` with its `dependabot_alert` detail node behind it, not a Dependabot-specific finding type. | Follows `github-core-tap#89`; placement edge is `CARRIES_COMPLIANCE_FINDING`. |
| req-rampart-20x-playground-dependabot-pull-6 | Code Scanning Kept | Proposed | The grid holds the code scanning alerts of `unified-systems-com/tap` (Trivy, Grype, SonarCloud) alongside the Dependabot alerts, and any cleanup of a wider pull keeps them. | Ruled 2026-10-14: the vulnerabilities page reads them. |
| req-rampart-20x-playground-dependabot-pull-7 | Detection Time From The Producer | Proposed | Every seeded finding carries `first_detected_at`: a finding made from a GitHub alert takes the alert's own `created_at`, and a finding made from the SBOM takes the SBOM document's `produced_at` (the producer's record, never the time the grid saw it), so the deadline and overdue Searches have a clock to count from. | Without it every finding reads `detection time unobserved` and no deadline is computed (`req-fedramp-20x-vdr-deadlines-3`). The two bundles are re-versioned (new batch ids) so a stack that already imported them takes the change. |

## Reference data

| Document | Contents | Seeded by |
| --- | --- | --- |
| `grift/keystone.grift.json` | The keystone node | `req-rampart-20x-playground-keystone` |
| `grift/dimensions.grift.json` | The `inventory` and `dataclass` dimension nodes | `req-rampart-20x-playground-dimensions` |
| `grift/mock-inventory.grift.json` | Mocked GovCloud resources | `req-rampart-20x-playground-mock-inventory` |
| `grift/mock-findings.grift.json` | Mocked `vdr_finding` and `vdr_report` rows | `req-rampart-20x-playground-mock-findings` |
| `grift/security-alerts.grift.json` | Captured batch: the `tap` code scanning and Dependabot alerts (all states), their generic findings and the `tap` repository, from a live `github_core` run of 2026-10-14. Not yet registered in `[grift]`: it needs `github_core` and `compliance_core` in `depends_on` first | `req-rampart-20x-playground-dependabot-pull` |
| `grift/pages.grift.json` | The four pages, their Searches and panel edges | the four `page` requirements |
| `grift/inventory-entities.grift.json` | The programs and the container's certificate and key halves the inventory tables need beyond the mock inventory | `req-rampart-20x-playground-inventory-tables` |
| `grift/application-flow.grift.json` | The ECS container of each web task, the five application flows (keyless; the customer's, the database's, the administrator's, the laptop's and the puller's, each stamped with one `dataclass.customer` or `dataclass.infra` value, and with `dataclass.action: transmit`) and the RUNS_TASK, RUNS_CONTAINER, RUNS_IMAGE, RUNS_PROGRAM (including the RDS instance to the PostgreSQL program), APPLICATION_FLOW_SOURCE and APPLICATION_FLOW_DESTINATION edges (needs computing_core with the application flow types) | `req-rampart-20x-playground-govcloud-layout-13`, `-14`, `-15`, `-20`, `-21` |
| `grift/inventory-page.grift.json` | The `/playground/inventory` page, its seven table panels and their Searches | `req-rampart-20x-playground-page-inventory` |
| `grift/classification-mapping.grift.json` | The four classification-mapping Searches, their four table panels, the hourly Schedule and its `SCHEDULED_TARGET` edge | `req-rampart-20x-playground-classification-mapping` |
| `grift/pain.grift.json` | The program stamps (`asset_profile` nodes and `PROFILES_PROGRAM` edges), the `RUNS_PACKAGE` root packages, the two PAIN Searches and the two PAIN table panels (placed on the StackArmor page) | `req-rampart-20x-playground-pain-profiles`, `req-rampart-20x-playground-page-pain` |
