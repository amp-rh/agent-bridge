from __future__ import annotations

from typing import Any

from agent_bridge.domain.model import AgentCard, AgentConfig


class BuildAgentCard:
    def __init__(self, config: AgentConfig) -> None:
        self._card = AgentCard(config=config)

    def execute(self) -> dict[str, Any]:
        return self._card.to_dict()
