from agent.tools.run import main


def test_cli_main_prints_message(capsys) -> None:
    exit_code = main(
        [
            "--content",
            "Provide a concise sprint recap.",
            "--system-message",
            "Respond in a professional and direct tone.",
            "--knowledge-base",
            "Sprint scope includes API integration and dashboard polish.",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "System message: Respond in a professional and direct tone." in captured.out
    assert "Knowledge base: Sprint scope includes API integration and dashboard polish." in captured.out
    assert "Output text: Provide a concise sprint recap." in captured.out
