# Rampart 20x Playground Inventory Specification

**The system inventory as nine small tables instead of one wide spreadsheet: applications, libraries, packages,
operating systems, containers, crypto, secrets, cloud services and third-party SaaS, each with only the columns
that make sense for what it lists.**

This file elaborates `req-rampart-20x-playground-page-inventory` and the `inventory` axis of
`req-rampart-20x-playground-dimensions` in `spec-rampart_20x_playground-v0.md`, and changes the latter (see
`req-rampart-20x-playground-inventory-dimension`). It inherits the v0 rules: the
plugin ships data only, the entities are fabricated for the demo from existing types, and every one carries
`dcom: design`.

## Philosophy

The FedRAMP Integrated Inventory Workbook is one sheet with 24 columns: Unique Asset Identifier, IP address,
Virtual, Public, DNS name, NetBIOS name, MAC address, Authenticated Scan, Baseline Configuration Name, OS name
and version, Location, Asset Type, Hardware make and model, In Latest Scan, Software or database vendor,
Software or database name and version, Patch Level, Diagram Label, Comments, Serial or asset tag, VLAN or
network ID, System administrator or owner, Application administrator or owner, and Function. One row has to
describe a laptop, a database, a library and a SaaS service, so most cells are empty or overloaded: the
network columns mean nothing for a library, and vendor and version mean nothing for a VLAN.

The playground has no such constraint. Each category is its own table with its own columns, and two kinds of
column are not typed at all: values the graph can derive (open findings, how many consumers a library has, how
many instances a container image has) are computed, and values that exist only because a single sheet needed
them are left out. There is no network table and no people table, and no export to the 24-column workbook
(George, 2026-10-14).

