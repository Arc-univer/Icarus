import asyncio

from agent_app.contracts.prompt import PromptContributionEvent
from icarus.core.contracts.input import UserInputEvent
from apps.agent.test.agent_app.plugins.knowledge.test_plugin import make_plugin


def test_knowledge_guidance_does_not_query_or_upload(tmp_path):
    async def run():
        backend, target = make_plugin(tmp_path)
        event = UserInputEvent(task_id="task", prompt="help")
        assert target.accepts_event("user-input", event)
        published = []
        async def publish(value):
            published.append(value)
        target.bind_publisher(publish)
        await target.consume("user-input", event)
        assert len(published) == 1 and isinstance(published[0], PromptContributionEvent)
        content = published[0].sections[0].content
        assert "knowledge_query" in content and "knowledge_read" in content
        assert "引用" in content and "不" in content
        assert backend.calls == []
    asyncio.run(run())
