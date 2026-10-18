# rela-mem 后端架构

本文依据 `src/`、`test/`、Dockerfile 和 Compose 描述当前实现，不把 Agent/Argus 适配写成已有能力。目标设计见 [design.md](design.md)，阶段与验证记录见 [plan.md](plan.md)。

## 边界

rela-mem 是独立 REST 服务，不导入 Agent、Gateway、Argus 或 Mem0。事件/档案分类由调用方决定；本服务保存人物身份、圈子、关系和档案，内部没有 LLM、插件运行时或后台认知流程。

## 代码路径

```text
main.create_app
  ├── config.load_settings：JSON、环境 Secret、严格校验
  ├── lifespan：图索引/约束、单表初始化、特殊身份 bootstrap
  ├── api.persons/profile/circles/relations
  │     └── domain.services 对应服务
  │           └── repositories 对应数据库访问
  └── shutdown：关闭 Redis 连接池与 PG engine
```

`src` 是 import root；`api/`、`domain/`、`schemas/`、`repositories/`、`utils/` 直接位于其中，没有额外 `rela_mem` 包层。`test/` 镜像源码层级，`test/integration` 包含跨层真实数据库用例。

HTTP 请求由 Pydantic 校验，统一将请求参数错误转为 400；服务层的 `ServiceError` 在 `main.py` 转为结构化 HTTP 错误，Redis/PG 故障映射为安全的 503，不暴露 SQL、连接凭据或异常正文。除 `/healthz` 外所有业务路由和 `/openapi.json` 要求 Bearer Token；默认不公开 Swagger。

## 图数据

`GraphClient` 封装 FalkorDB 异步查询和安全错误映射。参数通过绑定传递，代码中唯一动态拼接的标签/属性来自初始化常量。

节点为 `Person`、`Alias`、`Circle`，边为 `HAS_ALIAS`、`MEMBER_OF`、`RELATED_TO`。精确 Alias 使用计算属性 `identity_key` 唯一；`name` 不设置该属性，允许重名。人物的私有 `special_kind` 唯一属性限制 user/agent 各一个；普通 API 不能创建或更改特殊身份类别。

人物搜索按 display_name、alias.value/display_value 子串返回候选，不证明同一身份。每项附最多10个别名，仅投影 alias_id/namespace/value/display_value，先按人物聚合再按 person_id 分页；人物详情仍保留完整别名供调用方核验。

人物和初始别名在一个图查询内原子创建；唯一冲突不会留下无别名的新人物。Alias 删除同时清除该节点和归属边。成员以 `[person_id,circle_id]` 的确定性 JSON 编码唯一，离开时仅置 `left`。

双向关系规范化端点与称谓，只存一条边。`a→b` 始终指 a 是 b 的正向称谓；原始 `direction=one_way|two_way` 与查询投影 `relative_direction` 分离。双向内容 PATCH 必须同时提交正反内容。关系变更重算唯一键，冲突由数据库原子回滚。PATCH 的读后重建在同一图写查询内比较已读字段，发现并发变化返回 409，不覆盖期间的状态或称谓；DELETE 只原子设置失效字段，不重建旧快照。没有新增 version 字段。失效只置 `invalid`，不提供关系变更史。

最短路径通过批量邻接查询执行无向 BFS，最多 5 跳，每轮/累计有 5000 邻接行或节点预算。只通过 active 人物/关系，路径返回原始边方向而不推断亲属关系；超过预算报错，不截断后谎称无路径。

## 档案数据

`Database` 管理 SQLAlchemy async engine/session 和唯一业务表 `profile_entries`。schema 名经过严格校验；初始化、查询和测试使用同一配置。启动检查已有表的列类型/可空性、ID 默认值/主键、时间类型、状态约束和当前值索引，不兼容时明确拒绝而不是自动迁移。没有迁移框架或幂等/审计/历史附表。

每次写入追加一行，按 `recorded_at DESC,id DESC` 选择当前条目，再按状态、关键词和 keys 筛选。墓碑为 `status=deleted` + JSON null；合法的 active JSON null 不表示删除。`source_ref` 可重复，只作追溯。

`q` 在已选出的当前条目上对 key 和 JSON 文本执行大小写不敏感的字面子串匹配，转义 `%`、`_`、反斜线；不是语义搜索。历史按时间和 ID 倒序分页。游标携带查询指纹，修改过滤条件或格式损坏返回 400。

## 生命周期与部署

应用启动等待 FalkorDB 索引和约束 `OPERATIONAL`，然后建 PG 表、检查并创建特殊身份。已有特殊身份与配置冲突会失败，不自动迁移、覆盖或删除长期数据。

本期只提供 app 自己的 `scripts/install.sh`、`test.sh`、`manage.py` 与初始化脚本；根 Makefile 增加两个测试入口，没有接入根 `icarus` 全栈生命周期。

镜像只拷贝本应用源码和脚本，使用非 root 用户；配置只读挂载，Secret 由环境注入。Compose 同时提供 API/FalkorDB/PG，数据显式挂载在 `$ICARUS_DATA_DIR/services/rela-mem/`。API 默认宿主端口 8767，数据库 16379/15432，均默认绑定 loopback，可配置私网地址。

## 验证边界

自动测试涵盖配置、规范化/方向校验、认证和错误、真实图/PG CRUD、并发身份唯一、别名回滚、追加历史/墓碑/搜索、圈子/虚拟成员、关系反向 upsert/冲突/失效、BFS、种子和脚本。真实 HTTP/Docker 构建/重启验证结果见 plan 的实施记录；尚未执行的验证不得推定通过。

单元与契约测试入口 `make test-rela-mem`，真实库全量入口 `make test-rela-mem-integration`。测试只使用随机图和 schema，没有连接远端用户服务器或付费模型。
