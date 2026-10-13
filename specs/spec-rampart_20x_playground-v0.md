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

The inventory and findings are **mock data**. They are never presented as collected, and never as an
authorization boundary. The presenter says so; the pages and panels are not adjusted to say it (ruled
2026-10-13).

**Provenance markers.**
*Observed* (read from the named source on 2026-10-13, not run): `fedramp_20x_ksi` v0.3.1 `vdr_finding`
carries `pain`, `internet_reachable`, `likely_exploitable`, `is_kev`, `remediation_sla_days` and
`remediation_due_at`; `github_core` (`main`, plugin_version 0.12.2; latest tag v0.12.2) declares `code_scanning_alert` and no Dependabot model;
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
| req-rampart-20x-playground-nongoals | [v0 Non-Goals](#v0-non-goals) | Proposed | No models, edges, collectors or code; no live AWS; mock is not a boundary |
| req-rampart-20x-playground-boot | [Boot Records](#boot-records) | Proposed | The in-package `ci` record and a demo record, every plugin pinned by commit SHA, local passkeys |
| req-rampart-20x-playground-keystone | [Keystone](#keystone) | Proposed | One keystone node: project name and description |
| req-rampart-20x-playground-dimensions | [Dimensions](#dimensions) | Proposed | Sixteen dimension nodes: the six `inventory` categories and the six `dataclass` classes, with their axes |
| req-rampart-20x-playground-mock-inventory | [Mock Inventory](#mock-inventory) | Proposed | Mocked GovCloud resources from existing `aws_core` / `computing_core` types, on the `design` position |
| req-rampart-20x-playground-mock-findings | [Mock Findings](#mock-findings) | Proposed | Mocked `vdr_finding` and `vdr_report` rows carrying PAIN, SLA and due date |
| req-rampart-20x-playground-dependabot-pull | [Dependabot Pull](#dependabot-pull) | Proposed | One-off pull of `tap`'s Dependabot alerts, via a new model in `github-core-tap`; shapes the finding entry |
| req-rampart-20x-playground-page-landing | [Landing Page](#landing-page) | Proposed | Opens on the system visualization: the GovCloud design as a graph |
| req-rampart-20x-playground-page-inventory | [Inventory Page](#inventory-page) | Proposed | System inventory |
| req-rampart-20x-playground-page-vulnerabilities | [Vulnerabilities Page](#vulnerabilities-page) | Proposed | Vulnerabilities, organized by source, Dependabot first |
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
credential other than the local passkey login. It does not claim that its mocked design is, or models, a
FedRAMP authorization boundary.

#### Implementation

The manifest declares no `[models]` or `[edges]`. `pyproject.toml` lists no dependencies and the
manifest's `depends_on` is empty, because nothing here imports another plugin's Python and the two bundles
written so far use core entity types only; the composed plugins are installed by the `demo` record, not by
pip resolution (the `dcom` shape, whose `ci` record installs itself alone). When the mock inventory and
findings land they seed other plugins' types by string, which is a vocabulary dependency, so `depends_on`
gains those plugins (with a `note`) in the same change (`new-plugin` Tier 1b). The one permitted code path is a programmatic JavaScript
layout, written through the `create-layout` skill, if a page cannot be drawn from data.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-nongoals-1 | No Vocabulary | Proposed | `manage.py plugins` reports `models=0/0 edges=0/0` for the plugin. | |
| req-rampart-20x-playground-nongoals-2 | No Network | Proposed | The plugin's `ci` record contains no collector and no credential, and boots offline. | |
| req-rampart-20x-playground-nongoals-3 | Mock Is Not A Boundary | Proposed | The keystone description says the data is mock and the design is not an authorization boundary. | |
| req-rampart-20x-playground-nongoals-4 | No Dcom On App Entities | Proposed | The keystone, page, panel and Searches seeded by this plugin carry no `dcom` key. | The axis describes the system under design, not the app showing it. |

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
`github_core` (with `git_core`), `compliance_core`, `fedramp_20x_ksi`, `rampart_20x` and this plugin, and
seeds, in dependency order, `administrivia`, `dcom`, the `dimension` bundle of `aws_core`,
`computing_core` and `fedramp_20x_ksi`, and this plugin; those plugins' pages, regions and KSI seed stay out
until a page mounts them. Every plugin is pinned by the **peeled commit SHA** beside its
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
six categories, and `dataclass`, which classifies kinds of data. Both follow `dcom`'s pack shape
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
| `inventory.os` | `inventory: os` | Operating systems and containers. |
| `inventory.secrets` | `inventory: secrets` | Secrets: secret material, keys, certificates, secrets. |
| `inventory.cloud` | `inventory: cloud` | Cloud services: internal AWS capabilities such as Route 53, Secrets Manager, IAM and VPCs that come from the cloud but are not an application, library or OS/container. |
| `inventory.saas` | `inventory: saas` | Third-party SaaS: interconnected cloud systems, including AWS where all of this is hosted and GitHub where the code comes from. |

**The `dataclass` axis.** Names as given by the owner; the meanings are this spec's proposal and are for review.

| Node | Label it defines | Meaning (proposed) |
| --- | --- | --- |
| `dataclass` | axis | The class of data an item holds or handles. |
| `dataclass.customer` | axis (child) | Data that belongs to customers. |
| `dataclass.infra` | axis (child) | Data that belongs to running the infrastructure. |
| `dataclass.customer.data` | `dataclass.customer: data` | Customer data. |
| `dataclass.customer.creds` | `dataclass.customer: creds` | Customer credentials. |
| `dataclass.customer.logs` | `dataclass.customer: logs` | Customer logs. |
| `dataclass.infra.code` | `dataclass.infra: code` | Infrastructure code. |
| `dataclass.infra.secrets` | `dataclass.infra: secrets` | Infrastructure secrets. |
| `dataclass.infra.logs` | `dataclass.infra: logs` | Infrastructure logs. |

By `req-dcom-naming` the label a value node defines is everything before its last dot as the key, and the last
segment as the value, so an entity can carry one `dataclass.customer` value and one `dataclass.infra` value.
That rule says names deeper than axis-and-value "carry no defined meaning"; `dataclass` is two levels deep, so
it leans on that undefined territory (see the review ask). In v0 nothing is stamped with a `dataclass` value:
the nodes exist so classification can start without a vocabulary change.

#### Implementation

`grift/dimensions.grift.json`, one batch of sixteen `dimension` nodes (seven `inventory`, nine `dataclass`),
no edges. Each carries `tap.meta: dimension` and no `dcom` value (dictionary nodes carry no axis value,
`req-dcom-stamping` rule 6). Entity ids are minted once with `scripts/uuid7` and never change. Every node and
the batch carry a description. Queries use the bracketed key form, `n.dimensions["inventory"]`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-dimensions-1 | Sixteen Nodes | Proposed | Importing the bundle yields exactly sixteen `dimension` nodes, with the names in the two tables above. | |
| req-rampart-20x-playground-dimensions-2 | Inventory Enumerates | Proposed | `MATCH (d:dimension) WHERE d.name STARTS_WITH "inventory." RETURN d` returns exactly the six category nodes. | |
| req-rampart-20x-playground-dimensions-3 | No Dot In A Value | Proposed | No value node's last segment contains a dot. | Same constraint as `req-dcom-naming-3`. |
| req-rampart-20x-playground-dimensions-4 | Dictionary Carries No Axis Value | Proposed | None of the sixteen nodes carries an `inventory`, `dataclass` or `dcom` key; each carries `tap.meta: dimension`. | |
| req-rampart-20x-playground-dimensions-5 | Every Node Described | Proposed | Every node and the batch has a non-empty description. | |

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
| req-rampart-20x-playground-mock-inventory-4 | One Category Or None | Proposed | Every mock inventory item carries exactly one `inventory` value from the six categories; a node that fits none (for example pure topology) carries no `inventory` key. | The mapping of existing `aws_core`, `computing_core` and `github_core` types to categories was not checked. A category with no existing type (libraries is the likeliest) is a finding for the owning plugin. |

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

Route `/playground`. One `page` node mounting existing panel types by `USES_PANEL` edge, one Search over
the mock inventory, and a projection through `create-layout` if the arrangement needs one. Graph chrome is
`node_style: icon-badge`. Links to the three pages below. The page does not mount the keystone.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-landing-1 | Route Serves | Proposed | `GET /playground` returns 200 on a booted `demo` stack and renders the design graph. | |

### Inventory Page
----
RID: `req-rampart-20x-playground-page-inventory`

Status: `Proposed`

The system inventory, in six categories: applications, libraries, operating systems and containers, secrets,
cloud services and third-party SaaS. Each category is a section listing the items stamped with that
`inventory` value, each row linking to its entity page.

#### Implementation

Route `/playground/inventory`; six Searches, one per `inventory` value, each filtering on
`n.dimensions["inventory"]`; an existing table panel per section.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-inventory-1 | Route Serves | Proposed | `GET /playground/inventory` returns 200 and renders six sections, one per `inventory` category. | |
| req-rampart-20x-playground-page-inventory-2 | Section Matches Dimension | Proposed | Each section lists exactly the entities whose `inventory` value is that section's category. | |

### Vulnerabilities Page
----
RID: `req-rampart-20x-playground-page-vulnerabilities`

Status: `Proposed`

The vulnerabilities, organized by source. Dependabot is the first source and the first section. The other
sources are the code scanning tools that report on `tap`; on 2026-10-13 these were Trivy (container and OS
packages such as glibc), Grype (every one of its 26 open alerts was for `openssl-fips-provider`) and SonarCloud
(code findings), each shown as its own section. Which findings appear as `vdr_finding` entries, and how a source's
alerts map onto one, is the open decision of `req-rampart-20x-playground-dependabot-pull-3`.

#### Implementation

Route `/playground/vulnerabilities`; one Search and one existing table panel per source section. The Dependabot
section reads the alert model of `req-rampart-20x-playground-dependabot-pull`; the code scanning sections read
`github_core__code_scanning_alert` as `github_core` already collects it, one section per detecting tool. The
mock findings of `req-rampart-20x-playground-mock-findings` are not assigned a section here; where they appear
is left to the finding-entry decision.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-vulnerabilities-1 | Route Serves | Proposed | `GET /playground/vulnerabilities` returns 200 and renders one section per source. | |
| req-rampart-20x-playground-page-vulnerabilities-2 | Dependabot First | Proposed | The first section on the page is Dependabot. | |
| req-rampart-20x-playground-page-vulnerabilities-3 | One Section Per Source | Proposed | Each code scanning tool that has alerts for `tap` has its own section, and no alert appears in two sections. | |

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

**Observed 2026-10-13** (read-only sample through the GitHub API; nothing loaded onto the grid): 48 alerts,
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

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-dependabot-pull-1 | Model Exists First | Proposed | The Dependabot alert model of `github-core-tap#68` is released before any pull is run. | Prerequisite, other repository. |
| req-rampart-20x-playground-dependabot-pull-2 | Tap Only | Proposed | After the pull, the grid holds Dependabot alerts for `unified-systems-com/tap` and no other repository. | |
| req-rampart-20x-playground-dependabot-pull-3 | Entry Decided From Data | Proposed | The fields a finding entry carries are recorded in this spec, from the pulled alerts, before `mock-findings` is built. | The mapping of alert fields to `vdr_finding` is the open decision. |
| req-rampart-20x-playground-dependabot-pull-4 | No Code Here | Proposed | The playground package contains no collector and no script that loads alerts. | |
| req-rampart-20x-playground-dependabot-pull-5 | One Generic Finding | Proposed | Each pulled alert is one `compliance_core__compliance_finding` with its `dependabot_alert` detail node behind it, not a Dependabot-specific finding type. | Follows `github-core-tap#89`; placement edge is `CARRIES_COMPLIANCE_FINDING`. |

## Reference data

| Document | Contents | Seeded by |
| --- | --- | --- |
| `grift/keystone.grift.json` | The keystone node | `req-rampart-20x-playground-keystone` |
| `grift/dimensions.grift.json` | The `inventory` and `dataclass` dimension nodes | `req-rampart-20x-playground-dimensions` |
| `grift/mock-inventory.grift.json` | Mocked GovCloud resources | `req-rampart-20x-playground-mock-inventory` |
| `grift/mock-findings.grift.json` | Mocked `vdr_finding` and `vdr_report` rows | `req-rampart-20x-playground-mock-findings` |
| `grift/pages.grift.json` | The four pages, their Searches and panel edges | the four `page` requirements |
