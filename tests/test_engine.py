from agent.core import AgentEngine, AgentRequest


def test_engine_formats_output_from_required_inputs() -> None:
    engine = AgentEngine()
    request = AgentRequest(
        content="Escalate the deployment issue to on-call.",
        system_message="Use a concise operations tone.",
        knowledge_base="On-call rota: PagerDuty primary is Platform team.",
    )
    result = engine.respond(request)

    assert "System message: Use a concise operations tone." in result.content
    assert "Knowledge base: On-call rota: PagerDuty primary is Platform team." in result.content
    assert "Output text: Escalate the deployment issue to on-call." in result.content
    assert "Escalate the deployment issue" in result.content


def test_engine_rejects_blank_input() -> None:
    engine = AgentEngine()

    try:
        engine.respond(
            AgentRequest(
                content="   ",
                system_message="Stay professional.",
                knowledge_base="System runbook is approved.",
            )
        )
        assert False, "Expected ValueError for blank input"
    except ValueError as exc:
        assert "non-empty" in str(exc)
