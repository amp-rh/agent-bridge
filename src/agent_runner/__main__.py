"""Entrypoint: python -m agent_runner."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from agent_runner import __version__

log = logging.getLogger("agent_runner")


def _setup_logging(verbose: bool = False) -> None:
    """Configure logging with timestamps and level."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger = logging.getLogger("agent_runner")
    logger.setLevel(level)
    logger.addHandler(handler)


def _print_banner(config, mode: str) -> None:
    """Print startup banner with key config info."""
    features = []
    if config.a2a.enabled:
        features.append("a2a")
    if config.hooks.reflection.enabled:
        features.append("reflection")
    if config.hooks.audit.enabled:
        features.append("audit")

    log.info("agent-runner v%s", __version__)
    log.info(
        "Agent: %s | Model: %s | Mode: %s",
        config.agent.name,
        config.agent.model,
        mode,
    )

    if mode == "server":
        log.info(
            "Listening on %s:%d | Public URL: %s",
            config.server.host,
            config.server.port,
            config.server.public_url,
        )

    if features:
        log.info("Features: %s", ", ".join(features))

    mcp_count = len(config.mcp_servers)
    sub_count = len(config.subagents)
    if mcp_count or sub_count:
        log.info("MCP servers: %d | Subagents: %d", mcp_count, sub_count)


def main():
    parser = argparse.ArgumentParser(
        prog="agent-runner",
        description="Deploy Claude agents as MCP servers on Cloud Run.",
    )
    parser.add_argument("--config", help="Path to config YAML file")
    parser.add_argument("--task", help="Run a single task and exit (CLI mode)")
    parser.add_argument("--worker", action="store_true", help="Start Pub/Sub worker mode")
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate config and print resolved values, then exit",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--version", "-V", action="version", version=f"agent-runner {__version__}",
    )
    args = parser.parse_args()

    _setup_logging(verbose=args.verbose)

    from agent_runner.config import load_config

    try:
        config = load_config(args.config)
    except Exception as exc:
        if args.validate_config:
            print(f"Config validation failed: {exc}", file=sys.stderr)
            sys.exit(1)
        raise

    if args.validate_config:
        _validate_config(config)
        return

    if args.task:
        _print_banner(config, "cli")
        _run_cli(config, args.task)
    elif args.worker:
        _print_banner(config, "worker")
        _run_worker(config)
    else:
        _print_banner(config, "server")
        _run_server(config)


def _validate_config(config):
    """Print resolved config as YAML and exit."""
    import yaml

    print(yaml.dump(config.model_dump(), default_flow_style=False, sort_keys=False))


def _run_server(config):
    """Start MCP + A2A server via uvicorn."""
    import uvicorn

    from agent_runner.server import create_app

    app = create_app(config)
    uvicorn.run(app, host=config.server.host, port=config.server.port)


def _run_cli(config, task: str):
    """Run a single task via the Claude Agent SDK and exit."""
    from agent_runner.agent import AgentRunner

    runner = AgentRunner(config)
    result = asyncio.run(runner.run(task))
    print(result)


def _run_worker(config):
    """Start Pub/Sub background worker."""
    from agent_runner.worker.pubsub import run_worker

    asyncio.run(run_worker(config))


if __name__ == "__main__":
    main()
