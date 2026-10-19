# Icarus

Icarus 是一个面向个人长期协作的可扩展 Agent 系统。它把身份、会话、长期记忆、知识库和运行状态保存在用户自己的设备上，在需要时启动一次 Agent Run 完成推理与行动，结束后释放计算资源，同时保留可恢复的连续性。

当前版本：**v0.1.0**，定位为单用户、本地或私网部署的开发者预览版。

## 设计原则

- **属于用户**：身份、会话、状态、能力和可恢复数据以本地持久化为事实源。
- **长期连续**：进程和界面可以结束，重新启动后仍然是同一个 Icarus。
- **按需运行**：模型调用按任务启动，不要求 Agent 长期占用计算资源。
- **理解而非画像**：长期认知区分观察、事实、推断、时效和不确定性，并允许用户纠正。
- **插件化扩展**：Prompt、Memory、Knowledge、Relationship、Skill、MCP 等能力通过统一插件运行时组合。
- **运维可控制**：应用、中间件、地址、端口、依赖和启停由同一套仓库级控制面管理。

## 核心能力

### Agent Runtime

- 多 Session、多 Task、Run 状态与唯一终态。
- 流式模型输出、工具调用、取消、失败恢复和 Usage 统计。
- Session 元数据与会话记录持久化，支持刷新和重启后恢复。
- 模型协议差异收敛在模型接入层，Agent 与插件不直接依赖具体厂商协议。

### 插件系统

- Manifest 自动发现，声明 Capability、Tool、Event、状态范围和依赖。
- Plugin Runtime 按 Plugin 身份路由事件，不解释具体业务事件。
- 内置能力：
  - **Prompt**：稳定 System Prompt、静态分层与贡献者预算。
  - **Memory**：Mem0 自动召回、显式读取、写入和历史维护。
  - **Knowledge**：OpenKB 查询、列举、读取、上传与重编译。
  - **Relationship**：人物身份、档案、关系与候选确认。
  - **Skill / MCP / Builtin Tools / Process**：技能、外部工具和本地执行能力。
- Hook 只用于已登记的值改写点；记录、日志和观测归运行时基础设施。

### 交互入口

- **TUI**：终端内对话、图片输入、会话恢复、任务取消和本地队列。
- **WebUI**：浏览器中的会话、记忆管理和知识库工作台，通过同源代理连接 Gateway 与后端服务。
- **Gateway**：统一的 WebSocket RPC 服务，TUI 和 WebUI 共享同一 Session 执行事实。

### 服务与运维

- **mem0**：长期记忆服务，使用独立 PostgreSQL。
- **OpenKB**：知识库与编译服务。
- **rela-mem**：人物档案、身份与关系服务，使用 PostgreSQL 与 FalkorDB。
- **统一生命周期控制面**：`icarus.toml` 声明组件，支持 local/remote、依赖编排、健康探测、配置诊断和受限的进程/Compose 管理。

## 系统组成

| 组件 | 职责 | 运行形态 |
| --- | --- | --- |
| Agent | Agent Runtime、模型接入、插件和本地持久化 | 内嵌在 Gateway |
| Gateway | WebSocket RPC、Session 与任务入口 | 本地 Python 进程 |
| TUI | 终端客户端 | 前台进程 |
| WebUI | 浏览器工作台与同源代理 | Node.js 进程 |
| Mem0 | 长期记忆服务 | Docker Compose |
| OpenKB | 知识库服务 | Docker Compose |
| rela-mem | 人物档案与关系服务 | Docker Compose |
| PostgreSQL / FalkorDB | 关系服务与档案存储 | 独立 Compose 中间件 |
| `icarus` | 仓库级安装、配置、启停和状态控制 | Python 标准库 CLI |

## 快速开始

### 环境要求

- Python 3.11+
- Docker 与 Docker Compose
- Node.js 22.12+ 与 Corepack（仅 WebUI 安装和构建需要）
- Linux 可读 `/proc`（仅原生进程管理需要）

