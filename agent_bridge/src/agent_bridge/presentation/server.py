from starlette.applications import Starlette
from starlette.routing import Mount

from agent_bridge.application.execute_task import ExecuteTask
from agent_bridge.domain.model import AgentConfig
from agent_bridge.infrastructure.claude_executor import ClaudeSubprocessExecutor
from agent_bridge.presentation.a2a import create_a2a_routes
from agent_bridge.presentation.mcp_server import create_mcp_server


def build_app(config: AgentConfig) -> Starlette:
    executor = ClaudeSubprocessExecutor(
        agent_name=config.name,
        timeout=config.timeout,
    )
    execute_task = ExecuteTask(executor)

    mcp = create_mcp_server(execute_task, config)
    mcp_app = mcp.streamable_http_app()

    a2a_routes = create_a2a_routes(execute_task, config)

    return Starlette(
        routes=[
            *a2a_routes,
            Mount("/mcp", app=mcp_app),
        ],
    )