**Provenance markers.**
*Observed* (read or fetched on 2026-10-14, not run): the 24 column names, from memory and checked against a
third-party description of 21 of them, not from the official template; the FedRAMP guidance on containers, from
the search results quoted under `req-rampart-20x-playground-inventory-rows`; the v0 spec; the mock inventory on
`main` (50 nodes, 50 edges) and its four pending additions; the 71 code-scanning alerts as a read-only sample.
*Designed* (this spec's own claims, unbuilt and untried): every requirement below.

## Goals

| # | Name | Description |
| :---: | --- | --- |
| 1 | One Table Per Kind | Nine tables, each with only the columns that apply to its rows. |
| 2 | Derived, Not Typed | Counts, findings and consumer numbers are computed from the graph. |
| 3 | FedRAMP Row Rules | Identical containers count once; instances stay countable. |
| 4 | Library Per Version | A library is one row per name and version, with its consumers counted. |
| 5 | Secrets Without Values | Secret material is listed by kind and location, never by value. |
| 6 | Material Apart From Its Home | A secret is its own row, separate from the resource or file that holds it. |
| 7 | Packages From A Named Source | A package row says which document it was read from, so an SBOM-specific view can be cut later. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-inventory-tables | [Nine Tables](#nine-tables) | Proposed | The categories and what each lists |
| req-rampart-20x-playground-inventory-dimension | [Dimension Change](#dimension-change) | Proposed | Splits `inventory.os` into operating systems and containers; adds packages and crypto |
| req-rampart-20x-playground-inventory-common | [Common Columns](#common-columns) | Proposed | The columns every table carries |
| req-rampart-20x-playground-inventory-rows | [Row Rules](#row-rules) | Proposed | What counts as one row, with the FedRAMP basis |
| req-rampart-20x-playground-inventory-applications | [Applications](#applications) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-libraries | [Libraries](#libraries) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-packages | [Packages](#packages) | Proposed | Columns, rows and the source column |
| req-rampart-20x-playground-inventory-os | [Operating Systems](#operating-systems) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-containers | [Containers](#containers) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-crypto | [Crypto](#crypto) | Proposed | The crypto-BOM providers, with their disposition |
| req-rampart-20x-playground-inventory-secrets | [Secrets](#secrets) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-cloud | [Cloud Services](#cloud-services) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-saas | [Third-Party SaaS](#third-party-saas) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-software | [Software Bundle](#software-bundle) | Proposed | The data behind the operating-system, library, package, container and crypto tables |
| req-rampart-20x-playground-inventory-derived | [Derived Columns](#derived-columns) | Proposed | How computed columns are produced |
| req-rampart-20x-playground-inventory-gaps | [Recorded Gaps](#recorded-gaps) | Proposed | Columns the grid cannot supply yet |

### Nine Tables
----
RID: `req-rampart-20x-playground-inventory-tables`

Status: `Proposed`

Nine tables, one per value of the `inventory` dimension, in page order: applications, libraries, packages,
operating systems, containers, crypto, secrets, cloud services, third-party SaaS. Each is a Search over `n.dimensions["inventory"]` and an
existing table panel, as `req-rampart-20x-playground-page-inventory` already states. This spec adds the columns
and the row rules.

#### Acceptance Criteria

- Exactly nine tables; none for network endpoints or for people and their computers.
- Nothing from TAP's own internals (modules, registries, workers) appears in any table.

### Dimension Change
----
RID: `req-rampart-20x-playground-inventory-dimension`

Status: `Proposed`

The v0 spec has one category, `inventory.os`, described as "operating systems and containers". Operating
systems and containers are now separate tables, so the axis gains a value: `inventory.os` becomes operating
systems only and a new `inventory.containers` covers images (approved by George, 2026-10-14). The axis gains
two more values for the software tables: `inventory.packages` and `inventory.crypto` (George, 2026-10-14).
The dictionary goes from sixteen dimension nodes to nineteen (ten `inventory`, nine `dataclass`), and
`req-rampart-20x-playground-dimensions` and its tests (`test_sixteen_dimension_nodes`) change with it.

#### Acceptance Criteria

- `MATCH (d:dimension) WHERE d.name STARTS_WITH "inventory." RETURN d` returns nine category nodes.
- Every entity in the container table is stamped `inventory: containers`, and none in the operating-systems
  table is.

### Common Columns
----
RID: `req-rampart-20x-playground-inventory-common`

Status: `Proposed`

Every table carries: an identifier (the Unique Asset Identifier), a name (the Diagram Label, the same text drawn
on the board), a description (in place of Comments), the account and region (Location), the data classes it
handles (the `dataclass` axis), and the number of open findings.

#### Acceptance Criteria

- The name in a row equals the label of the same entity on the board.
- No table has a free-text Comments column.

### Row Rules
----
RID: `req-rampart-20x-playground-inventory-rows`

Status: `Proposed`

A row is one running instance of an actual service, except that identical containers count once.

#### Implementation

The FedRAMP basis, as found in the search results (the primary PDFs were not opened): the Vulnerability Scanning
Requirements for Containers say a unique asset identifier must be assigned to every class of image that
corresponds to one or more production-deployed containers, and those image-based identifiers are documented in
the Integrated Inventory Workbook. The same document says individual container instances are tracked internally
by the CSP and need not be in the workbook unless a security sensor scans them directly. The Continuous
Monitoring Playbook (v1.0, 11/17/2025) says the CSP must be able to show that the assets in a class are
identical and test that annually. One consultant's write-up (Schellman) reads production-sensor scanning as
requiring each instance; the official wording ties that to sensors targeting an instance directly. So:

- A **container** row is an image class. Two ECS tasks that run the same image digest are one row with an
  instances count of two. Each task stays a node on the board.
- A task whose image digest differs from its siblings is its own row, and the identical check says so.
- Every other **service** is one row per resource: each bucket, each load balancer, each secret.
- A **library** is one row per name and version, with the number of consumers (see
  `req-rampart-20x-playground-inventory-libraries`).

#### Acceptance Criteria

- The instances count of a container row equals the number of task nodes that run its image.
- If instances of one class report different digests, the row shows "no" under identical and the class splits.

### Applications
----
RID: `req-rampart-20x-playground-inventory-applications`

Status: `Proposed`

The running programs of the deployment: the TAP web program (and gunicorn that hosts it) and the specific
PostgreSQL database instance. The managed service that runs the database is a cloud-services row, not this one.
Columns: version, vendor or source, function, what it runs in, the ports it listens on, runtime or
language, whether it is public, FIPS status (derived from TAP's own validation record), open findings.

#### Acceptance Criteria

- The TAP web program has a row with its ports and the container it runs in.
- The PostgreSQL database instance has a row here and the RDS service has a different row under cloud services.

### Libraries
----
RID: `req-rampart-20x-playground-inventory-libraries`

Status: `Proposed`

Libraries are the things built outside a package manager, listed once per name and version: the self-built
OpenSSL FIPS provider and the `cryptography` library built from source (George, 2026-10-14). Everything a
package manager installed is a package row (see `req-rampart-20x-playground-inventory-packages`), not a library
row. This replaces the earlier reading of this section, which put every package and library of the web image
here.

#### Implementation

Columns: name, version, ecosystem, how it was built (self-built or source-built), what it was built from, path,
license, CPE. Whether a library carries cryptography is not a column: it is the presence of a
`CARRIES_CRYPTO_PROVIDER` edge to a crypto provider (see `req-rampart-20x-playground-inventory-crypto`). The
count of consumers, fixed version and open findings stay derived columns not yet built.

#### Acceptance Criteria

- The table has exactly two rows on the web image: the OpenSSL FIPS provider (source kind self-built, version
  and CPE from `docker/sbom-supplemental.json`) and `cryptography` (source kind source-built, version from
  `uv.lock`).
- No apk or Python package that a package manager installed has a row here.

### Packages
----
RID: `req-rampart-20x-playground-inventory-packages`

Status: `Proposed`

Every package the web image's package managers installed, one row per ecosystem, name and version. Where two
versions of a package are present, both are rows. The database image's packages are out of scope, as they are
for the findings. Each row carries a source column naming the document it was read from. This sets up a later
SBOM-specific view: the rows are the SBOM's rows (George, 2026-10-14).

#### Implementation

Columns: name, version, ecosystem (apk, pypi, npm), source, architecture, license, package URL. Until a
generated SBOM exists, the source column names the same inputs the SBOM scan reads, with an honest label: the
apk database (`apk`), `uv.lock` (`pypi`) and the vendored `package-lock.json` (`npm`). When the real SBOM
replaces them, the source becomes `sbom`; the rows and the table do not change. Licence is blank where the
source holds none (`uv.lock` carries none).

#### Acceptance Criteria

- No two rows share ecosystem, name and version.
- Every row names its source, and no row says `sbom` before a generated SBOM is its source.
- The web image's host has an `INSTALLS_PACKAGE` edge to each row.

### Operating Systems
----
RID: `req-rampart-20x-playground-inventory-os`

Status: `Proposed`

Operating systems, as their own table. The base of the product's images is Wolfi, the Chainguard distribution
(TAP's Dockerfile builds on `cgr.dev/chainguard/wolfi-base`, pinned by digest; read from the repository, not run).

#### Implementation

Columns: name, OS ID, version ID, build, vendor, rolling, base image. Wolfi is a rolling distribution:
`/etc/os-release` says `ID=wolfi` and `VERSION_ID="20230201"`, a fixed placeholder, so the build is the digest
of the pinned base image in the Dockerfile (`cgr.dev/chainguard/wolfi-base:latest@sha256:...`), which is the
node's `build_id`. Patch level, end of life, baseline configuration, images-built-on-it and FIPS status wait for
fields or edges that do not exist yet.

#### Acceptance Criteria

- Wolfi has one row per pinned base-image digest, however many images are built on it.
- The images-built-on-it count equals the number of container rows that name it as their base.

### Containers
----
RID: `req-rampart-20x-playground-inventory-containers`

Status: `Proposed`

Container image classes, per `req-rampart-20x-playground-inventory-rows`.

#### Implementation

Rows: the web image's host (a `computing_core__host` of kind container, joined to its operating system by
`RUNS_OPERATING_SYSTEM`) and the GHCR package version of the product image. Columns: kind, image tag and digest,
base operating system (a link to its row), architecture, instances (derived),
identical across instances (derived), libraries (derived count), in latest scan (derived), authenticated scan
(not applicable to image scans; shown as such), baseline configuration.

#### Acceptance Criteria

- The web image appears as one container row, not one per task.
- Each container row names its base operating system and the link resolves to a row in the operating-systems
  table.

### Crypto
----
RID: `req-rampart-20x-playground-inventory-crypto`

Status: `Proposed`

What the crypto-BOM scan (`req-fips-crypto-bom`) parsed out of the web image: one row per cryptographic
implementation and the file it was found in, with the reviewed decision about it. Key material is not shown and
is not held by the node type (`req-rampart-20x-playground-inventory-secrets` still governs secrets).

#### Implementation

Columns: name, provider, provider kind, artifact, boundary, FIPS validation, scope, rationale. The scope is
`tap-web`. The code that carries a provider is joined by a `CARRIES_CRYPTO_PROVIDER` edge: the OpenSSL FIPS
provider library carries its own provider row, `cryptography` carries the row for its Rust extension, an apk
package carries the rows for the binaries it owns (by the apk database's file ownership), and a Python package
carries the rows for the extensions in its directory. A provider whose file no package, library or program owns
(the `uv` binary) has no carrier edge, and the table says so by the absence.

#### Acceptance Criteria

- The rows equal the findings of `tap.crypto_bom.core_report()` plus the shipped-provider finding, nothing more.
- No row, property or edge carries key material or a fingerprint.

### Secrets
----
RID: `req-rampart-20x-playground-inventory-secrets`

Status: `Proposed`

Secret material: secrets, keys and certificates, listed by kind and where they are held, never by value. A
secret is its own row and its home is a different row: the key material of a KMS key is a secret row here, and
the AWS KMS key that holds it is a cloud-services row (George, 2026-10-14). The same applies to a certificate on
disk (the secret, and the file that holds it) and to a secret in Secrets Manager (the secret, and the service
resource). Columns: kind (secret, key or certificate), algorithm, key size, where it is held (a file, a running program or
Secrets Manager), who uses it, what protects it (the KMS key), rotation, expiry.

#### Acceptance Criteria

- No row, property or batch carries a secret value, a file's content or a private-key fingerprint.
- The KMS key appears twice: as key material under secrets, and as the AWS resource under cloud services, and
  the first names the second as where it is held.
- The load balancer's certificate and the container's certificate are two rows, the second with its public and
  private halves identified.

### Cloud Services
----
RID: `req-rampart-20x-playground-inventory-cloud`

Status: `Proposed`

Cloud capabilities that are neither application, library nor operating system: the load balancer, cluster,
database service, internet gateway, Route 53 zone, ECR, Secrets Manager, KMS, S3 buckets, Lambda
function, the KMS key as a resource, and the CodePipeline and CodeBuild resources once `aws_core` has types for
them. Columns: service,
resource type, ARN or ID, public, encrypted at rest, Multi-AZ, FIPS endpoint, who manages it (customer
configured or AWS managed).

#### Acceptance Criteria

- Every cloud-service node on the board has a row, except the conceptual containers.
- Neither a subnet (in any zone) nor the VPC has a row: they are conceptual containers, not systems
  (George, 2026-10-14).

### Third-Party SaaS
----
RID: `req-rampart-20x-playground-inventory-saas`

Status: `Proposed`

Outside systems the deployment depends on: GitHub where the code comes from, GHCR, and AWS where it is hosted.
Columns: vendor, service, purpose, data shared, how it authenticates to the deployment, the vendor's own
authorization status, what it connects to.

#### Acceptance Criteria

- GitHub.com and GHCR each have a row.

### Software Bundle
----
RID: `req-rampart-20x-playground-inventory-software`

Status: `Proposed`

The data behind the operating-system, library, package, container and crypto tables is one bundle,
`grift/inventory-software.grift.json`, of existing `computing_core` types (v0.6.0): `operating_system`, `host`
(kind container), `package`, `library` and `crypto_provider`, with the official edges `RUNS_OPERATING_SYSTEM`,
`INSTALLS_PACKAGE`, `LOADS_LIBRARY` and `CARRIES_CRYPTO_PROVIDER`.

#### Implementation

Values are read, not invented: the OS from the web container's `/etc/os-release` and the Dockerfile pin; apk
packages from the container's apk database; Python packages from `uv.lock`; npm packages from the vendored
`package-lock.json`; the self-built provider from `docker/sbom-supplemental.json`; crypto providers from the
crypto-BOM scan run inside the web container. Every entity carries `dcom: design` because the bundle is
hand-seeded, and none is stamped `overview`, so none appears on the Overview board. A field the source does not
hold (a Python package's licence, a library's language) is left unset.

#### Acceptance Criteria

- Every entity carries `dcom: design` and one `inventory` value; no entity carries `overview`.
- Every edge joins types the edge supports, and every endpoint exists.
- Re-running the read against the same image reproduces the rows.

### Derived Columns
----
RID: `req-rampart-20x-playground-inventory-derived`

Status: `Proposed`

Derived columns are computed from the graph: open findings (a count over the findings attached to the row's
entity and what it contains), consumers, instances, libraries, identical-across-instances, end of life, in
latest scan and FIPS status. Gryphon is tried first; a computation Gryphon cannot express (COUNT is its only
aggregate; no SUM or UNION) falls back to the panel's JavaScript. Neither has been run.

#### Acceptance Criteria

- A derived value is never stored on an entity.
- The open findings figure on the inventory equals the figure on the board for the same entity.

### Recorded Gaps
----
RID: `req-rampart-20x-playground-inventory-gaps`

Status: `Proposed`

| Gap | Detail |
| --- | --- |
| Properties the types do not hold | Function, baseline configuration, vendor authorization, rotation and responsibility have no field on today's types; each is a candidate for a tag or a dimension or a plugin field, decided before it is used. |
| No owner column | The workbook's administrator and owner columns pointed at people; with no people table there is nothing to point at. |
| Findings on a library | Findings attach to scan results by package and version, not yet to a library node. |
| Fixed version and consumers | A package or library row shows no fixed version, consumer count or open findings: findings attach to scan results, not yet to a package node. |
| `uv` and `uvx` | They enter the image by `COPY --from` and `docker/sbom-supplemental.json` calls them `copied-image` libraries; they are not rows here, pending a ruling on whether a copied binary is a library. |
| Container image identity | The image digest needs a home on the task or container node. |
| Secret and key nodes | `secret` and `asymmetric_key` are proposed in the internals spec and do not exist; neither does an edge from a KMS key or a file to the secret it holds. |
| Dimension change | `inventory.containers` is a new dimension node; the v0 spec and `dimensions.grift.json` change with it. |

## Open Questions

| # | Question |
| :---: | --- |
| Q1 | The dimension change touches the v0 spec, `dimensions.grift.json` and one test. Does it go in the pull request that carries this spec, or in a build pull request of its own? |

## Sources

Fetched or read, not run, on 2026-10-14: FedRAMP Vulnerability Scanning Requirements for Containers v1.0;
FedRAMP Continuous Monitoring Playbook v1.0 (11/17/2025); Schellman, "Navigating FedRAMP Security Requirements
for Containers"; a third-party description of the Integrated Inventory Workbook columns; the playground v0 spec
and mock inventory.
