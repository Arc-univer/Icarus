import asyncio

from agent_app.contracts.prompt import PromptContributionEvent
from icarus.core.contracts.input import UserInputEvent
from icarus.core.run_control import TaskContextInputEvent
from apps.agent.test.agent_app.plugins.memory.test_plugin import BackendStub, bind_background, item, plugin


def test_memory_guidance_precedes_recall_without_duplicating_records():
    async def run():
        target = plugin(BackendStub([item(content="UNIQUE-MEMORY-FACT")]))
        published = []
        bind_background(target, published)
        await target.consume("user-input", UserInputEvent(task_id="task", prompt="hello"))
        await asyncio.gather(*target._recall_tasks)
        guidance = [event for event in published if isinstance(event, PromptContributionEvent)]
        assert len(guidance) == 1
        assert published[0] is guidance[0]
        content = guidance[0].sections[0].content
        assert guidance[0].status == "completed"
        assert "你自己的长期记忆" in content
        assert "我记不起来了" in content
        assert "不要记录密码、Token、Cookie、私钥" in content
        assert "删除或遗忘前先确认目标和范围" in content
        assert "无需每次征求用户确认" in content
        assert "UNIQUE-MEMORY-FACT" not in content
        recalled = [event for event in published if isinstance(event, TaskContextInputEvent)]
        assert len(recalled) == 1 and "UNIQUE-MEMORY-FACT" in recalled[0].content
        await target.stop()
    asyncio.run(run())