### 安装

```bash
git clone https://github.com/Removel/Icarus.git
cd Icarus
cp -n .example.env .env
./bin/icarus install
```

`icarus install` 会创建各应用自己的 Python 环境、构建应用镜像并拉取中间件镜像；不会启动服务，也不会覆盖已有 `.env`。命令链接不会自动安装，需要时执行：

```bash
bash scripts/install-commands.sh
```

### 配置

在 `.env` 中填写模型 Key、服务 Secret 和绝对数据目录：

```dotenv
OPENAI_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-api-key
ICARUS_DATA_DIR=/absolute/path/to/icarus-data

ICARUS_MEM0_API_KEY=your-memory-key
ICARUS_MEM0_POSTGRES_PASSWORD=your-database-password
ICARUS_MEM0_JWT_SECRET=your-jwt-secret
ICARUS_MEM0_LLM_API_KEY=your-memory-model-key

ICARUS_OPENKB_API_TOKEN=your-knowledge-token
ICARUS_OPENKB_LLM_API_KEY=your-knowledge-model-key

RELA_MEM_API_TOKEN=your-relationship-token
RELA_MEM_PG_PASSWORD=your-database-password
RELA_MEM_FALKORDB_PASSWORD=your-graph-password
```

模型、Plugin 和 Prompt 等业务配置保留在应用自己的配置中，例如 `apps/agent/settings.json`；不要把它们写进根 `icarus.toml`。

检查有效配置：

```bash
./bin/icarus config validate
./bin/icarus config show
./bin/icarus config show rela-mem
```

### 启动

```bash
./bin/icarus start
```

该命令按依赖顺序启动默认栈，最后在当前终端打开 TUI。TUI 退出不会停止后台服务。

也可以显式管理单个组件：

```bash
./bin/icarus start gateway      # Gateway + 内嵌 Agent + required 服务
./bin/icarus start mem0
./bin/icarus start openkb
./bin/icarus start rela-mem
./bin/icarus status
./bin/icarus logs rela-mem --no-follow
./bin/icarus stop rela-mem      # 只停止应用，保留共享数据库
./bin/icarus stop               # 逆序停止默认 stack
```

## 配置模型

Icarus 的配置分成三层所有权：

| 配置 | 内容 | 是否提交 |
| --- | --- | --- |
| `icarus.toml` | 组件拓扑、命令、端口、探测、依赖和 Secret 变量名 | 是 |
| `icarus.local.toml` | 本机 local/remote、地址和部署方式覆盖 | 否 |
| `.env` 或进程环境 | Secret、`ICARUS_DATA_DIR` 和应用运行环境 | 否 |
| 应用配置 | 模型、Prompt、Plugin、用户/Agent 身份 | 由应用自己管理 |

优先级：

```text
命令行显式组件覆盖
> icarus.local.toml
> icarus.toml
> 内置默认值
```

`remote` 组件只登记和探测，不会在远端安装、启动或停止。数据库、rela-mem 等中间件可以本地管理，也可以指向已经存在的外部服务。

## 部署形态

### 全本地

默认拓扑：Gateway、TUI、WebUI、mem0、OpenKB、rela-mem 以及 PostgreSQL/FalkorDB 都在同一台设备上。适合个人工作站。

### 分离部署

可以按组件拆分：

- 设备 A：WebUI，监听私网地址，代理到设备 B。
- 设备 B：Gateway、mem0、OpenKB、rela-mem 和数据库。
- 本机：TUI，直接连接设备 B 的 Gateway。

部署时每台设备运行仓库中自己负责的部分；当前版本不提供远程部署或 SSH 编排。非 loopback 访问应使用 Tailscale、WireGuard、SSH 隧道或带认证的 TLS 反向代理。Gateway 当前没有内置认证，不应直接暴露到公网。

远程 TUI 需要注意：Agent 运行在 Gateway 所在设备，Workspace 路径必须在两台设备上同时存在，或使用共享目录。

