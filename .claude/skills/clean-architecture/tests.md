# Tests

- Confirm the project context matches: Usa quando decidi in che layer va una funzionalità, come disaccoppiare backend dal DB o dal framework, o per revisionare i confini tra moduli del Control Plane (config_reader, activation_engine, ecc. da ARCHITECTURE.md).
- Confirm the source skill still matches the manifest commit and hash before export.
- Confirm no MCP, shell, network, secret, or write permissions were added without updating `tools.md`.
