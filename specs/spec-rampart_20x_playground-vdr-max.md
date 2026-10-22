# Rampart 20x Playground VDR Max Page Specification

**The playground shows the VDR max method two ways on one page: as a process (the rules it follows) and as it runs on this system (counts, one finding's evaluation and clocks, and the FedRAMP timeframe rows as data), all computed live from the grid by `fedramp_20x_vdr`.**

This extends `spec-rampart_20x_playground-v0.md`. It adds one page and one bundle. Nothing is stored that the page derives.

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-rampart-20x-playground-page-vdr-max | [VDR Max Page](#vdr-max-page) | Proposed | `/playground/vdr-max` (VDR MAX): three text panels and seven data panels over the `fedramp_20x_vdr` Searches. |

### VDR Max Page
----
RID: `req-rampart-20x-playground-page-vdr-max`

Status: `Proposed`

`grift/vdr-max-page.grift.json` seeds the page `/playground/vdr-max`, ten panels and the seven Searches they use. Three panels are text (the introduction, the rules, the steps). The open-evaluations table links each row to the page with `?entity_id=<finding>`; the page forwards that parameter to the Searches that declare it, so with none it shows the first listed finding.

| Panel | Type | Search |
| --- | --- | --- |
| Where The System Stands | Stat card | `vdr-summary` (`counts`) |
| Counts By Clock | Bar chart | `vdr-summary` (`by_view`) |
| Open Evaluations | Table | `vdr-deadlines` (`remediation_due`) |
| The Remediation Clock | Table | `vdr-deadlines` (`entity_id`) |
| The Evaluation | Table | a Gryphon Search of the finding's evaluation (`entity_id`) |
| Reportable Incident? | Table | `vdr-incidents` (`entity_id`) |
| FedRAMP Timeframes | Table | a Gryphon Search of the timeframe rows |

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-rampart-20x-playground-page-vdr-max-1 | Page And Panels | Proposed | The page has slug `/playground/vdr-max`, and every panel its layout names exists and is used by the page through `USES_PANEL`. | |
| req-rampart-20x-playground-page-vdr-max-2 | Panels Read Searches | Proposed | Each data panel is bound by one `USES_SEARCH` edge to a Search that names a `fedramp_20x_vdr` runner or a Gryphon query, and no panel computes a figure itself. | Projects are data. |
| req-rampart-20x-playground-page-vdr-max-3 | A Picker Reloads The Page | Proposed | The open-evaluations table's `row_url_template` is `/playground/vdr-max?entity_id={finding_id}`, and the Searches that follow the chosen finding declare `entity_id` with one listed finding as the default. | |
| req-rampart-20x-playground-page-vdr-max-4 | Prose Is Three Panels | Proposed | The only prose on the page is the three text panels; every other panel is data under a title. | |
| req-rampart-20x-playground-page-vdr-max-5 | Needs Version 0.1.5 | Proposed | The manifest depends on `fedramp_20x_vdr` at 0.1.5 or later (the release with `vdr-summary` and the `entity_id` input), the `ci` and `demo` records pin it, and the `demo` record fires the `vdr_max` collector once after seeding so evaluations exist. | The plugin is public, so the ci record seeds this bundle. |
| req-rampart-20x-playground-page-vdr-max-6 | Worst Case Is Shown As Unset | Proposed | The evaluation table shows an unset factor as `unset (worst case: ...)`, never as a blank or as false. | |
| req-rampart-20x-playground-page-vdr-max-7 | Named, Nested And Scheduled | Proposed | The page is named `VDR MAX` with `nav_weight` 10 and nests under the VDR Implementations page through a `NESTS_UNDER` edge in a demo-only bundle seeded after both; an hourly Schedule targets the `fedramp_20x_vdr:vdr_max` collector. | The section page is not seeded in ci, so the edge cannot sit in the ci-seeded page bundle. |
| req-rampart-20x-playground-page-vdr-max-8 | Rules And Steps Last | Proposed | The Rules and From Finding To Deadline text panels are the last band of the page. | |
| req-rampart-20x-playground-page-vdr-max-9 | The Count Card Is Titled | Proposed | The card of counts is titled Open Evaluations (`title`) and shows the figure once, at the right; it has no `title_field` and no unit. | It showed the count as its own title. |
| req-rampart-20x-playground-page-vdr-max-10 | Tables Fit | Proposed | Open Evaluations and FedRAMP Timeframes use `default_page_size` 25, a size the Rows selector offers; The Remediation Clock, The Evaluation and Reportable Incident? run at full width with fixed widths that hold their headers and values (no header sort on those one-row tables). | The selector offers 25, 50 and All, so a default of 10 or 12 showed 25 selected beside "Showing 10". |
