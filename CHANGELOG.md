# Changelog

All notable changes to Icarus are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning. The first public source release is `v0.1.0`.

## [0.1.0] - 2026-10-19

First public source release. Icarus is a single-user developer preview for local or private-network deployment.

### Added

- **Agent Runtime**
  - Multi-session and multi-task execution with explicit Run states and terminal outcomes.
  - Streaming model output, tool calls, cancellation, failure recovery, usage accounting and local persistence.
  - Model-provider differences isolated behind the model integration layer.

- **Plugin Runtime**
  - Manifest-based plugin discovery with capabilities, tools, events, state scopes and lifecycle.
  - Prompt plugin with stable system-prompt composition, layered sections, token budgets and contributor deadlines.
  - Memory plugin with Mem0-backed automatic recall, explicit tools and history maintenance.
  - Knowledge plugin with OpenKB query, list, read, upload and recompile tools.
  - Relationship plugin with person search, context, remember, forget and relate tools.
  - Skill, MCP, builtin tools and process plugins.
  - Event, Hook, Blackboard and runtime-update infrastructure with explicit ownership boundaries.

- **Interfaces**
  - Textual TUI with session restore, image paste, local queues, cancellation and streaming output.
  - Single-user WebUI for chat, memory and knowledge workbenches, served through a same-origin proxy.
  - Gateway WebSocket RPC shared by TUI and WebUI.
  - Session metadata and conversation history persisted in SQLite; plugin state, assets and traces stored per session.

- **Services**
  - Mem0 long-term memory service with bundled PostgreSQL and dashboard.
  - OpenKB knowledge-base service with configurable knowledge base and model settings.
  - rela-mem standalone person-profile and relationship service backed by PostgreSQL and FalkorDB.
  - Independent PostgreSQL and FalkorDB Compose definitions under `infra/`.

- **Unified operations control plane**
  - Root `icarus.toml` registry for apps and middleware with component kinds, local/remote modes, commands, ports, probes, dependencies and environment bindings.
  - `icarus install/start/stop/status/logs` with dependency ordering, required/optional failure propagation and remote-only probing.
  - `icarus config validate` and `icarus config show` for secret-free, Docker-free configuration inspection.
  - Bounded HTTP/TCP probes and environment injection for Agent and rela-mem connection settings.
  - Safe native process identity checks and Compose operations with preserved data paths.

- **Documentation and validation**
  - Repository README, contribution guide, infrastructure guide and feature design records.
  - Functional tests for the control plane, plugins, application suites and real subprocess/container acceptance.
  - Real acceptance for Gateway/WebUI lifecycle and isolated PostgreSQL/FalkorDB/rela-mem CRUD and restart persistence.

### Changed

- Application and middleware lifecycle is now declared in `icarus.toml` instead of hard-coded root project tables.
- rela-mem runs as an app-only Compose service and uses independent PostgreSQL/FalkorDB middleware.
- Application connection settings can be overridden by control-plane environment variables without rewriting business configuration.
- Root lifecycle control is standard-library only; app dependencies and build files remain application-owned.

### Fixed

- Coordinated process cleanup when a managed leader exits before its descendants.
- Bounded TCP probing including DNS and multi-address attempts.
- Endpoint-only CLI overrides now derive a consistent host/port instead of creating invalid null fields.
- Embedded dependency readiness now checks the effective runtime owner while preserving remote opacity.
- CI references to the moved builtin-tools test and the Windows pytest identifier limit.

### Known limitations

- Single-user deployment: no multi-tenancy, RBAC or public-internet hardening. Gateway has no built-in authentication; WebUI only provides Basic Auth.
- Managed native processes require readable Linux `/proc`; macOS and Windows native process management are not implemented.
- No automatic migration of legacy JSONL session data or database schema migrations.
- The old combined rela-mem Compose deployment must be stopped manually before reusing retained database bind mounts.
- Mem0 PostgreSQL remains bundled; Argus is not registered in the lifecycle.
- No remote deployment, SSH orchestration or image publishing.
- The TUI snapshot suite has 13 pre-existing failing baselines; this release does not claim a fully green TUI test suite.
