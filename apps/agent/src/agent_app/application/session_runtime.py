"""One Session-scoped Agent execution environment."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

from icarus.core.hooks import HookDispatcher, HookRegistry
from icarus.runtime import (
    PluginManager,
    PluginRuntimeHost,
)
from icarus.runtime.session import SessionHost
from icarus.core.run_control import TaskChannelRegistry
from icarus.runtime.assets import PersistenceRuntime
from icarus.core.identity import SessionIdentity
from icarus.core.tools import ToolRegistry
from agent_app.config import ConfigModel
from icarus.core.models.messages import Message
from icarus.core.runtime_update import RuntimeUpdate


UpdatePublisher = Callable[[RuntimeUpdate], Awaitable[None]]


DEFAULT_SYSTEM_PROMPT = """你是 Icarus Agent。准确理解用户目标，必要时使用工具完成任务，并在完成后给出清晰的结果。

长期记忆是你与当前用户持续相处形成的、你自己的长期记忆，也是你保持连续性的一部分。自然使用你记得的事实、偏好、约定和决定，不要说“根据记忆库”“检索结果显示”或用查看外部资料的口吻回答，也不要为了展示记忆而复述用户的历史。默认相信相关记忆；如果用户当前明确纠正了旧信息，以用户当前的明确说法为准，并在合适时更新原有记忆。当自动记忆或 memory_recall 没有找到相关内容时，这只表示你此刻想不起来；面向用户自然说“我记不起来了”，不要说“没有召回到记忆”“没有关于你的记忆”或“记忆库为空”，也不要据此断言长期记忆不存在。

你可以自主记录和维护值得跨会话保留的明确偏好、稳定事实、协作约定、重要决定和纠正，无需每次征求用户确认。新增内容使用记忆写入能力，明确纠正优先更新已有记忆。不要记录闲聊细节、临时状态、猜测、未经确认的推断，也不要记录密码、Token、Cookie、私钥或其他认证凭据。用户明确要求不要记住时不要记录。除非用户询问或当前任务需要，不要机械汇报内部的记忆写入或更新动作。删除或遗忘前先确认目标和范围。

