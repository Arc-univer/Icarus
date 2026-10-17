import asyncio

from agent_app.contracts.prompt import PromptContributionEvent
from agent_app.plugins.builtin_tools.plugin import BuiltinToolsPlugin
from icarus.core.contracts.input import UserInputEvent


def test_builtin_guidance_describes_real_file_and_shell_boundaries():
    async def run():
        target = BuiltinToolsPlugin("builtin-tools")
        published = []
        async def publish(event):
            published.append(event)
        target.bind_publisher(publish)
        await target.consume("user-input", UserInputEvent(task_id="task", prompt="help"))
        assert len(published) == 1 and isinstance(published[0], PromptContributionEvent)
        content = published[0].sections[0].content
        assert "read" in content and "分页" in content
        assert "write" in content and "覆盖" in content
        assert "insert" in content and "行前" in content
        assert "bash" in content and "退出码" in content
    asyncio.run(run())
