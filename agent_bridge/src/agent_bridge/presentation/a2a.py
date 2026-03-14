from __future__ import annotations

import uuid

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from agent_bridge.application.build_agent_card import BuildAgentCard
from agent_bridge.application.execute_task import ExecuteTask
from agent_bridge.domain.model import AgentConfig


def create_a2a_routes(execute_task: ExecuteTask, config: AgentConfig) -> list[Route]:
    card_builder = BuildAgentCard(config)

    async def handle_agent_card(request: Request) -> JSONResponse:
        return JSONResponse(card_builder.execute())

    async def handle_a2a(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None},
                status_code=400,
            )

        rpc_id = body.get("id")
        method = body.get("method")
        params = body.get("params", {})

        if method == "tasks/send":
            return await _handle_task_send(execute_task, rpc_id, params)

        return JSONResponse(
            {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": rpc_id},
            status_code=400,
        )

    return [
        Route("/.well-known/agent.json", handle_agent_card),
        Route("/a2a", handle_a2a, methods=["POST"]),
    ]


async def _handle_task_send(execute_task: ExecuteTask, rpc_id, params: dict) -> JSONResponse:
    message = params.get("message", {})
    parts = message.get("parts", [])
    prompt = ""
    for part in parts:
        if part.get("type") == "text":
            prompt += part.get("text", "")

    if not prompt:
        return JSONResponse(
            {"jsonrpc": "2.0", "error": {"code": -32602, "message": "No text content in message"}, "id": rpc_id},
            status_code=400,
        )

    task_id = params.get("id", str(uuid.uuid4()))
    result = await execute_task.async_execute(prompt, task_id)

    return JSONResponse({
        "jsonrpc": "2.0",
        "result": {
            "id": result.task_id,
            "status": {"state": result.state},
            "artifacts": [{"parts": [{"type": "text", "text": result.output}]}],
        },
        "id": rpc_id,
    })
