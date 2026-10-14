# Rampart 20x Playground TAP Internals Specification

**The third elevation of the playground's system visualization: zooming from the host view into the running
TAP application, to see the server that hosts it, its main parts, the Django layer under them, the plugins
loaded into it, the collectors, scheduler and registries that move facts around, and the secret material it
holds.**

This file follows `spec-rampart_20x_playground-host-view.md`, which ends at the TAP program as a
program on the web container. It inherits the v0 rules (`spec-rampart_20x_playground-v0.md`): the plugin
ships data only (`req-rampart-20x-playground-nongoals`) and every fabricated entity carries `dcom: design`.

## Philosophy

The host elevation ends at a box for the TAP program. This view is what is inside that box. A viewer who
zooms in sees gunicorn, the server TAP runs inside, with its worker processes stacked into one box that shows
how many there are; the large parts of TAP (the grid, the web layer, the visualization layer, the collector
runtime); the Django framework and its add-ons as endpoints those parts point at; the plugins loaded into this
instance; the machinery that runs collectors on a schedule and the registries every part consults; and the
secret material TAP holds, certificates included.

TAP should ship with what it needs to draw itself. Where something inside TAP can be drawn with a generic
node (a running program, a code module, a library, a file, a key), it uses that node, in `computing_core`.
Where TAP has a concept of its own that no generic node expresses (a plugin, a registry, the scheduler), it
gets a node type in TAP core. The view is not a plugin of its own; a `double-tap` plugin is tabled.

The nodes are produced once, by AI reading the repository, and held as a static batch in this repository. A
deterministic extractor (AST parsing, tree-sitter) replaces that batch later without changing the view,
because the view reads only the grid. Some of TAP's internals are already real nodes written by the running
instance (`collector`, `schedule`, `schedule_fire`, `collection_job`); the view reads those rather than
duplicating them.

