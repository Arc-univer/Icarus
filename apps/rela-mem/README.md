# rela-mem

独立人物关系与档案服务。Mem0 记录事件/经历；rela-mem 保存人物身份、圈子、关系和档案。分类由调用方负责，本服务不运行 LLM，不导入 Agent/Gateway/Argus。

## 启动

需要 Python 3.12 与 Docker Compose。

```bash
bash apps/rela-mem/scripts/install.sh
```

复制 `settings.example.json` 到部署用配置文件，修改 `identity.user` 与 `identity.agent`。当前设备可配置 `removel / 鱼梦`、`icarus / Icarus`；这不是其他部署的默认用户。

在仓库根 `.env` 或进程环境设置以下值（不要提交真实值）：

```dotenv
ICARUS_DATA_DIR=/absolute/path/to/icarus-data
RELA_MEM_API_TOKEN=<nonempty-token>
RELA_MEM_FALKORDB_PASSWORD=<nonempty-password>
RELA_MEM_PG_PASSWORD=<nonempty-password>
RELA_MEM_SETTINGS_FILE=/absolute/path/to/settings.json
```

从仓库根运行：

```bash
docker compose --env-file .env -f apps/rela-mem/docker-compose.yaml up -d --build --wait
```

默认仅绑定 loopback，应用 `8767`、FalkorDB `16379`、PostgreSQL `15432`。通过 `RELA_MEM_BIND_ADDRESS` 和 `RELA_MEM_DB_BIND_ADDRESS` 配置用户自有服务器的私网地址；不要将无 TLS 的数据库开放到公网。外部数据库部署可以只启动应用服务（`up --no-deps rela-mem`），并在 JSON 中配置远端连接信息。

持久数据是明确的 bind mount：

```text
$ICARUS_DATA_DIR/services/rela-mem/falkordb
$ICARUS_DATA_DIR/services/rela-mem/postgres
```

`docker compose down` 不会删除这些数据。镜像本地构建为 `rela-mem:dev`，不自动推送。

## 本机开发

设置 `RELA_MEM_CONFIG` 指向 JSON 配置；将数据库 host/port 改为本机暴露的端口。应用会在开发时加载仓库根 `.env`（不覆盖已设置的环境变量）；容器只读取注入的环境和挂载配置。

```bash
apps/rela-mem/.venv/bin/python apps/rela-mem/scripts/manage.py check-config
apps/rela-mem/.venv/bin/python apps/rela-mem/scripts/manage.py serve
# 或在 apps/rela-mem 下
.venv/bin/uvicorn main:app --app-dir src
```

`src` 直接是 import root，测试镜像相同层级，没有 `src/rela_mem` 包层。每个应用使用独立环境以避免 `config` 等通用模块名相互冲突。

初始化在应用 lifespan 中完成；独立脚本也可重复执行：

```bash
apps/rela-mem/.venv/bin/python apps/rela-mem/scripts/init_graph.py
apps/rela-mem/.venv/bin/python apps/rela-mem/scripts/init_postgres.py
```

不做自动数据迁移、不清理已有数据。特殊身份冲突或图约束验证失败会拒绝启动。

## REST 使用

除 `/healthz` 外，所有 API（包括 `/openapi.json`）均需要 `Authorization: Bearer <token>`。默认不公开 Swagger 页面。

```bash
curl http://127.0.0.1:8767/healthz
curl -H "Authorization: Bearer $RELA_MEM_API_TOKEN" http://127.0.0.1:8767/openapi.json
```

端点覆盖人物、别名、精确身份解析、档案/历史/关键词搜索、圈子/成员、关系与最短路径。详细字段由 OpenAPI 提供；背景设计见 [design](docs/spec/2026-10-18-rela-mem/design.md)。

- 姓名 `name` 别名允许重名，用 `/v1/persons?query=小张` 返回候选。
- `/v1/identity/resolve?namespace=qq&value=123456` 只查精确身份，没找到返回 `200 {"person":null}`。
- 档案 key 不限制语义，只限制小写 ASCII、下划线与点分格式。`GET /v1/persons/{id}/profile?q=猫罐头` 搜当前有效档案的 key 和 JSON 文本。
- 写档案只追加，同一 key 按 `recorded_at DESC,id DESC` 取最新；回填时间须有时区且不能在未来。
- 删除档案用 `DELETE /v1/persons/{id}/profile/{key}?source=agent&source_ref=...`；追加 `deleted` 历史，不物理擦除。合法 JSON null 与删除不同。
- `source_ref` 是来源引用，不是幂等键。写超时不能盲目重试；重复请求可能增加历史或覆盖期间的新值。
- `a → b` 表示“a 是 b 的 xxx”。双向关系必须填 `forward_detail` 与 `reverse_detail`，内容更新也必须同时提交两者；服务规范化双向端点但不改变语义。
- 关系查询保留存储 `direction=one_way|two_way`，另用 `relative_direction` 和 `detail` 提供查询视角。
- 最短路径按无向连接遍历 active 关系，不推导业务关系；最多 5 跳且有 5000 节点/邻接行预算，超额明确报错。
- 人物/圈子归档不删除历史。单用户、静态 Bearer Token，不实现 RBAC、多租户、PII 加密、硬删除/合并。

## 测试

```bash
make test-rela-mem                 # 无数据库的单元/HTTP 契约/脚本测试
make test-rela-mem-integration     # 含真实数据库测试
```

集成测试需要**独立**的本机实例，不得指向用户数据库：

- FalkorDB：`127.0.0.1:26379`，密码 `rela-test-graph-password`；
- PostgreSQL：`127.0.0.1:25432`，用户 `rela_mem`、数据库 `rela_mem_test`、密码 `rela-test-pg-password`。
- 可用 `RELA_TEST_GRAPH_PORT` / `RELA_TEST_PG_PORT` 调整测试端口；每个测试创建随机测试图和 schema，结束清理自己的对象。

只读真实 HTTP 冒烟：

```bash
apps/rela-mem/.venv/bin/python apps/rela-mem/scripts/smoke_rest.py --url http://127.0.0.1:8767
```

明确向测试服务写种子（记录会保留，脚本不删除数据）：

```bash
apps/rela-mem/.venv/bin/python apps/rela-mem/scripts/seed_demo.py --url http://127.0.0.1:8767 --allow-write
```

本期没有 Agent 插件、Argus 接入、WebUI、统一生命周期注册或镜像发布。
