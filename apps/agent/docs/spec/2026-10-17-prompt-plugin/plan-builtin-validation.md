# 内置插件贡献｜增量验证

> 2026-10-17，新增于同一开发周期的Prompt实现之上；用户授权接入合理插件指导并精简system。原功能验证见[plan-validation.md](plan-validation.md)。

## 本轮交付

memory/skill/process/knowledge/mcp/builtin-tools六个插件通过真实input→prompt.contribution参与准备，每个插件独立prompts.py。
Memory指导先发、召回/Region/ACK不变；Skill增加有界目录与写开关事实，生成Agent/Job通知不变；
Process只给使用规则；Knowledge不自动RAG；MCP不主动远端枚举，无server发空completed；基础工具保持原schema。

基础system1110→472字符/保守token（减少57.5%），3208→1374 UTF-8 bytes（减少57.2%）。
记忆规则迁到Memory贡献，通用身份、安全、事实、验证、表达规则保留。整次请求包含新增动态指导，
因此**不能把base减少量宣称为整次调用tokens/费用同幅下降**；动态指导每task进入当前User Prompt并进入历史。

## RED/GREEN

- T1四个测试RED（没有Memory贡献/Skill拒绝输入/Process无handler）→4GREEN。
- 原Memory事件序列断言只增加一条Prompt贡献，保留原Region→Context→Region顺序；三插件原套件恢复。
- T2四测试RED（Knowledge拒绝事件/MCP、Builtin无handler）→4GREEN。
- 六插件套件328passed（10.13s）。
- T3 base1110>600及真实socket中system仍含记忆规则RED→精简后GREEN；2项Gateway E2E5.79s。
- scanner两项RED（完整正文IO、元数据无界）→GREEN，Skill全套110passed2.39s；只读取16KiB以内frontmatter。
- mypy一次entries空list缺注解已修正，make typecheck-agent238文件通过；没有ignore掩盖。

## 最新全套

- make test-agent：**902 passed in42.03s**。
- make test-gateway：**34 passed in7.51s**，1条既有Starlette/AnyIO弃用warning。
- make typecheck-agent：**238 files，no issues**。
- make check-package-agent：wheel构建、12manifest、临时venv安装/非repo cwd导入通过。
- compileall Agent/Gateway src/test、git diff --check通过。

## 真实网络验证

`test_builtin_plugin_guidance_reaches_user_context_not_base_system` 使用实际Uvicorn/TCP/WebSocket、生产12插件/Agent/SQLite/模型适配器：
将六个来源设为required；模型HTTP请求的user消息含六个section（builtin-tool-use/knowledge-use/mcp-use/memory-use/process-use/skill-discovery），
system不含记忆专属段且短于800字符。MCP配置存在但没有任何/mcp网络请求。创建实际SKILL.md验证目录名称进入user，正文BODY-NOT-AUTO-INJECTED不进入。
另一项外部persona贡献/私有指令/Gateway重启E2E继续通过。

本轮不重复真实远端调用；上一轮一次受限deepseek-flash验证见原记录。本轮无新客户端/协议字段，无DB/框架变化。

## 取舍与审查

- 仅接入六个有实际工具业务的插件，persistence/runtime-update/user-input/agent不强制成为贡献者；避免日志回灌/输出循环。
- 工具指导不冒充persona静态层；采用已实现contributor能力，无新通用mixin或注册接口。
- Skill元数据收集以前读取全文件，本轮有界frontmatter是自动发现的必要IO边界；超过16KiB头部现在省略并warning，不截断语义。
- 旧base记忆断言移至Memory贡献测试，不删除记忆约束；旧文档草稿保留为历史设计，当前文案以base_prompt.py为准。
- 开发验收阶段未自动提交；之后按用户单独授权与前轮Prompt实现一并分层提交，不建分支/推送。

独立Opus增量审查完成：本轮范围未发现需修复的确定缺陷，无deferred minors。审查者另跑聚焦贡献/scanner15passed与六插件完整目录330passed10.15s；未将这些结果冒称主会话全套结果。
主会话最后真实socket2passed5.53s，optional-source/装配/边界9passed3.19s，文档链接/manifest/diff检查通过。

## 提交前复验

用户另行授权commit后重新执行：Agent **902 passed in43.99s**、Gateway **34 passed in7.86s**、
make typecheck-agent **238文件通过**，compileall通过。暂存检查发现新文件末尾额外空行，清理后再执行cached diff检查；
仅包含Agent/Gateway本功能实现、测试与所属文档，`.claude/`与忽略的临时证据不提交。