**Provenance markers.**
*Observed* (read in the `rampart-pg` checkout of `unified-systems-com/tap` on 2026-10-14, not run):
`INSTALLED_APPS` and the settings in `tap/settings.py`; `architecture.md` § Subsystems; `docker/entrypoint.sh`;
`docker/gunicorn.conf.py`; `specs/spec-tap-serving.md`; `tap/serving.py`; `tap/registry.py` and every
`Registry(` and `ScopedRegistry(` construction under `tap*`; `tap_cares/registry.py`, `tap_cares/models.py`,
`tap_cares/specs/spec-tap-cares-scheduler.md`, `tap_cares/specs/spec-tap-cares-secrets.md`,
`tap_cares/task_backend.py`; `tap/secrets_root.py`; the two `register_collector(` calls under `_dev-plugins`;
`pyproject.toml`; `computing-core-tap` v0.5.0 types as summarized in the host-view spec.
*Designed* (this spec's own claims, unbuilt and untried): every requirement below.

## Goals

| # | Name | Description |
| :---: | --- | --- |
| 1 | Big Parts First | The first thing a viewer sees inside TAP is the server and its main parts, placed so their relationships read at a glance. |
| 2 | Endpoints, Not Parents | The Django framework and its add-ons are nodes the parts point at, not boxes the parts sit in. |
| 3 | Workers Counted | The gunicorn workers are one stacked box that shows the real count. |
| 4 | Plugins, Machinery, Secrets | Loaded plugins, collectors, the scheduler, the registries and the secret material each get a section. |
| 5 | Core Draws Itself | TAP's own concepts get core node types; everything else uses generic nodes. |
| 6 | Replaceable Extraction | AI-produced nodes carry enough provenance to be replaced by a deterministic extractor. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-internals-view | [Application Elevation](#application-elevation) | Proposed | The elevation below the host view |
| req-rampart-20x-playground-internals-server | [Server And Workers](#server-and-workers) | Proposed | gunicorn hosts TAP; workers stacked; the queue supervisor beside it |
| req-rampart-20x-playground-internals-apps | [Main Parts](#main-parts) | Proposed | The ten parts of TAP |
| req-rampart-20x-playground-internals-django | [Django Layer](#django-layer) | Proposed | Django and its add-ons as endpoints |
| req-rampart-20x-playground-internals-plugins | [Loaded Plugins](#loaded-plugins) | Proposed | The installed plugins |
| req-rampart-20x-playground-internals-runtime | [Collectors, Scheduler And Registries](#collectors-scheduler-and-registries) | Proposed | The machinery section |
| req-rampart-20x-playground-internals-secrets | [Secret Material](#secret-material) | Proposed | The secrets directory, its files, and certificates |
| req-rampart-20x-playground-internals-types | [Node And Edge Types](#node-and-edge-types) | Proposed | Where each type lives and what is proposed |
| req-rampart-20x-playground-internals-extraction | [AI Extraction And Provenance](#ai-extraction-and-provenance) | Proposed | How nodes are produced now and replaced later |
| req-rampart-20x-playground-internals-check | [Reconciliation Checks](#reconciliation-checks) | Proposed | Counts on the page that agree with the live instance |
| req-rampart-20x-playground-internals-gaps | [Recorded Gaps](#recorded-gaps) | Proposed | What the grid lacks |
| req-rampart-20x-playground-internals-deferred | [Deferred](#deferred) | Proposed | Compound edges, function calls, deeper zooms |

### Application Elevation
----
RID: `req-rampart-20x-playground-internals-view`

Status: `Proposed`

The application elevation is reached by double-tapping the TAP program in the host elevation. It is its
own tap_viz Elevation with its own layout, because its subject is software structure rather than
infrastructure.

#### Implementation

The view has these regions: the server and its stacked workers, with the queue supervisor beside it
(`req-rampart-20x-playground-internals-server`); the main parts (`...-apps`) inside the TAP program; the
Django layer as endpoint nodes (`...-django`); the plugins section (`...-plugins`); the machinery section
(`...-runtime`); and the secrets section (`...-secrets`). Zoom expands detail as the earlier elevations do: at
the entry zoom each part is one named box; deeper, a part opens to its sub-systems, then its modules.
Function-level detail is deferred.

#### Acceptance Criteria

- The elevation is reached by double-tap from the TAP program node and from nowhere else.
- At the entry zoom a viewer sees only named boxes with a heading per region.
- Nothing on the view explains that the data is a mock.

### Server And Workers
----
RID: `req-rampart-20x-playground-internals-server`

Status: `Proposed`

TAP runs inside gunicorn. The picture says so.

#### Implementation

Read from `docker/entrypoint.sh` and `specs/spec-tap-serving.md`: the container's entrypoint `exec`s gunicorn,
so the gunicorn arbiter is the container's first process; gunicorn runs a fixed number of sync workers; each
worker loads `tap.wsgi.application` and serves requests in its own process. So:

- gunicorn is a `program` that hosts the TAP web `program`.
- The workers are drawn as one stacked box, a tap_viz stack, whose count chip is the number of worker
  nodes. Stacked nodes are distinguished from compound-edges by the hyphenated edge names the grid already uses.
- WhiteNoise, which serves static files, is middleware inside the web program, so it is a library
  endpoint of the web program and appears in the Django layer, not as a server.
- The Steady Queue supervisor is a second `program` in the same container, started in the
  background by the entrypoint. It forks one worker per declared queue (one for the scheduler tick, one for the
  default queue). It hosts the collector runtime and the scheduler, and is drawn beside gunicorn.

The worker count in the code is `TAP_WEB_WORKERS`, defaulting to three (`tap/serving.py`). The decision
(George, 2026-10-14) is to show whatever is configured: the batch holds one worker node per configured worker,
so the chip reads three unless the demo configuration sets `TAP_WEB_WORKERS` otherwise. A worker is drawn as a
`program` node inside the gunicorn `program` node; no separate process type is used (see
`req-rampart-20x-playground-internals-types`).

#### Acceptance Criteria

- gunicorn contains the web program; the web program is not drawn in front of or beside gunicorn.
- The stack's count equals the number of worker nodes it holds, and the check strip shows it
  (`req-rampart-20x-playground-internals-check`).
- The queue supervisor is drawn outside gunicorn and inside the container.

### Main Parts
----
RID: `req-rampart-20x-playground-internals-apps`

Status: `Proposed`

Inside the TAP program are its ten parts, read from `INSTALLED_APPS` and `architecture.md` § Subsystems:
`tap` (project core), `tap_boot`, `tap_health`, `tap_auth`, `tap_grid`, `tap_plugins`, `tap_cares`, `tap_api`,
`tap_web`, `tap_viz`.

#### Implementation

TAP is a running `program` (the existing `computing_core` type: a thing running on a computer, code being
executed). Its ten parts are code modules loaded by it, mapped to what they are in Python: packages with a real
`__init__.py`, not programs that run on their own. Each
carries a one-line purpose taken from `architecture.md`. Load order from `INSTALLED_APPS` is a property of the
node, not an edge, until dependency edges are decided. Sub-systems named in the same sources become children on
zoom: in `tap_grid` the service layer, Gryphon, GRIFT, keystone, reconciliation and history; in `tap_cares`
the collector runtime, the scheduler, the secrets subsystem and the task backend; in `tap_viz` the
projection, elevation and layout runtime.

#### Acceptance Criteria

- All ten parts appear, each once, inside the TAP program.
- A part's children appear only on zoom and the parent stays visible around them.

### Django Layer
----
RID: `req-rampart-20x-playground-internals-django`

Status: `Proposed`

Django and its add-ons are library nodes that TAP's parts point at. They are endpoints, not parents: a part
uses a library; the library does not contain the part.

#### Implementation

Two groups of library nodes. Django's built-in apps from `INSTALLED_APPS` (`admin`, `auth`, `contenttypes`,
`sessions`, `messages`, `staticfiles`, `postgres`, `sites`), and the third-party packages from
`pyproject.toml`: `django-simple-history` (audit trail), `django-allauth` (login engine), `django-ninja`
(API), `steady-queue` (task backend and scheduler tick), `whitenoise` (static files), `gunicorn` (server,
drawn as a program per `...-server` and linked to its library entry), `psycopg` (database driver), and
the smaller libraries (`croniter`, `lark`, `jsonschema`, `webauthn`). Each part draws a "uses library" edge to
each library it needs. A library used by several parts is one node with several edges pointing at it.

#### Acceptance Criteria

- Each library appears once, whoever uses it.
- Every library named here has at least one edge from a part.
- The library set is read from the dependency declaration, not typed by hand.

### Loaded Plugins
----
RID: `req-rampart-20x-playground-internals-plugins`

Status: `Proposed`

One `tap_plugin` node per plugin installed into the instance, a new core node type
(`req-rampart-20x-playground-internals-types`).

#### Implementation

The set is what the instance's boot record installs, the same list that is the instance's bill of materials.
Each plugin node is labelled with slug and release and links to what it contributes: collectors, and the
registries that receive its types and panels. It links to the program that loads it. `tap_plugins` today
holds manifest dataclasses (`PluginManifest` and entries), which are not graph nodes, so there is nothing to
read yet; the batch carries the nodes until core writes them.

#### Acceptance Criteria

- The plugin list equals the boot record's install list.
- A plugin that contributes no collector shows none.

### Collectors, Scheduler And Registries
----
RID: `req-rampart-20x-playground-internals-runtime`

Status: `Proposed`

#### Collectors

One box per registered collector, read from the real `collector` nodes. The two observed registrations are
`aws_core:boto3` and `github_core:github_core`. Existing relationships are used as they are:
`schedule --SCHEDULED_TARGET--> collector`, `collector --HAS_COLLECTION_JOB--> collection_job`,
`schedule --HAS_FIRED--> schedule_fire`, `schedule_fire --TRIGGERED_JOB--> collection_job`.

#### Scheduler

One `tap_scheduler` node (new core type), not one per schedule. It is the minute-resolution tick: one
`@recurring` task in `tap_cares/task_backend.py` that evaluates enabled schedules. Schedules attach to it. It
runs inside the Steady Queue supervisor.

#### Registries

One `tap_registry` node (new core type) per registry. Observed by reading every `Registry(` and
`ScopedRegistry(` construction: the meta-registry that lists the others; the entity-model registry; the
search-runner registry; the edge-identity registry; five constraint registries (node constraints, edge
constraints, edge property schemas, edge default dimensions, internal-only edge types); the health-probe
registry; the panel-type registry; the collector registry; and the secret registry. That is thirteen. Each
already carries a title, a description and a creating module, which the node takes as its properties. The
meta-registry is drawn at the centre of the group because it enumerates the others. The module dictionary in
`tap/secret_sources.py` is not a registry class and is not drawn.

#### Acceptance Criteria

- Every `collector` node on the live grid appears and none that is not a node there.
- The registry count equals the live meta-registry's entry count.
- The scheduler is one component; schedules attach to it.

### Secret Material
----
RID: `req-rampart-20x-playground-internals-secrets`

Status: `Proposed`

The view shows that TAP holds secret material, where it lives, and what consumes it. It never shows a value.

#### Implementation

Secrets live off-grid in a mounted secrets directory (`/run/tap-secrets` in the container; `TAP_SECRETS_ROOT`),
as `<key>.secret.json` files whose directory layout carries no meaning
(`req-tap-cares-secrets-files-2`). The secrets themselves are modelled inside that directory on disk: the
directory is a node, each secret file is a `file` node inside it with a role of secret, and the secret
registry (one of the thirteen) is linked to the program that loads from it. Two observed scopes,
`aws_core` (`boto_collector`) and `auth` (a Google login), are named by file; the file contents are not read
by this spec and not drawn.

Certificates are shown at this level, in two places (George, 2026-10-14). The load balancer has a certificate
pulled from the certificate manager: in the account view that is the `aws_acm_certificate` node `aws_core`
already has. The TAP instance has a certificate on the filesystem of its container, held as a `file` node with a
role of certificate, with its key as a separate `private_key` node, presented by gunicorn. Today gunicorn
serves plain HTTP and TLS terminates outside it (`docker/gunicorn.conf.py`, `certfile` and `keyfile` unset), so
the in-container certificate is the design the view shows for gunicorn taking over TLS; the current code does
not use one. `computing_core` has `public_key` and `private_key` but no `certificate` type
(`req-rampart-20x-playground-internals-gaps`).

#### Acceptance Criteria

- No secret value, fingerprint of a private key, or file content appears anywhere in the batch or the page.
- Every secret file node is inside the secrets directory node.
- Two certificates appear: the load balancer's, tied to the certificate-manager node, and the container's,
  tied to gunicorn. Each shows subject, issuer and validity dates, and its key is a separate node.

### Node And Edge Types
----
RID: `req-rampart-20x-playground-internals-types`

Status: `Proposed`

Rulings (George, 2026-10-14): the vocabulary starts in `computing_core` and stays there unless it grows
large; TAP ships the node and edge types it needs to draw itself, so concepts specific to TAP get core types;
the TAP program is shown as a running `program`, so no TAP-specific application type is needed. There is no
`application` type: `program` means a thing running on a computer, code being executed, and a program may hold
several processes.

#### Implementation

In `computing_core` (generic):

- `program` (exists): a thing running on a computer, code being executed. TAP, gunicorn, the gunicorn workers
  and the Steady Queue supervisor are all `program` nodes; nesting expresses "inside". No `application` and no
  `process` type is added.
- `code_module`: a Python package or module. `code_symbol`: a class, function or variable (populated later).
- `library` (and `package`), already proposed in `computing-core-tap#33`.
- `file`, `public_key`, `private_key` exist. `certificate` is a gap for the on-disk certificate.

In TAP core (specific to TAP): `tap_plugin` (owned by `tap_plugins`), `tap_registry` (owned by `tap_grid`),
`tap_scheduler` (owned by `tap_cares`). Slugs are proposals; the plugin-naming rule does not apply to core
types, but the form matches `collector` and `schedule`.

Edges follow `<ACTION>_<OBJECT>` (`req-tap-plugin-edge-naming`; no `HAS_`, `IS_` or trailing preposition) and
are plain edges until a compound edge is wanted: a program hosts a program; a program loads a
module; a module contains a module; a module imports a module; a module defines a symbol; a module or
program uses a library; a program loads a plugin; a plugin contributes a collector; a plugin
populates a registry; a module defines a registry; a program runs a scheduler; a scheduler evaluates a
schedule; a program reads a file; a program presents a certificate. Exact names are settled when
the issue is filed.

#### Acceptance Criteria

- The settled list is filed as issues against `computing-core-tap` and tap, one per owner, before any node of
  a new type is written.
- Every proposed edge name passes `req-tap-plugin-edge-naming`.

### AI Extraction And Provenance
----
RID: `req-rampart-20x-playground-internals-extraction`

Status: `Proposed`

AI reads the repository once; the output is a static batch in this repository.

#### Implementation

Each extracted node records its source file, the commit it was read at, and that it came from AI extraction.
The batch is regenerated rather than edited, so a deterministic extractor can replace it. Three sources are
structured enough to read mechanically today and are read that way: the part list from `INSTALLED_APPS`, the
libraries from `pyproject.toml`, the registries from the `Registry(` constructions. The AI step covers the
sub-systems, the "uses" relationships and the one-line purposes.

#### Acceptance Criteria

- Every extracted node names its source file and commit.
- The batch regenerates from the repository without hand edits.

### Reconciliation Checks
----
RID: `req-rampart-20x-playground-internals-check`

Status: `Proposed`

A strip on the page compares counts with the live instance: workers in the stack against the worker nodes,
registries against the live meta-registry, collectors against `collector` nodes, plugins against the boot
record. A check that disagrees is shown disagreeing. Gryphon is tried first for grid-side counts; the
projection's JavaScript is the fallback; neither is run yet.

#### Acceptance Criteria

- Each count appears beside the number it was compared with.

### Recorded Gaps
----
RID: `req-rampart-20x-playground-internals-gaps`

Status: `Proposed`

| Gap | Detail |
| --- | --- |
| No module, class, function, variable node | See `...-types`. |
| No installed-plugin, registry or scheduler node | Core types to add. |
| No process node | Not needed here: workers are `program` nodes nested in gunicorn. `computing_core` plans a `process` type. |
| No certificate node | `public_key` and `private_key` exist; the load balancer's certificate is `aws_acm_certificate`. |
| No containment, dependency, "uses" or "loads" edges | `computing_core` has four edges. |
| Library/package types | `computing-core-tap#33`. |
| Compound edges | Not implemented; `PR 1021` proposes the shape. |

#### Acceptance Criteria

- Each gap is filed or decided here before a node of that kind is written.

### Deferred
----
RID: `req-rampart-20x-playground-internals-deferred`

Status: `Proposed`

Function and variable nodes populated; calls between components (the first compound edges); a
runtime-activity overlay; the `double-tap` plugin; a deterministic extractor; gunicorn terminating TLS itself.

## Open Questions

| # | Question |
| :---: | --- |
| Q1 | Should the in-container certificate be a new `certificate` type in `computing_core`, or a `file` with a role until one is needed? |
| Q2 | Does the gunicorn `program` carry the worker count as a property as well as nesting the worker nodes, or is nesting alone enough for the stack chip? |

## Sources

Read, not run, on 2026-10-14: the files named in the provenance markers.
