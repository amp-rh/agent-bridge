import subprocess
from unittest.mock import patch

import pytest

from agent_bridge.domain.exceptions import AgentExecutionError, AgentTimeoutError
from agent_bridge.infrastructure.claude_executor import ClaudeSubprocessExecutor


class TestClaudeSubprocessExecutor:
    def test_successful_execution(self):
        executor = ClaudeSubprocessExecutor(agent_name="test", timeout=30)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="output", stderr="",
            )
            result = executor.execute("test prompt")

        assert result == "output"
        args = mock_run.call_args[0][0]
        assert "claude" in args
        assert "--agent" in args
        assert "test" in args
        assert "test prompt" in args

    def test_nonzero_exit_raises_execution_error(self):
        executor = ClaudeSubprocessExecutor(agent_name="test", timeout=30)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="error msg",
            )
            with pytest.raises(AgentExecutionError, match="error msg"):
                executor.execute("test prompt")

    def test_empty_stderr_uses_default_message(self):
        executor = ClaudeSubprocessExecutor(agent_name="test", timeout=30)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="",
            )
            with pytest.raises(AgentExecutionError, match="Agent execution failed"):
                executor.execute("test prompt")

    def test_timeout_raises_timeout_error(self):
        executor = ClaudeSubprocessExecutor(agent_name="test", timeout=1)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=1)
            with pytest.raises(AgentTimeoutError, match="timed out"):
                executor.execute("test prompt")
