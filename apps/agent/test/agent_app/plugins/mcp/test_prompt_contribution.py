import asyncio

import pytest

from agent_app.contracts.prompt import PromptContributionEvent
from agent_app.plugins.mcp.plugin import MCPPlugin
from icarus.core.contracts.input import UserInputEvent
from apps.agent.test.agent_app.plugins.mcp.test_plugin import BridgeStub, EmptyManagerStub, ManagerStub


@pytest.mark.parametrize("configured", [True, False])
def test_mcp_guidance_is_local_and_empty_configuration_completes(configured):
    async def run():
        bridge = BridgeStub()
        target = MCPPlugin("mcp", manager=ManagerStub() if configured else EmptyManagerStub(), bridge=bridge)
        published = []
        async def publish(event):
            published.append(event)
        target.bind_publisher(publish)
        await target.consume("user-input", UserInputEvent(task_id="task", prompt="help"))
        assert len(published) == 1 and isinstance(published[0], PromptContributionEvent)
        result = published[0]
        assert result.status == "completed"
        if configured:
            assert "mcp_tool_search" in result.sections[0].content
            assert "tool_ref" in result.sections[0].content
            assert "不代表" in result.sections[0].content
        else:
            assert result.sections == ()
        assert not bridge.is_running
    asyncio.run(run())
