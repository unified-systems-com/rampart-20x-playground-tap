# Double-Tap TAP Internals View Specification

**A standalone visualization of what is inside a running TAP instance: its main applications, the Django layer
under them, the plugins loaded into it, and the collectors, scheduler and registries that move facts around.**

This file is written to leave the playground. It names no AWS account, no demo customer and no playground
page; the playground reaches it through one navigation target from the TAP application in the host elevation
(`spec-rampart_20x_playground-host-view.md`). Its requirement identifiers use the `req-double-tap-internals-*`
prefix so the file can move into the planned `double-tap` plugin without renaming anything.

## Philosophy

The host elevation ends at a box labelled as the TAP application. This view is what is inside that box. A
viewer who zooms in sees the large parts of TAP first (the grid, the web layer, the visualization layer, the
collector runtime), then the Django framework and its add-ons underneath them, then the plugins loaded into
this instance, then the machinery that runs collectors on a schedule and the registries that every part
consults.

The view is built for the design phase. The point of this round is to decide which node types and edge types
are needed to draw TAP's own structure, not to build an extractor. The nodes are produced once, by AI reading
the repository, and held as a static batch. A deterministic extractor (AST parsing, tree-sitter) replaces that
batch later without changing the view, because the view reads only the grid.

Two kinds of node feed the view, and the view must not blur them. Some of TAP's internals are already on its
own grid as real nodes written by the running instance: the `collector`, `schedule`, `schedule_fire` and
`collection_job` types of `tap_cares`. The rest (applications, modules, registries, plugins, Django add-ons)
have no node type today. For those the grid has nothing to read, so this spec proposes where they come from.

