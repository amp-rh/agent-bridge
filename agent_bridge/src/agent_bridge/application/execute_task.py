from __future__ import annotations

import asyncio
import uuid

from agent_bridge.domain.exceptions import AgentExecutionError
from agent_bridge.domain.model import TaskResult
from agent_bridge.domain.ports import AgentExecutor


class ExecuteTask:
    def __init__(self, executor: AgentExecutor) -> None:
        self._executor = executor

    def execute(self, prompt: str, task_id: str | None = None) -> TaskResult:
        task_id = task_id or str(uuid.uuid4())
        try:
            output = self._executor.execute(prompt)
            return TaskResult.completed(task_id, output)
        except AgentExecutionError as exc:
            return TaskResult.failed(task_id, str(exc))

    async def async_execute(self, prompt: str, task_id: str | None = None) -> TaskResult:
        return await asyncio.to_thread(self.execute, prompt, task_id)
