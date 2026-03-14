import argparse
import os
import sys

import uvicorn

from agent_bridge.infrastructure.config_loader import load_config
from agent_bridge.infrastructure.prompt_installer import PromptInstaller
from agent_bridge.presentation.server import build_app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="agent-bridge")
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Start the agent server")
    serve_parser.add_argument("--config", default=os.environ.get("AGENT_CONFIG_FILE"), help="Path to YAML config file")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    serve_parser.add_argument("--port", type=int, default=None, help="Bind port")

    check_parser = subparsers.add_parser("config-check", help="Validate config and print summary")
    check_parser.add_argument("--config", default=os.environ.get("AGENT_CONFIG_FILE"), help="Path to YAML config file")

    args = parser.parse_args(argv)

    if args.command is None:
        args.command = "serve"
        args.config = os.environ.get("AGENT_CONFIG_FILE")
        args.host = "0.0.0.0"
        args.port = None

    if args.command == "serve":
        _serve(args)
    elif args.command == "config-check":
        _config_check(args)


def _serve(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    PromptInstaller().install(config)
    port = args.port or int(os.environ.get("PORT", "8080"))
    app = build_app(config)
    uvicorn.run(app, host=args.host, port=port)


def _config_check(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    print(f"name:        {config.name}")
    print(f"description: {config.description}")
    print(f"timeout:     {config.timeout}")
    print(f"public_url:  {config.public_url}")
    print(f"prompt_text:  {'set' if config.prompt_text else 'not set'}")
    print(f"mcp_servers:  {'set' if config.mcp_servers else 'not set'}")
