from typing import Protocol


class AgentExecutor(Protocol):
    def execute(self, prompt: str) -> str: ...
