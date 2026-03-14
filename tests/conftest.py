import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

ENTRYPOINT = Path(__file__).parent.parent / "entrypoint.sh"
AGENT_CONFIG_SCRIPT = Path(__file__).parent.parent / "agent_config.py"
PYTHON_BIN_DIR = Path(sys.executable).parent


@pytest.fixture
def fake_claude(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "invocations.log"
    script = bin_dir / "claude"
    script.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> {log}\n')
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return SimpleNamespace(bin_dir=bin_dir, log=log)


@pytest.fixture
def fake_server(tmp_path):
    server_script = tmp_path / "server.py"
    log = tmp_path / "server.log"
    server_script.write_text(f'#!/usr/bin/env python3\nwith open("{log}", "w") as f: f.write("started\\n")\n')
    server_script.chmod(server_script.stat().st_mode | stat.S_IEXEC)
    return SimpleNamespace(script=server_script, log=log)


@pytest.fixture
def run_entrypoint(tmp_path, fake_claude, fake_server):
    home = tmp_path / "home"
    home.mkdir()

    def _run(env=None, prompt_content=None, mcp_config_content=None, agent_config_content=None):
        base_env = {
            "HOME": str(home),
            "PATH": f"{fake_claude.bin_dir}:{PYTHON_BIN_DIR}:/usr/bin:/bin",
            "AGENT_NAME": "agent",
            "AGENT_CONFIG_SCRIPT": str(AGENT_CONFIG_SCRIPT),
        }

        entrypoint = str(ENTRYPOINT)

        # Patch entrypoint to use fake server.py instead of real one
        patched = tmp_path / "entrypoint_patched.sh"
        original = ENTRYPOINT.read_text()
        patched.write_text(original.replace(
            "exec python3.11 /usr/local/bin/server.py",
            f"exec python3 {fake_server.script}",
        ))
        patched.chmod(patched.stat().st_mode | stat.S_IEXEC)
        entrypoint = str(patched)

        if prompt_content is not None:
            prompt_file = tmp_path / "system_prompt.md"
            prompt_file.write_text(prompt_content)
            base_env["AGENT_PROMPT_FILE"] = str(prompt_file)

        if mcp_config_content is not None:
            mcp_file = tmp_path / "mcp_config.json"
            mcp_file.write_text(mcp_config_content)
            base_env["MCP_CONFIG_FILE"] = str(mcp_file)

        if agent_config_content is not None:
            config_file = tmp_path / "config.yaml"
            config_file.write_text(agent_config_content)
            base_env["AGENT_CONFIG_FILE"] = str(config_file)

        if env:
            base_env.update(env)

        result = subprocess.run(
            ["sh", entrypoint],
            env=base_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        return SimpleNamespace(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            home=home,
            server_started=fake_server.log.exists(),
        )

    return _run
