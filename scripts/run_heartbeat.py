"""Run the heartbeat trigger from source without installation."""

from agent.triggers.heartbeat import main


if __name__ == "__main__":
    raise SystemExit(main())
