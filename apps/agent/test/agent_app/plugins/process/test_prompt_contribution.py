import asyncio

from agent_app.contracts.prompt import PromptContributionEvent
from icarus.core.contracts.input import UserInputEvent
from apps.agent.test.agent_app.plugins.process.test_plugin import create_runtime


def test_process_guidance_does_not_start_or_query_a_process(tmp_path):
    async def run():
        target, runtime, events = create_runtime(tmp_path)
        await target.consume("user-input", UserInputEvent(task_id="task", prompt="help"))
        assert len(events) == 1 and isinstance(events[0], PromptContributionEvent)
        assert events[0].status == "completed"
        content = events[0].sections[0].content
        assert "background_process" in content
        assert "ready" in content
        assert "logs" in content
        assert not target._started
    asyncio.run(run())
