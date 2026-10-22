# Rampart 20x Playground StackArmor Page Specification

**The playground shows the stackArmor PAIN method two ways on one page: as a process (what each step is) and as it runs on this system (every number computed live from the grid by `stackarmor_vdr`). The memo's five worked examples are stood up as data, so a reader can pick one and follow it down the page.**

This is an extension of `spec-rampart_20x_playground-v0.md`. It adds one page, one examples bundle and one dependency. It stores nothing derived: every figure comes from a `stackarmor_vdr` Search run when the page loads.

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-stackarmor-examples | [Memo Examples](#memo-examples) | Proposed | The five worked examples of the stackArmor memo as data: a finding, component, program, container and stamp each (no vulnerability: the three DEMO vulnerabilities are removed). |
| req-rampart-20x-playground-page-stackarmor | [StackArmor Page](#stackarmor-page) | Proposed | `/playground/stackarmor`: the system's PAIN figures, the PAIN tables, the followed finding and the method. |

### Memo Examples
----
RID: `req-rampart-20x-playground-stackarmor-examples`

Status: `Proposed`

`grift/stackarmor-examples.grift.json` holds, for each of the memo's examples 1 to 5 (section 10), a fictional component (`generic` package), a program that runs it, an image host and a container that runs the image and the program, an open finding that the component carries (source `stackarmor-memo`, key `memo-example-<k>`), and the `stackarmor_vdr` asset-profile stamp pointing at the program with the memo's effective requirements and affected-agency flag. The bundle seeds no vulnerability, so these findings concern none and do not appear in `stackarmor-pain`. The memo's own result is written in each finding's `summary`.

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-stackarmor-examples-1 | Five Examples | Proposed | The bundle holds five findings with source `stackarmor-memo`, five programs, five stamps and no vulnerability. | |
| req-rampart-20x-playground-stackarmor-examples-2 | The Memo's Inputs | Proposed | The stamps carry the memo's effective requirements and flag: H/H/H and 1, M/M/M and 1, L/L/L and 0, M/M/H and 0, L/M/M and 0. | |
| req-rampart-20x-playground-stackarmor-examples-3 | Same Result As The Memo | Superseded | `stackarmor-pain` on each example finding returns the memo's U, S, word and N-level (N5, N4, N3, N3, N2). | Checked against a booted stack; the bundle tests read the inputs only. |
| req-rampart-20x-playground-stackarmor-examples-4 | Stamped Like The Inventory | Proposed | The programs and components carry the Engineering `team.responsible` and the programs `dataclass.action` `process`, so the inventory guards hold; the hosts carry neither, as every other host. | The guards pin the counts. |
| req-rampart-20x-playground-stackarmor-examples-5 | Fictional Is Said | Proposed | Every example's name begins `Memo Example` or `memo example`, and its finding says it is the memo's example. | |

### StackArmor Page
----
RID: `req-rampart-20x-playground-page-stackarmor`

Status: `Proposed`

`grift/stackarmor-page.grift.json` seeds the page `/playground/stackarmor`, eight panels and five Searches; the two PAIN tables of the `pain` bundle are placed on it by `USES_PANEL`. Top to bottom: the intro text, the PAIN Distribution chart beside the titled Status card of what is assumed, the followed finding (Components), the PAIN Findings table, the PAIN Assets table, who requires what, the archetype catalog, and last the method and steps text. The followed finding is the Search's default `entity_id`: the highest-PAIN real finding on the live data when it was set (an interim; a runner input that picks it on read is pending in `stackarmor_vdr`).

| Panel | Type | Search |
| --- | --- | --- |
| Components | Table with column groups | `stackarmor-pain` (`entity_id`) |
| Who Requires What | Table | a Gryphon Search of the stamps, without the memo programs |
| Archetype Catalog | Table | a Gryphon Search of the archetypes |
| Status | Stat card | `stackarmor-summary` (`assumptions`) |
| PAIN Distribution | Bar chart | `stackarmor-summary` (`by_pain`) |
| Findings, Assets | Tables | `PAIN Findings`, `PAIN Assets` |

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-stackarmor-1 | Page And Panels | Proposed | The page has slug `/playground/stackarmor`, and every panel its layout names exists and is used by the page through `USES_PANEL`. | |
| req-rampart-20x-playground-page-stackarmor-2 | Panels Read Searches | Proposed | Each data panel is bound by one `USES_SEARCH` edge to a Search that names a `stackarmor_vdr` runner or a Gryphon query, and no panel computes a figure itself. | Projects are data (no code in the project). |
| req-rampart-20x-playground-page-stackarmor-3 | No Picker | Proposed | There is no picker. The Search that follows a finding declares `entity_id` with a real (non-memo) finding as default; the stamps table leaves out the memo programs. | |
| req-rampart-20x-playground-page-stackarmor-4 | No Explanation Beyond The Method | Proposed | The only prose on the page is the three text panels; every other panel is data under a title. | |
| req-rampart-20x-playground-page-stackarmor-6 | PAIN Tables Merged | Proposed | The `Findings` and `Assets` tables of the `pain` bundle sit on this page (`USES_PANEL`); the bundle holds no page, and `/playground/pain` does not exist. | Supersedes `req-rampart-20x-playground-page-pain`. |
| req-rampart-20x-playground-page-stackarmor-7 | Order | Proposed | The intro is first; the PAIN Distribution chart and the titled Status card, in that order, are the next band; the method and steps text panels are the last band. | |
| req-rampart-20x-playground-page-stackarmor-8 | Navigation Section | Proposed | The page nests (`NESTS_UNDER`) under `/playground/vdr-implementations`, a title-only page named `VDR Implementations`; the section pages order by `nav_weight`: Data Classification, Inventory, Vulnerabilities, VDR Implementations, Teams. | The route does not change. |
| req-rampart-20x-playground-page-stackarmor-5 | Private Plugin Stays Out Of CI | Proposed | The `demo` record pins `stackarmor_vdr` at v0.3.2 with its install credential and seeds it; the `ci` record installs neither it nor the examples and page bundles, and the manifest does not list it in `depends_on`. | The repository is private and CI is offline; the pain bundle is handled the same way. |
| req-rampart-20x-playground-page-stackarmor-9 | Levels As H, M, L | Proposed | In every table on the page the C, I, A, CR, IR and AR cells read H, M, L (N for none) through the table's `toneBadge` formatter (`tones` and `labels`), and High is red. | Data only: the stored word is unchanged. |
| req-rampart-20x-playground-page-stackarmor-10 | Component Columns Not Wrapped | Proposed | The Findings table names the owner column Component and the former component column Package; the owner column is wide enough that its text is not wrapped. | |
| req-rampart-20x-playground-page-stackarmor-11 | Dropped Panels | Proposed | The page has no Same CVE, Different Assets chart and no graph of the finding (it had no projection); their Searches went with them. | |

## Notes

The five example findings concern no vulnerability, so `stackarmor-pain` returns no row for them; their components, programs and stamps remain. The five example programs are counted by the classification mapping like every program (they carry `dataclass.action` `process`), so they raise the program rows of that summary by five mapped entries. They carry no `inventory` dimension, so the inventory tables and the coverage charts that group by it do not count them.
