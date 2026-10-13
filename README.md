# rampart-20x-playground-tap

A data-only TAP instance plugin (`rampart_20x_playground`) that demonstrates FedRAMP 20x
Vulnerability Detection and Response (VDR), and later Key Security Indicator (KSI), capabilities
for a podcast demo. It composes existing plugins; it ships no models, edges or code.

- **Owns:** a keystone, mocked AWS GovCloud inventory and findings (seed data), and the pages that
  show a deployment design, a system inventory, vulnerabilities, and VDR reports (vulns x SLA).
- **Lives elsewhere:** vocabulary belongs to the `*_core` plugins, `fedramp_20x_ksi` and
  `rampart_20x`; any capability the pages cannot draw belongs to the plugin that owns it.
- **Read first:** `specs/spec-rampart_20x_playground-v0.md` (arrives by PR; the spec is the plan).
- **Status:** spec stage. No package exists yet.
