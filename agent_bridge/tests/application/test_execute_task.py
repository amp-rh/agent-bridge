import pytest

from agent_bridge.application.execute_task import ExecuteTask
from agent_bridge.domain.exceptions import AgentExecutionError, AgentTimeoutError


class FakeExecutor:
    def __init__(self, response: str = "ok") -> None:
        self.response = response
        self.last_prompt: str | None = None

    def execute(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


class FailingExecutor:
    def __init__(self, error: AgentExecutionError) -> None:
        self._error = error

    def execute(self, prompt: str) -> str:
        raise self._error


class TestExecuteTask:
    def test_successful_execution(self):
        executor = FakeExecutor("hello world")
        use_case = ExecuteTask(executor)
        result = use_case.execute("say hello", task_id="t1")

        assert result.task_id == "t1"
        assert result.state == "completed"
        assert result.output == "hello world"
        assert executor.last_prompt == "say hello"

    def test_generates_task_id_when_not_provided(self):
        use_case = ExecuteTask(FakeExecutor())
        result = use_case.execute("test")
        assert result.task_id

    def test_execution_error_returns_failed(self):
        executor = FailingExecutor(AgentExecutionError("agent crashed"))
        use_case = ExecuteTask(executor)
        result = use_case.execute("test", task_id="t2")

        assert result.state == "failed"
        assert "agent crashed" in result.output

    def test_timeout_error_returns_failed(self):
        executor = FailingExecutor(AgentTimeoutError("timed out"))
        use_case = ExecuteTask(executor)
        result = use_case.execute("test", task_id="t3")

        assert result.state == "failed"
        assert "timed out" in result.output

    @pytest.mark.anyio
    async def test_async_execute(self):
        executor = FakeExecutor("async result")
        use_case = ExecuteTask(executor)
        result = await use_case.async_execute("prompt", task_id="t4")

        assert result.state == "completed"
        assert result.output == "async result"
