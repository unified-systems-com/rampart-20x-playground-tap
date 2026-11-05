# rampart-20x-playground-tap

A data-only TAP instance plugin (`rampart_20x_playground`) that demonstrates FedRAMP 20x
Vulnerability Detection and Response (VDR), and later Key Security Indicator (KSI), capabilities
for a podcast demo. It composes existing plugins; it ships no models, edges or code.

- **Owns:** a keystone and twenty-six `inventory` and `dataclass` dimension nodes today; mocked AWS GovCloud inventory and findings
  and the pages that show a deployment design, an inventory, vulnerabilities and VDR reports (vulns x
  SLA) as they land. All inventory and findings are mock data, never collected.
- **Lives elsewhere:** vocabulary belongs to the `*_core` plugins, `fedramp_20x_ksi` and
  `rampart_20x`; any capability the pages cannot draw belongs to the plugin that owns it.
- **Read first:** `specs/spec-rampart_20x_playground-v0.md` (the spec is the plan).
- **Boot it:** `scripts/spawn-session.sh <label> cli --from <demo record>` from a TAP checkout, with
  the record at `tap_plugin/rampart_20x_playground/boot/demo.boot.json`. To develop, add
  `--dev-plugins rampart_20x_playground`. Login is by the local passkey that spawn replays.
- **Status:** a working demo. The Overview, Inventory, Data Classification, Vulnerabilities, VDR MAX and StackArmor pages are seeded, and the coverage figures are recorded hourly. The spec lists what is built and what is not.

## How this came about, and credits

FedRAMP 20x asks a provider to evaluate every vulnerability against an asset and remediate within a time set by its Potential Agency Impact (PAIN, N1 to N5). FedRAMP publishes the levels and the remediation matrix, but not the step that decides which level a given vulnerability on a given asset gets. This playground shows two ways of taking that step on a TAP grid, side by side, on one mock deployment: the **VDR MAX** method of `fedramp_20x_vdr` (every finding at the worst case, lowered only by evidence) and the **StackArmor** method of `stackarmor_vdr`, which implements the published approach of Matthew Venne and stackArmor: [the whitepaper](https://stackarmor.github.io/rfc-fedramp-vdr/vdr-pain-cvss.pdf), [the site](https://stackarmor.github.io/rfc-fedramp-vdr/) and [the source](https://github.com/stackArmor/rfc-fedramp-vdr). **Thank you, Matthew, and stackArmor, for publishing it** in a form we could test against. The method is theirs; errors in these implementations are ours, and nothing here is affiliated with or endorsed by stackArmor or FedRAMP.

**What is mock and what is real.** The deployment is a mock design: the GovCloud accounts, resources, people and laptops are invented (reserved `example.invalid` addresses, made-up ids), and a keystone node in the grid says so. The findings are not invented: they are a captured snapshot, never collected live, of real scans of TAP itself, namely TAP's code-scanning and Dependabot alerts, and the vulnerabilities in the signed CycloneDX SBOM of a published `tap-web` image, attached to the mock deployment so the methods have something to evaluate. The StackArmor memo's five worked examples are stood up as data too. The playground is a data-only instance plugin: it ships no code, only seed data, pages and panel configuration for the plugins it composes.

Developed with AI coding assistance (Claude Code) under the direction of the maintainer; the pull requests record what was run and what was not.

## Licence

Apache-2.0, see `LICENSE`.

## Display data the Overview reads

- **`icon_angle`** (dimension of an application flow, degrees): the way the flow points. **0 = north / up, 90 = east, 180 = south, 270 = west**
  (default 90). The Overview turns only the flow's circle icon (the data marker) to it. Arrows always point from the session initiator (the flow's source) to the target (its destination): the arrowhead is on the destination end whatever the angle. Today: `source pull` 270,
  `code` 270, `administration` 0, `customer data` and `database` 90. It is a marked playground exception in `landing.js`
  (exception 38) that becomes a per-node `icon_angle` display hint in tap_viz.
