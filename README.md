# rampart-20x-playground-tap

A data-only TAP instance plugin (`rampart_20x_playground`) that demonstrates FedRAMP 20x
Vulnerability Detection and Response (VDR), and later Key Security Indicator (KSI), capabilities
for a podcast demo. It composes existing plugins; it ships no models, edges or code.

- **Owns:** a keystone and nineteen `inventory` and `dataclass` dimension nodes today; mocked AWS GovCloud inventory and findings
  and the pages that show a deployment design, an inventory, vulnerabilities and VDR reports (vulns x
  SLA) as they land. All inventory and findings are mock data, never collected.
- **Lives elsewhere:** vocabulary belongs to the `*_core` plugins, `fedramp_20x_ksi` and
  `rampart_20x`; any capability the pages cannot draw belongs to the plugin that owns it.
- **Read first:** `specs/spec-rampart_20x_playground-v0.md` (the spec is the plan).
- **Boot it:** `scripts/spawn-session.sh <label> cli --from <demo record>` from a TAP checkout, with
  the record at `tap_plugin/rampart_20x_playground/boot/demo.boot.json`. To develop, add
  `--dev-plugins rampart_20x_playground`. Login is by the local passkey that spawn replays.
- **Status:** scaffold. The keystone and dimensions bundles exist; the pages and mock bundles are
  later requirements in the spec.
