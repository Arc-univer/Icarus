from agent_app.plugins.builtin_tools.config import PluginConfig
from icarus.core.plugin import BasePlugin


class BuiltinToolsPlugin(BasePlugin):
    config_schema = PluginConfig
    def build_tools(self):
        return self._tools
