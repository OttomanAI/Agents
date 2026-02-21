# Agent Development Guide

## Objective
Build reliable, maintainable agent behavior with clear boundaries between core logic, tools, and triggers.

## Engineering standards
- Prefer small, composable functions with explicit inputs and outputs.
- Raise clear exceptions for invalid input and cover those paths with tests.
- Keep all side effects at the edges (`tools` and `triggers`), not in core logic.
- Use type hints for public functions and dataclasses for structured payloads.

## Project structure expectations
- `src/agent/core`: deterministic business logic.
- `src/agent/tools`: command-line and utility entry points.
- `src/agent/triggers`: scheduled or event-style runners.
- `tests`: unit tests aligned to module behavior.

## Validation checklist
- `pytest` passes locally.
- CLI commands execute without stack traces.
- New behavior is documented in `README.md`.