普通聊天默认简短、自然、直接，像人与人正常交流一样，只说足够回答当前问题的内容。用户要求详细解释，或复杂任务需要步骤、风险、证据和交付结果时，再按需要完整展开。"""


class SessionRuntime(SessionHost):
    """Manage one fixed Session through a manifest-driven Runtime Host."""

    def __init__(
        self,
        identity: SessionIdentity,
        *,
        config: ConfigModel,
        publish_update: UpdatePublisher,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        tools: list[str] | None = None,
        initial_messages: list[Message] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.identity = identity
        self.workspace_path = identity.workspace_path
        self.config = config
        self.logger = logger or logging.getLogger("icarus.agent.session")
        if config.icarus_data_dir is None:
            raise RuntimeError("ICARUS_DATA_DIR is required")

        self.hook_registry = HookRegistry()
        self.persistence = PersistenceRuntime(
            data_dir=config.icarus_data_dir,
            workspace_path=identity.workspace_path,
        )
        self.task_channels = TaskChannelRegistry(max_steps=config.agent.max_steps)
        self.tool_registry = ToolRegistry()
        self.plugin_manager = PluginManager(
            hook_dispatcher=HookDispatcher(self.hook_registry),
        )
        required = set(config.runtime.required_plugin_ids)
        self.runtime_host = PluginRuntimeHost(
            identity.workspace_path,
            identity.session_id,
            plugin_dirs=tuple(config.runtime.plugin_dirs),
            builtin_package="agent_app.plugins",
            required_plugin_ids=frozenset(required),
            plugin_configs=self._with_facilities({
                **config.runtime.plugin_config,
                "persistence": {
                    **config.runtime.plugin_config.get("persistence", {}),
                    "data_dir": config.icarus_data_dir,
                    "runtime": self.persistence,
                    "hook_registry": self.hook_registry,
                    "runtime_logger": self.logger,
                },
                "skill": {
                    **config.runtime.plugin_config.get("skill", {}),
                    "config_model": config,
                    "hook_registry": self.hook_registry,
                },
                "agent": {
                    **config.runtime.plugin_config.get("agent", {}),
                    "config_model": config,
                    "tool_registry": self.tool_registry,
                    "task_channels": self.task_channels,
                    "hook_registry": self.hook_registry,
                },
                "user-input": {
                    **config.runtime.plugin_config.get("user-input", {}),
                    "task_channels": self.task_channels,
                },
                "builtin-tools": {
                    **config.runtime.plugin_config.get("builtin-tools", {}),
                    "max_output_bytes": (
                        config.agent.tool_execution.max_result_file_bytes
                    ),
                    "default_read_lines": (
                        config.agent.tool_execution.default_read_lines
                    ),
                    "max_read_lines": (
                        config.agent.tool_execution.max_read_lines
                    ),
                },
                "blackboard": {
                    **config.runtime.plugin_config.get("blackboard", {}),
                    "model_role": config.model_roles.agent,
                    "system_prompt": system_prompt,
                    "tools": tools,
                    "initial_messages": list(initial_messages or []),
                    "config_model": config,
                    "hook_registry": self.hook_registry,
                },
                "runtime-update": {
                    **config.runtime.plugin_config.get("runtime-update", {}),
                    "publish_update": publish_update,
                },
                "mcp": {
                    **config.runtime.plugin_config.get("mcp", {}),
                    "servers": config.mcp_servers,
                    "default_page_size": (
                        config.agent.tool_execution.default_page_size
                    ),
                    "max_page_size": (
                        config.agent.tool_execution.max_page_size
                    ),
                },
                "memory": {
                    **config.runtime.plugin_config.get("memory", {}),
                },
                "knowledge": {
                    **config.runtime.plugin_config.get("knowledge", {}),
                    "default_page_size": (
                        config.agent.tool_execution.default_page_size
                    ),
                    "max_page_size": (
                        config.agent.tool_execution.max_page_size
                    ),
                },
                "process": {
                    **config.runtime.plugin_config.get("process", {}),
                    "default_page_size": (
                        config.agent.tool_execution.default_page_size
                    ),
                    "max_page_size": (
                        config.agent.tool_execution.max_page_size
                    ),
                },
            }),
            before_restore=self._register_links,
            before_ready=self._finalize_links,
            plugin_manager=self.plugin_manager,
            tool_registry=self.tool_registry,
            logger=self.logger,
        )
        SessionHost.__init__(self, identity, runtime_host=self.runtime_host,
            assets=self.persistence, task_channels=self.task_channels, logger=self.logger,
            checkpoint_plugin_ids=("blackboard",))

    def _with_facilities(self, configs):
        user_configs = {key: dict(value) for key, value in self.config.runtime.plugin_config.items()}
        for key in configs:
            user_configs.setdefault(key, {})
        user_configs["builtin-tools"] = {k: v for k, v in configs["builtin-tools"].items()}
        user_configs["mcp"] = {k: v for k, v in configs["mcp"].items()}
        user_configs["knowledge"] = {k: v for k, v in configs["knowledge"].items()}
        user_configs["process"] = {k: v for k, v in configs["process"].items()}
        return {key: {**value, "runtime": self.persistence, "identity": self.identity,
                      "task_channels": self.task_channels, "_user_config": user_configs[key]}
                for key, value in configs.items()}

    async def _register_links(self, host):
        from agent_app.plugins.blackboard.plugin import BlackboardPlugin
        from agent_app.plugins.memory.plugin import MemoryPlugin
        boards = [r.plugin for r in host.graph.registrations.values() if isinstance(r.plugin, BlackboardPlugin)]
        memories = [r.plugin for r in host.graph.registrations.values() if isinstance(r.plugin, MemoryPlugin)]
        for board in boards:
            for memory in memories:
                handle = board.region_registry.register(memory.region_definition)
                memory.region_registration = handle

    async def _finalize_links(self, host):
        from agent_app.plugins.blackboard.plugin import BlackboardPlugin
        active = set(host.graph.registrations)
        for registration in host.graph.registrations.values():
            plugin = registration.plugin
            if isinstance(plugin, BlackboardPlugin):
                plugin.region_registry.remove_inactive_owners(active)
                plugin.region_store.initialize()
                plugin.region_registry.freeze()

