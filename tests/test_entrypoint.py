"""Tests for entrypoint.sh behaviour."""


def test_starts_server(run_entrypoint):
    result = run_entrypoint()

    assert result.returncode == 0
    assert result.server_started


def test_prompt_file_is_copied_to_agents_dir(run_entrypoint):
    result = run_entrypoint(
        env={"AGENT_NAME": "myagent"},
        prompt_content="You are a helpful assistant.",
    )

    assert result.returncode == 0
    agent_file = result.home / ".claude" / "agents" / "myagent.md"
    assert agent_file.exists()
    assert "helpful assistant" in agent_file.read_text()


def test_default_agent_name_is_agent(run_entrypoint):
    result = run_entrypoint(prompt_content="system prompt")

    assert result.returncode == 0
    assert (result.home / ".claude" / "agents" / "agent.md").exists()


def test_no_prompt_file_skips_copy(run_entrypoint):
    result = run_entrypoint()

    assert result.returncode == 0
    agents_dir = result.home / ".claude" / "agents"
    assert not agents_dir.exists() or list(agents_dir.iterdir()) == []


# --- YAML agent config ---

def test_yaml_config_sets_agent_name(run_entrypoint):
    result = run_entrypoint(agent_config_content="name: myagent\n")

    assert result.returncode == 0
    assert result.server_started


def test_yaml_config_system_prompt_written(run_entrypoint):
    yaml = "name: myagent\nsystem_prompt: |\n  You are a helpful assistant.\n"
    result = run_entrypoint(agent_config_content=yaml)

    assert result.returncode == 0
    agent_file = result.home / ".claude" / "agents" / "myagent.md"
    assert agent_file.exists()
    assert "helpful assistant" in agent_file.read_text()


def test_yaml_config_absent_is_noop(run_entrypoint):
    result = run_entrypoint()

    assert result.returncode == 0
    assert result.server_started
