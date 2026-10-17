from agent_app.contracts.prompt import PromptContributionEvent, PromptSection
from agent_app.plugins.builtin_tools.prompts import BUILTIN_TOOLS_GUIDANCE
from icarus.core.contracts.input import UserInputEvent
from icarus.core.plugin import handles
from agent_app.plugins.builtin_tools.config import PluginConfig
from icarus.core.plugin import BasePlugin


class BuiltinToolsPlugin(BasePlugin):
    config_schema = PluginConfig

    @handles(UserInputEvent)
    async def on_prompt_input(self, source_plugin_id: str, event: UserInputEvent):
        if event.task_id is None:
            return None
        return (PromptContributionEvent(task_id=event.task_id, status="completed",
            sections=(PromptSection("builtin-tool-use", "contributor", BUILTIN_TOOLS_GUIDANCE),)),)

    def build_tools(self):
        return self._tools
