import subprocess

from agent_bridge.domain.exceptions import AgentExecutionError, AgentTimeoutError


class ClaudeSubprocessExecutor:
    def __init__(self, agent_name: str, timeout: int) -> None:
        self._agent_name = agent_name
        self._timeout = timeout

    def execute(self, prompt: str) -> str:
        try:
            result = subprocess.run(
                [
                    "claude", "--print", "--dangerously-skip-permissions",
                    "--agent", self._agent_name, "-p", prompt,
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise AgentTimeoutError(f"Agent timed out after {self._timeout}s") from exc

        if result.returncode != 0:
            raise AgentExecutionError(result.stderr or "Agent execution failed")
        return result.stdout
