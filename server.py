#!/usr/bin/env python3
"""Dual-protocol MCP + A2A server exposing a Claude agent."""

import asyncio
import json
import os
import subprocess
import uuid

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

AGENT_NAME = os.environ.get("AGENT_NAME", "agent")
AGENT_TIMEOUT = int(os.environ.get("AGENT_TIMEOUT", "300"))
AGENT_DESCRIPTION = os.environ.get("AGENT_DESCRIPTION", "Claude agent")
PORT = int(os.environ.get("PORT", "8080"))


def execute_agent(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions",
         "--agent", AGENT_NAME, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=AGENT_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Agent execution failed")
    return result.stdout


async def async_execute_agent(prompt: str) -> str:
    return await asyncio.to_thread(execute_agent, prompt)


# --- MCP Server ---

mcp = FastMCP(AGENT_NAME, instructions=AGENT_DESCRIPTION)


@mcp.tool()
def run_task(prompt: str) -> str:
    """Send a task to the agent and return its response."""
    return execute_agent(prompt)


# --- A2A Endpoints ---

def agent_card() -> dict:
    public_url = os.environ.get("PUBLIC_URL", "")
    return {
        "name": AGENT_NAME,
        "description": AGENT_DESCRIPTION,
        "url": f"{public_url}/a2a",
        "version": "0.1.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "run_task",
                "name": "Run Task",
                "description": f"Execute a task using {AGENT_NAME}",
                "tags": ["agent"],
            }
        ],
    }


async def handle_agent_card(request: Request) -> JSONResponse:
    return JSONResponse(agent_card())


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
        return await _handle_task_send(rpc_id, params)

    return JSONResponse(
        {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": rpc_id},
        status_code=400,
    )


async def _handle_task_send(rpc_id, params: dict) -> JSONResponse:
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

    try:
        output = await async_execute_agent(prompt)
    except (subprocess.TimeoutExpired, RuntimeError) as exc:
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {
                "id": task_id,
                "status": {"state": "failed"},
                "artifacts": [{"parts": [{"type": "text", "text": str(exc)}]}],
            },
            "id": rpc_id,
        })

    return JSONResponse({
        "jsonrpc": "2.0",
        "result": {
            "id": task_id,
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"type": "text", "text": output}]}],
        },
        "id": rpc_id,
    })


# --- ASGI App Composition ---

mcp_app = mcp.streamable_http_app()

app = Starlette(
    routes=[
        Route("/.well-known/agent.json", handle_agent_card),
        Route("/a2a", handle_a2a, methods=["POST"]),
        Mount("/mcp", app=mcp_app),
    ],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
