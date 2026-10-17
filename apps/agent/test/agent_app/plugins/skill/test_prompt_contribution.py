import asyncio

from agent_app.contracts.prompt import PromptContributionEvent
from agent_app.plugins.skill.models import SkillDefinition
from icarus.core.contracts.input import UserInputEvent
from icarus.core.run_control import TaskContextInputResultEvent
from apps.agent.test.agent_app.plugins.skill.test_plugin import plugin


def test_skill_guidance_lists_bounded_metadata_without_loading_skill_body(tmp_path):
    async def run():
        skills = [SkillDefinition(f"skill-{i:02}", "fixture skill", tmp_path / f"skill-{i:02}" / "SKILL.md", "workspace") for i in range(20)]
        target, jobs = plugin(tmp_path, skills=skills, allow_produce=False, allow_evolve=False)
        assert target.accepts_event("user-input", UserInputEvent(task_id="task", prompt="help"))
        published = []
        async def publish(event):
            published.append(event)
        target.bind_publisher(publish)
        await target.consume("user-input", UserInputEvent(task_id="task", prompt="help"))
        contribution = next(event for event in published if isinstance(event, PromptContributionEvent))
        assert contribution.status == "completed"
        content = contribution.sections[0].content
        assert "skills_list" in content and "skill_search" in content
        assert "SKILL.md" in content and "读取" in content
        assert "skill-00" in content and "skill-08" not in content
        assert len(content) < 2000
        assert "不可信" in content
        assert "当前未开放" in content
        assert not jobs.produce_calls and not jobs.evolve_calls
        assert not target.accepts_event("unrelated", TaskContextInputResultEvent(task_id="task", request_event_id="request", status="accepted"))
    asyncio.run(run())


def test_skill_catalog_failure_is_a_terminal_prompt_failure(tmp_path):
    async def run():
        target, jobs = plugin(tmp_path)
        def fail(*args):
            raise RuntimeError("PRIVATE-CATALOG-ERROR")
        target.catalog.list_skills = fail
        published = []
        async def publish(event):
            published.append(event)
        target.bind_publisher(publish)
        await target.consume("user-input", UserInputEvent(task_id="task", prompt="help"))
        event = next(event for event in published if isinstance(event, PromptContributionEvent))
        assert event.status == "failed"
        assert "PRIVATE-CATALOG-ERROR" not in str(event)
    asyncio.run(run())