**Provenance markers.**
*Observed* (read in the `rampart-pg` checkout of `unified-systems-com/tap` on 2026-10-14, not run):
`INSTALLED_APPS` in `tap/settings.py`; `architecture.md` § Subsystems; `tap/registry.py` and every `Registry(`
and `ScopedRegistry(` construction under `tap*`; `tap_cares/registry.py`, `tap_cares/models.py`,
`tap_cares/specs/spec-tap-cares-scheduler.md`, `tap_cares/task_backend.py`; the two `register_collector(`
calls under `_dev-plugins`; the dependency list in `pyproject.toml`; `computing-core-tap` v0.5.0 node and
edge types as summarized in the host-view spec.
*Designed* (this spec's own claims, unbuilt and untried): every requirement below.

## Goals

| # | Name | Description |
| :---: | --- | --- |
| 1 | Big Parts First | The first thing a viewer sees inside TAP is its main applications, sized and placed so their relationships read at a glance. |
| 2 | Layers Underneath | The Django framework and its add-ons sit beneath the applications they serve, as their own layer. |
| 3 | Plugins And Machinery | Loaded plugins, collectors, the scheduler and the registries each get a section. |
| 4 | Standalone | The view depends only on grid data and tap_viz configuration, so it moves into `double-tap` unchanged. |
| 5 | Sorted Types | The round ends with a decided list of node and edge types, each with an owner, and nothing minted beyond it. |
| 6 | Replaceable Extraction | AI-produced nodes carry enough provenance to be replaced by a deterministic extractor without touching the view. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-double-tap-internals-view | [Application Elevation](#application-elevation) | Proposed | The elevation below the host view: TAP's own structure |
| req-double-tap-internals-apps | [Main Applications](#main-applications) | Proposed | The Django apps of TAP, as the first and largest layer |
| req-double-tap-internals-django | [Django Layer](#django-layer) | Proposed | Django itself and the add-ons TAP installs |
| req-double-tap-internals-plugins | [Loaded Plugins](#loaded-plugins) | Proposed | The plugins installed into this instance |
| req-double-tap-internals-runtime | [Collectors, Scheduler And Registries](#collectors-scheduler-and-registries) | Proposed | The machinery section |
| req-double-tap-internals-code | [Code Nodes](#code-nodes) | Proposed | How modules, classes, functions and variables enter the grid |
| req-double-tap-internals-standalone | [Standalone Rule](#standalone-rule) | Proposed | The view survives a move into `double-tap` |
| req-double-tap-internals-extraction | [AI Extraction And Provenance](#ai-extraction-and-provenance) | Proposed | How the nodes are produced now and replaced later |
| req-double-tap-internals-check | [Reconciliation Checks](#reconciliation-checks) | Proposed | Counts on the page that agree with the live instance |
| req-double-tap-internals-gaps | [Recorded Gaps](#recorded-gaps) | Proposed | What the grid lacks, to be settled before anything is minted |
| req-double-tap-internals-deferred | [Deferred](#deferred) | Proposed | Compound edges, function-level calls, deeper zooms |

### Application Elevation
----
RID: `req-double-tap-internals-view`

Status: `Proposed`

The application elevation is reached by double-tapping the TAP application program in the host elevation. It is
a separate elevation (a tap_viz Elevation entity with its own layout), not a nested layer of the host
elevation, because its subject is a different kind of thing: software structure rather than infrastructure.

#### Implementation

The view has four bands, top to bottom:

1. The main applications (`req-double-tap-internals-apps`), large, in the centre of the canvas.
2. The Django layer (`req-double-tap-internals-django`), a band directly beneath, spanning the width.
3. The plugins section (`req-double-tap-internals-plugins`) to one side.
4. The machinery section (`req-double-tap-internals-runtime`) to the other: collectors, the scheduler and the
   registries.

Zoom expands detail the same way the earlier elevations do: at the entry zoom each application is one box with
its name; deeper, an application opens to its sub-systems; deeper still, to modules. Function-level detail is
deferred (`req-double-tap-internals-deferred`).

#### Acceptance Criteria

- The application elevation has its own entry in the elevation order and is reached by double-tap from the TAP
  application node; no page other than the projection is needed.
- At the entry zoom a viewer sees only the main applications, the Django band and the two sections, each with a
  heading.
- Nothing on the view names the playground, an AWS account or a customer.

### Main Applications
----
RID: `req-double-tap-internals-apps`

Status: `Proposed`

The first layer is the ten parts of TAP's own code, read from `INSTALLED_APPS` and `architecture.md`
§ Subsystems: `tap` (the project core), `tap_boot`, `tap_health`, `tap_auth`, `tap_grid`, `tap_plugins`,
`tap_cares`, `tap_api`, `tap_web`, `tap_viz`.

#### Implementation

Each is a node with a one-line purpose taken from `architecture.md`, so the description is TAP's own wording
rather than a new one. The names a viewer expects to see large are `tap_grid` (everything depends on it),
`tap_web` and `tap_viz` (the visible layers), `tap_cares` (the collector runtime) and `tap_plugins`.

Load order in `INSTALLED_APPS` is meaningful (`tap_boot` first, `tap_auth` before `tap_grid`, `tap_cares` before
the plugins, `tap_api` after them) and is carried as a property on the node, not drawn as edges, until the
dependency edges are decided (`req-double-tap-internals-gaps`).

Sub-systems named in the same sources become children when the viewer zooms: in `tap_grid` the service layer,
Gryphon, GRIFT, keystone, reconciliation and history; in `tap_cares` the collector runtime, the scheduler, the
secrets subsystem and the task backend; in `tap_viz` the projection, elevation and layout runtime.

#### Acceptance Criteria

- All ten parts appear, each exactly once.
- Each box shows its name; its purpose appears on hover or at a deeper zoom.
- A part's children appear only when the viewer zooms in, and the parent box stays visible around them.

### Django Layer
----
RID: `req-double-tap-internals-django`

Status: `Proposed`

Beneath the applications is a band for what TAP is built on: Django itself and the add-ons it installs.

#### Implementation

Two groups. First, Django's built-in apps from `INSTALLED_APPS` (`admin`, `auth`, `contenttypes`, `sessions`,
`messages`, `staticfiles`, `postgres`, `sites`). Second, the third-party packages: `django-simple-history`
(audit trail), `django-allauth` (login engine), `django-ninja` (API), `steady-queue` (task backend and the
once-a-minute scheduler tick), `whitenoise` and `gunicorn` (serving), `psycopg` (database driver), and the
smaller libraries the code leans on (`croniter`, `lark`, `jsonschema`, `webauthn`).

Each add-on sits under the application that uses it, by a "used by" relationship, so `steady-queue` is
visibly under `tap_cares`, `django-allauth` under `tap_auth`, `django-ninja` under `tap_api`,
`django-simple-history` under `tap_grid`. Whether an add-on that several applications use is drawn once or per
user is open (Q7).

#### Acceptance Criteria

- Django's built-in apps and the third-party packages are visually distinct groups.
- Every package named in this requirement is present and sits under at least one application.
- The package set is read from the dependency declaration, not typed in by hand (`req-double-tap-internals-extraction`).

### Loaded Plugins
----
RID: `req-double-tap-internals-plugins`

Status: `Proposed`

A section showing the plugins installed into this instance.

#### Implementation

One node per plugin, labelled with its slug and release. The set is what the instance's boot record installs
(`TAP_PLUGINS`), the same list the instance's own bill of materials carries. Each plugin shows the kinds of
thing it contributed: node types, edge types, collectors, panel types, searches. Plugins connect to the
applications they extend (`tap_plugins` loads them; `tap_grid`'s registries receive their types; `tap_cares`
receives their collectors; `tap_web`'s panel registry receives their panels).

No node type for "an installed plugin" exists in `tap_plugins` today: the search over `tap_plugins`, `tap_grid`
and `tap_boot` found only the manifest dataclasses (`PluginManifest` and its entries), which are not graph nodes.
That is the first entry in `req-double-tap-internals-gaps`.

#### Acceptance Criteria

- The plugin list on the view equals the plugin list in the instance's boot record.
- Each plugin links to the applications it extends.
- A plugin that contributes no collector shows no collector.

### Collectors, Scheduler And Registries
----
RID: `req-double-tap-internals-runtime`

Status: `Proposed`

The machinery section has three groups.

#### Collectors

One box per collector registered in the collector registry. The registry is keyed `scope:key`, and the two
registrations observed in `_dev-plugins` are `aws_core:boto3` and `github_core:github_core`. The `collector`
node type already exists in `tap_cares` and is written by the running instance when a collector registers, so
these are real nodes the view reads rather than nodes this spec adds. A collector shows the schedules aimed at
it and its recent jobs, using the existing relationships: `schedule --SCHEDULED_TARGET--> collector`,
`collector --HAS_COLLECTION_JOB--> collection_job`, `schedule --HAS_FIRED--> schedule_fire`,
`schedule_fire --TRIGGERED_JOB--> collection_job`.

#### Scheduler

The scheduler is the minute-resolution tick: one `@recurring` task in `tap_cares/task_backend.py` (the file
states it declares exactly one) that calls the schedule evaluation, which fires collectors through the
collection runtime. It is drawn as one component with the `schedule` nodes attached to it. Its place among the
Django add-ons is that it runs on `steady-queue`.

#### Registries

The registries built long ago and rarely looked at. Observed by reading every `Registry(` and `ScopedRegistry(`
construction: the meta-registry that lists the others; the entity-model registry; the search-runner registry;
the edge-identity registry; five constraint registries in `tap_grid/constraints.py` (node constraints, edge
constraints, edge property schemas, edge default dimensions, internal-only edge types); the health-probe
registry; the panel-type registry; the collector registry; and the secret registry. That is thirteen. Each
carries a title, a description and a creating module, which is exactly what a node for it needs.

The registries are drawn as a group, each linked to the application that creates it and to the application
that reads it most, with the meta-registry at the centre because it enumerates the rest. The secret-source
table in `tap/secret_sources.py` is a plain module dictionary rather than a registry class and is left out of
the group until Q5 is answered.

#### Acceptance Criteria

- Every collector node on the live grid appears, and no collector appears that is not a node there.
- The scheduler is one component, not one per schedule; schedules attach to it.
- The registry count on the page equals the number of entries in the live meta-registry (`req-double-tap-internals-check`).

### Code Nodes
----
RID: `req-double-tap-internals-code`

Status: `Proposed`

The grid has no way to say "this module" or "this function". `computing_core` (v0.5.0) has `program`, `file`,
`host` and the network types, and four edges; it has no module, class, function or variable.

#### Implementation

For this round the proposal is the smallest vocabulary that draws the view, added to `computing_core` as a
continuation (the decision to start a programming plugin later is not taken here):

- `code_module`: a Python package or module; properties: dotted name, file path, kind (package or module).
- `code_symbol`: a class, function or variable defined in a module; properties: name, kind (class, function,
  variable), signature or type text where the source gives one.
- Main applications and registries are `code_module` and `code_symbol` nodes respectively, distinguished by a
  `role` the view reads, rather than additional types, until the roles prove they need their own shape (Q1).

Edges proposed, names non-binding and subject to the plugin edge-naming rule: a module contains a module or
symbol; a module imports a module; a symbol is registered in a registry; an application uses a package. Which
of these are ordinary edges and which would ever sit in a compound stack is answered by the rule already in
use: if the edge would never be included in a compound-stack, it is a normal edge.

At this round only module-level granularity is populated. Function and variable nodes are defined so the
types are settled, and populated when compound edges allow the calls between them to be drawn
(`req-double-tap-internals-deferred`).

#### Acceptance Criteria

- The proposal is filed as one issue against `computing-core-tap`, naming every proposed type and edge and
  marking each as settled or open.
- No node or edge of these types is written to a grid before the issue is settled.

### Standalone Rule
----
RID: `req-double-tap-internals-standalone`

Status: `Proposed`

The view must work in an instance that has no AWS plugin, no playground plugin and no demo data.

#### Implementation

Everything the view needs comes from three places: the node and edge types in the grid, the tap_viz
projection, elevation and layout configuration, and a page that hosts the panel. The projection selects by node
type and `role`, never by the name of any customer or account. The entry point is a navigation target on the
`program` node that represents a TAP application, so the host elevation needs no knowledge of the internals
view beyond that target.

#### Acceptance Criteria

- Loading the batch and the view configuration into an instance whose boot record installs only the types the
  view uses renders the full view.
- Searching the view's projection, layouts and elevation for `aws`, `rampart` or `playground` returns nothing.
- The only link from the host elevation to this view is one navigation target.

### AI Extraction And Provenance
----
RID: `req-double-tap-internals-extraction`

Status: `Proposed`

AI reads the repository and writes the nodes and edges once. The result is held as a static batch.

#### Implementation

Each extracted node records where it came from: the source file path, the commit it was read at, and that it
was produced by AI extraction rather than parsed. The batch is regenerated, not edited, so a later
deterministic extractor produces the same shape and replaces it. The package set for the Django layer is read
from the dependency declaration, the application list from `INSTALLED_APPS`, and the registries from the
`Registry(` constructions, because those three sources are structured enough that a deterministic reader
exists today; the AI step is for the sub-systems, the "used by" relationships and the one-line purposes.

Where this batch lives (in the playground repository for now, or in the future `double-tap` plugin) is Q3.

#### Acceptance Criteria

- Every extracted node names its source file and the commit.
- The batch can be regenerated from the repository without hand edits.
- A node whose source file no longer exists at the recorded commit is detectable from its own properties.

### Reconciliation Checks
----
RID: `req-double-tap-internals-check`

Status: `Proposed`

The earlier elevations show that numbers add up. This view has the same obligation for the counts it can check
against the running instance.

#### Implementation

Three checks, shown as a small strip on the page: the registry count against the live meta-registry; the
collector count against the `collector` nodes on the grid; the plugin count against the boot record. A check
that disagrees is shown as disagreeing, not hidden. Whether Gryphon expresses the grid-side counts directly is
not yet tried; the projection's JavaScript fallback is used if it does not.

#### Acceptance Criteria

- Each of the three counts appears with the number it was compared against.
- Adding a collector to the instance changes both numbers and the check stays agreeing.

### Recorded Gaps
----
RID: `req-double-tap-internals-gaps`

Status: `Proposed`

What the view needs and the grid does not have. Nothing here is minted; each is discussed first.

| Gap | Detail |
| --- | --- |
| No installed-plugin node | Plugins exist as manifests, not as graph nodes, in `tap_plugins`. |
| No application, module, class, function or variable node | See `req-double-tap-internals-code`. |
| No Django app or package node | `computing-core#33` proposes `package` and `library` types; whether an add-on is a `library` there is open. |
| No registry node | Registries are Python objects; their title, description and creator would populate a node. |
| Containment and dependency edges | `computing_core` has four edges and no general containment family; the plan mentions one. |
| "Used by" and "extends" edges | Neither exists. |
| `fedramp_20x_ksi` types | Not used (standing instruction); nothing in this view needs them. |
| Compound edges | Not implemented; `PR 1021` proposes the shape. |

#### Acceptance Criteria

- Each gap has a filing against the owning plugin or a decision recorded here before any node of that kind is
  written.

### Deferred
----
RID: `req-double-tap-internals-deferred`

Status: `Proposed`

Not in this round: function-level and variable-level nodes populated; calls between components (the first
compound edges); a runtime-activity overlay showing what the instance is doing now; request-flow animation;
the `double-tap` plugin itself; a deterministic extractor.

## Open Questions

| # | Question |
| :---: | --- |
| Q1 | Are applications and registries `code_module`/`code_symbol` nodes with a `role`, or their own types? |
| Q2 | Does a programming vocabulary start inside `computing_core` now, with a move later, or is the right cut a new plugin from the first commit? |
| Q3 | Where does the extracted batch live while `double-tap` does not exist? |
| Q4 | Which relationships are ordinary edges and which are future compound-stack members? |
| Q5 | Is `tap/secret_sources.py`'s module dictionary a registry for this view? |
| Q6 | Is the loaded-plugin node an `aws_core`-style resource, a `tap_plugins` model, or a `double-tap` type? |
| Q7 | Is a shared add-on (e.g. `jsonschema`) drawn once with several parents, or once per user? tap_viz nesting is single-parent. |

## Sources

Read, not run, on 2026-10-14: `tap/settings.py`; `architecture.md`; `tap/registry.py`; `tap_grid/registry.py`,
`tap_grid/constraints.py`, `tap_grid/edge_identity.py`; `tap_cares/registry.py`, `tap_cares/models.py`,
`tap_cares/task_backend.py`, `tap_cares/specs/spec-tap-cares-scheduler.md`; `tap_health/registry.py`;
`tap_web/registry.py`; `tap_plugins/manifest.py`; `pyproject.toml`; `_dev-plugins/aws_core` and
`_dev-plugins/github_core` `apps.py`; `tap_viz/specs`.
