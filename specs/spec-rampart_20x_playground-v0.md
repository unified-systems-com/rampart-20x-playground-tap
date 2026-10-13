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
panels, Searches and the keystone carry no `dcom` value (ruled 2026-10-13).

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
`remediation_due_at`; `github_core` (`main`, plugin_version 0.12.2; latest tag v0.9.0) declares `code_scanning_alert` and no Dependabot model;
`rampart-20x-tap` and `highbar-tap` carry no release tags.
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
| req-rampart-20x-playground-mock-inventory | [Mock Inventory](#mock-inventory) | Proposed | Mocked GovCloud resources from existing `aws_core` / `computing_core` types, on the `design` position |
| req-rampart-20x-playground-mock-findings | [Mock Findings](#mock-findings) | Proposed | Mocked `vdr_finding` and `vdr_report` rows carrying PAIN, SLA and due date |
| req-rampart-20x-playground-page-landing | [Landing Page](#landing-page) | Proposed | Opens on the system visualization: the GovCloud design as a graph |
| req-rampart-20x-playground-page-inventory | [Inventory Page](#inventory-page) | Proposed | System inventory |
| req-rampart-20x-playground-page-vulnerabilities | [Vulnerabilities Page](#vulnerabilities-page) | Proposed | Vulnerabilities |
| req-rampart-20x-playground-page-vdr-reports | [VDR Reports Page](#vdr-reports-page) | Proposed | VDR reports: vulnerabilities against SLA |
| req-rampart-20x-playground-page-internals | [Web And DB Internals Page](#web-and-db-internals-page) | Backlog | TAP's web and db applications, internal processing |
| req-rampart-20x-playground-page-dataflows | [Data Flow Pages](#data-flow-pages) | Backlog | Management, user interaction and deployment flows |
| req-rampart-20x-playground-page-ksi | [KSI Page](#ksi-page) | Backlog | KSI implementation view |
| req-rampart-20x-playground-ranking | [VDR Ranking](#vdr-ranking) | Backlog | Ranking process; likely its own plugin |
| req-rampart-20x-playground-vuln-pull | [One-Off Vulnerability Pull](#one-off-vulnerability-pull) | Backlog | Pull recent OpenSSL vulnerabilities in through existing code scanning |

### v0 Non-Goals
----
RID: `req-rampart-20x-playground-nongoals`

Status: `Proposed`

The playground contributes no TAP-managed entity types: no models, no edges, no collectors, no panel
types, and no Python beyond what the plugin package requires to install. It makes no AWS calls and holds no
credential other than the local passkey login. It does not claim that its mocked design is, or models, a
FedRAMP authorization boundary.

#### Implementation

The manifest declares no `[models]` or `[edges]`. Every dependency is an install dependency in
`pyproject.toml` and the manifest's `depends_on` is empty, because nothing here imports another plugin's
Python (the `git_serious_double_tap` shape). The one permitted code path is a programmatic JavaScript
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
seeds their bundles in dependency order. Every plugin is pinned by the **peeled commit SHA** beside its
tag (`git ls-remote <url> 'refs/tags/<tag>*'`, the `^{}` line). `rampart_20x` has no tag, so it is pinned
by the SHA of its `main` at the time the record is written, and the record says so in a `note`.
The demo record loads a passkey stored locally, through the mechanism the base TAP instance already offers.
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

The system inventory: every mock resource, grouped by kind, each row linking to its entity page.

#### Implementation

Route `/playground/inventory`; one Search over the mock inventory; an existing table panel.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-inventory-1 | Route Serves | Proposed | `GET /playground/inventory` returns 200 and lists every mock inventory resource. | |

### Vulnerabilities Page
----
RID: `req-rampart-20x-playground-page-vulnerabilities`

Status: `Proposed`

The vulnerabilities: every `vdr_finding`, with PAIN, reachability, KEV, age and the resource it concerns.
It shows every `vdr_finding`, mock or not, without distinction.

#### Implementation

Route `/playground/vulnerabilities`; one Search over `fedramp_20x_ksi__vdr_finding`; an existing table
panel.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-vulnerabilities-1 | Route Serves | Proposed | `GET /playground/vulnerabilities` returns 200 and lists the seeded findings. | |

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

### One-Off Vulnerability Pull
----
RID: `req-rampart-20x-playground-vuln-pull`

Status: `Backlog`

Pull recent OpenSSL vulnerabilities onto the grid through the code scanning data `github_core` already
collects. The owner reports they already arrive that way, so no new model is expected; if one is needed it
is a `github-core-tap` PR. The pull is run by hand from an existing collector, with no collector code here.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-vuln-pull-1 | Existing Alerts Suffice | Backlog | Before any model work, a query confirms the OpenSSL vulnerabilities of interest exist as `github_core__code_scanning_alert` nodes. | Reported, not yet checked. |

## Reference data

| Document | Contents | Seeded by |
| --- | --- | --- |
| `grift/keystone.grift.json` | The keystone node | `req-rampart-20x-playground-keystone` |
| `grift/mock-inventory.grift.json` | Mocked GovCloud resources | `req-rampart-20x-playground-mock-inventory` |
| `grift/mock-findings.grift.json` | Mocked `vdr_finding` and `vdr_report` rows | `req-rampart-20x-playground-mock-findings` |
| `grift/pages.grift.json` | The four pages, their Searches and panel edges | the four `page` requirements |
