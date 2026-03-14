from __future__ import annotations

import httpx
import pytest
from starlette.applications import Starlette
from starlette.routing import Mount

from agent_bridge.application.execute_task import ExecuteTask
from agent_bridge.domain.exceptions import AgentExecutionError
from agent_bridge.domain.model import AgentConfig
from agent_bridge.presentation.a2a import create_a2a_routes
from agent_bridge.presentation.mcp_server import create_mcp_server


class FakeExecutor:
    def __init__(self, response: str = "fake output") -> None:
        self.response: str | AgentExecutionError = response
        self.last_prompt: str | None = None

    def execute(self, prompt: str) -> str:
        self.last_prompt = prompt
        if isinstance(self.response, AgentExecutionError):
            raise self.response
        return self.response

    def set_error(self, error: AgentExecutionError) -> None:
        self.response = error


@pytest.fixture
def fake_executor():
    return FakeExecutor()


@pytest.fixture
def test_config():
    return AgentConfig(name="agent", description="Claude agent")


@pytest.fixture
def test_app(fake_executor, test_config):
    execute_task = ExecuteTask(fake_executor)
    mcp = create_mcp_server(execute_task, test_config)
    mcp_app = mcp.streamable_http_app()
    a2a_routes = create_a2a_routes(execute_task, test_config)
    return Starlette(routes=[*a2a_routes, Mount("/mcp", app=mcp_app)])


@pytest.fixture
def client(test_app):
    transport = httpx.ASGITransport(app=test_app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")
