from mcp.server.fastmcp import FastMCP

from agent_bridge.application.execute_task import ExecuteTask
from agent_bridge.domain.model import AgentConfig


def create_mcp_server(execute_task: ExecuteTask, config: AgentConfig) -> FastMCP:
    mcp = FastMCP(config.name, instructions=config.description)

    @mcp.tool()
    def run_task(prompt: str) -> str:
        """Send a task to the agent and return its response."""
        result = execute_task.execute(prompt)
        if result.state == "failed":
            raise RuntimeError(result.output)
        return result.output

    return mcp
