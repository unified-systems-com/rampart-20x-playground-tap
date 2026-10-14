# Rampart 20x Playground Inventory Specification

**The system inventory as six small tables instead of one wide spreadsheet: applications, libraries, operating
systems and containers, secrets, cloud services and third-party SaaS, each with only the columns that make
sense for what it lists.**

This file elaborates `req-rampart-20x-playground-page-inventory` and the `inventory` axis of
`req-rampart-20x-playground-dimensions` in `spec-rampart_20x_playground-v0.md`. It inherits the v0 rules: the
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
| 1 | One Table Per Kind | Six tables, each with only the columns that apply to its rows. |
| 2 | Derived, Not Typed | Counts, findings and consumer numbers are computed from the graph. |
| 3 | FedRAMP Row Rules | Identical containers count once; instances stay countable. |
| 4 | Library Per Version | A library is one row per name and version, with its consumers counted. |
| 5 | Secrets Without Values | Secret material is listed by kind and location, never by value. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-inventory-tables | [Six Tables](#six-tables) | Proposed | The categories and what each lists |
| req-rampart-20x-playground-inventory-common | [Common Columns](#common-columns) | Proposed | The columns every table carries |
| req-rampart-20x-playground-inventory-rows | [Row Rules](#row-rules) | Proposed | What counts as one row, with the FedRAMP basis |
| req-rampart-20x-playground-inventory-applications | [Applications](#applications) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-libraries | [Libraries](#libraries) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-os | [Operating Systems And Containers](#operating-systems-and-containers) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-secrets | [Secrets](#secrets) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-cloud | [Cloud Services](#cloud-services) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-saas | [Third-Party SaaS](#third-party-saas) | Proposed | Columns and rows |
| req-rampart-20x-playground-inventory-derived | [Derived Columns](#derived-columns) | Proposed | How computed columns are produced |
| req-rampart-20x-playground-inventory-gaps | [Recorded Gaps](#recorded-gaps) | Proposed | Columns the grid cannot supply yet |

### Six Tables
----
RID: `req-rampart-20x-playground-inventory-tables`

Status: `Proposed`

Six tables, one per value of the `inventory` dimension: applications, libraries, operating systems and
containers, secrets, cloud services, third-party SaaS. Each is a Search over `n.dimensions["inventory"]` and an
existing table panel, as `req-rampart-20x-playground-page-inventory` already states. This spec adds the columns
and the row rules.

#### Acceptance Criteria

- Exactly six tables; none for network endpoints or for people and their computers.
- Nothing from TAP's own internals (modules, registries, workers) appears in any table.

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

The running programs of the deployment: the TAP web program (and gunicorn that hosts it) and the database
engine. Columns: version, vendor or source, function, what it runs in, the ports it listens on, runtime or
language, whether it is public, FIPS status (derived from TAP's own validation record), open findings.

#### Acceptance Criteria

- The TAP web program has a row with its ports and the container it runs in.

### Libraries
----
RID: `req-rampart-20x-playground-inventory-libraries`

Status: `Proposed`

Every library, listed once per name and version, with the number of consumers. This replaces counting a library
once per container: a library used by two identical containers is one row with the container class as its
consumer.

#### Implementation

Columns: name, version, ecosystem (apk, pip and so on), fixed version where known, whether it carries
cryptography, license, consumers (derived count of image classes or programs that include it), open findings.
The set is every package and library on the web image, taken from the same scan data that feeds the findings
(the OpenSSL FIPS provider, glibc, Python, gosu, oauthlib and the rest), with the database image's packages
excluded as the findings are.

#### Acceptance Criteria

- Two entries of the same library at different versions are two rows.
- The consumers count for a library on the web image equals the number of image classes that include it, not
  the number of running tasks.

### Operating Systems And Containers
----
RID: `req-rampart-20x-playground-inventory-os`

Status: `Proposed`

Two kinds of row: an operating system, and a container image class.

#### Implementation

Operating system columns: name and version, patch level, end of life (derived), baseline configuration.
Container columns: image tag and digest, base image, architecture, instances (derived), identical across
instances (derived), libraries (derived count), in latest scan (derived), authenticated scan (not applicable
to image scans; shown as such), baseline configuration.

#### Acceptance Criteria

- The web image appears as one container row, not one per task.
- The base operating system the image is built on appears as its own row and the container row links to it.

### Secrets
----
RID: `req-rampart-20x-playground-inventory-secrets`

Status: `Proposed`

Secret material: secrets, keys and certificates, listed by kind and where they are held, never by value.
Columns: kind (secret, key or certificate), algorithm, key size, where it is held (a file, a running program or
Secrets Manager), who uses it, what protects it (the KMS key), rotation, expiry.

#### Acceptance Criteria

- No row, property or batch carries a secret value, a file's content or a private-key fingerprint.
- The load balancer's certificate and the container's certificate are two rows, the second with its public and
  private halves identified.

### Cloud Services
----
RID: `req-rampart-20x-playground-inventory-cloud`

Status: `Proposed`

Cloud capabilities that are neither application, library nor operating system: the load balancer, cluster,
database service, VPC, subnets, internet gateway, Route 53 zone, ECR, Secrets Manager, KMS, S3 buckets, Lambda
function, and the CodePipeline and CodeBuild resources once `aws_core` has types for them. Columns: service,
resource type, ARN or ID, public, encrypted at rest, Multi-AZ, FIPS endpoint, who manages it (customer
configured or AWS managed).

#### Acceptance Criteria

- Every cloud-service node on the board has a row.

### Third-Party SaaS
----
RID: `req-rampart-20x-playground-inventory-saas`

Status: `Proposed`

Outside systems the deployment depends on: GitHub where the code comes from, GHCR, and AWS where it is hosted.
Columns: vendor, service, purpose, data shared, how it authenticates to the deployment, the vendor's own
authorization status, what it connects to.

#### Acceptance Criteria

- GitHub.com and GHCR each have a row.

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
| Container image identity | The image digest needs a home on the task or container node. |

## Open Questions

| # | Question |
| :---: | --- |
| Q1 | Does the KMS key belong under Secrets (it is key material) or Cloud Services (it is an AWS resource)? |
| Q2 | Are the zone copies of one subnet tier one row or several? They are stacked on the board. |
| Q3 | Does the database appear under Applications (the engine) as well as Cloud Services (the managed instance), or only the latter? |
| Q4 | Is the base operating system a row of its own, or a column on the container row? |

## Sources

Fetched or read, not run, on 2026-10-14: FedRAMP Vulnerability Scanning Requirements for Containers v1.0;
FedRAMP Continuous Monitoring Playbook v1.0 (11/17/2025); Schellman, "Navigating FedRAMP Security Requirements
for Containers"; a third-party description of the Integrated Inventory Workbook columns; the playground v0 spec
and mock inventory.