## 常用命令

| 命令 | 作用 |
| --- | --- |
| `./bin/icarus install [app]` | 安装应用依赖、构建应用镜像、拉取中间件镜像 |
| `./bin/icarus config validate` | 校验有效拓扑，不依赖 Docker 或 Secret |
| `./bin/icarus config show [component]` | 查看有效配置和来源文件 |
| `./bin/icarus start [component]` | 启动组件及 required 依赖 |
| `./bin/icarus stop [component]` | 停止目标；无参数时逆序停止默认 stack |
| `./bin/icarus status [component]` | 查看 mode、地址、状态和依赖降级 |
| `./bin/icarus logs <component>` | 查看日志，默认持续跟随 |
| `./bin/icarus tui` | 打开本地 TUI，不隐式启动 Gateway |

## 项目结构

```text
apps/
├── agent/       Agent Runtime、模型接入、插件和持久化
├── gateway/     WebSocket RPC 服务
├── tui/         Textual 终端客户端
├── webui/       浏览器工作台与同源代理
├── mem0/        长期记忆服务
├── openkb/      知识库服务
├── rela-mem/    人物档案与关系服务
└── argus/       实验性策略应用（未纳入生命周期）
infra/           PostgreSQL、FalkorDB 等仓库中间件定义
packages/        应用间共享的数据模型和协议
scripts/         `icarus` 生命周期控制面
spec/            跨应用需求入口
docs/            产品、路线图、仓库基建和功能设计
skills/          生产基础技能源约定
.agents/skills/  开发期技能参考
```

## 开发与测试

使用每个应用自己的环境和脚本，根目录不创建共享 `.venv`：

```bash
make test                 # 根控制面 + 各应用测试
make test-agent
make test-gateway
make test-tui
make test-mem0
make test-openkb
make test-rela-mem
make test-rela-mem-integration
```

常用检查：

```bash
./bin/icarus config validate
git diff --check
```

CI 覆盖 Agent/Gateway 契约、根控制面、Mem0/OpenKB 契约、WebUI 构建、镜像构建、语法和仓库规范。真实模型或真实服务 smoke 必须使用隔离数据和临时凭据。

## 已知限制

v0.1.0 是开发者预览版，以下边界是明确的设计或验证范围：

- **单用户定位**：不是多租户、RBAC 或公网安全方案；Gateway 无内置认证，WebUI 仅有 Basic Auth。
- **平台限制**：原生受管进程目前依赖 Linux 可读 `/proc`；macOS/Windows 原生进程管理未实现。
- **数据迁移**：不自动迁移旧 JSONL Session 数据；数据库没有自动迁移框架。
- **rela-mem 切换**：从旧三合一 Compose 切换前必须人工停止旧项目，不能让新旧数据库同时挂载同一数据目录。
- **服务边界**：mem0 的 PostgreSQL 仍为 bundled；Argus 未登记；不提供远程部署、SSH 编排或镜像发布。
- **TUI 测试基线**：仓库中存在 13 个既有快照失败；它们不表示本轮功能回归，但 v0.1.0 不宣称 TUI 测试全绿。

## 文档

- [统一组件生命周期架构](docs/spec/2026-10-19-component-lifecycle/arch.md)
- [统一组件生命周期设计](docs/spec/2026-10-19-component-lifecycle/design.md)
- [实施与验收记录](docs/spec/2026-10-19-component-lifecycle/execution.md)
- [仓库贡献指南](CONTRIBUTING.md)
- [基础设施与中间件说明](infra/README.md)
- 应用说明：[Agent](apps/agent/README.md)、[Gateway](apps/gateway/README.md)、[TUI](apps/tui/README.md)、[WebUI](apps/webui/README.md)、[rela-mem](apps/rela-mem/README.md)

## 许可证

Icarus 根项目许可证见 [LICENSE](LICENSE)。Mem0、OpenKB 等第三方源码和修改说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 及各应用的 `MODIFICATIONS.md`。
