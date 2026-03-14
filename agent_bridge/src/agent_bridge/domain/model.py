from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from agent_bridge.domain.exceptions import ConfigError


@dataclass(frozen=True)
class AgentConfig:
    name: str = "agent"
    description: str = "Claude agent"
    timeout: int = 300
    public_url: str = ""
    prompt_text: str | None = None
    mcp_servers: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ConfigError("Agent name must not be empty")
        if self.timeout <= 0:
            raise ConfigError("Agent timeout must be positive")


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    state: str
    output: str

    @classmethod
    def completed(cls, task_id: str, text: str) -> TaskResult:
        return cls(task_id=task_id, state="completed", output=text)

    @classmethod
    def failed(cls, task_id: str, error: str) -> TaskResult:
        return cls(task_id=task_id, state="failed", output=error)


@dataclass(frozen=True)
class AgentCard:
    config: AgentConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.config.name,
            "description": self.config.description,
            "url": f"{self.config.public_url}/a2a",
            "version": "0.1.0",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
                "stateTransitionHistory": False,
            },
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "skills": [
                {
                    "id": "run_task",
                    "name": "Run Task",
                    "description": f"Execute a task using {self.config.name}",
                    "tags": ["agent"],
                }
            ],
        }
