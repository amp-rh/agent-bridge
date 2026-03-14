import pytest

from agent_bridge.presentation.cli import main


class TestCliConfigCheck:
    def test_config_check_defaults(self, capsys):
        main(["config-check"])
        output = capsys.readouterr().out
        assert "name:        agent" in output
        assert "timeout:     300" in output

    def test_config_check_with_yaml(self, tmp_path, capsys):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("name: myagent\ntimeout: 60\n")
        main(["config-check", "--config", str(config_file)])
        output = capsys.readouterr().out
        assert "name:        myagent" in output
        assert "timeout:     60" in output
