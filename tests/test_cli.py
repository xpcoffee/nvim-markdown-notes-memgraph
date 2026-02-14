"""Tests for CLI commands."""

import json
from click.testing import CliRunner
from nvim_markdown_notes_memgraph.cli import main


class TestCLIHelp:
    """Test CLI help output."""

    def test_main_help(self):
        """Test that main --help works."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])

        assert result.exit_code == 0
        assert 'nvim-markdown-notes-memgraph CLI' in result.output
        assert 'Manage Memgraph and MCP server' in result.output
        assert '--notes-root' in result.output

    def test_start_help(self):
        """Test that start --help works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)
            result = runner.invoke(main, ['--notes-root', notes_dir, 'start', '--help'])

            assert result.exit_code == 0
            assert 'Start Docker Compose services' in result.output

    def test_stop_help(self):
        """Test that stop --help works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)
            result = runner.invoke(main, ['--notes-root', notes_dir, 'stop', '--help'])

            assert result.exit_code == 0
            assert 'Stop Docker Compose services' in result.output

    def test_status_help(self):
        """Test that status --help works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)
            result = runner.invoke(main, ['--notes-root', notes_dir, 'status', '--help'])

            assert result.exit_code == 0
            assert 'Show status of Docker Compose services' in result.output

    def test_config_help(self):
        """Test that config --help works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)
            result = runner.invoke(main, ['--notes-root', notes_dir, 'config', '--help'])

            assert result.exit_code == 0
            assert 'Output MCP JSON configuration' in result.output
            assert '--memgraph-host' in result.output
            assert '--memgraph-port' in result.output

    def test_serve_help(self):
        """Test that serve --help works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)
            result = runner.invoke(main, ['--notes-root', notes_dir, 'serve', '--help'])

            assert result.exit_code == 0
            assert 'Run the MCP server directly' in result.output

    def test_bridge_help(self):
        """Test that bridge --help works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)
            result = runner.invoke(main, ['--notes-root', notes_dir, 'bridge', '--help'])

            assert result.exit_code == 0
            assert 'Run the Neovim bridge' in result.output


class TestConfigCommand:
    """Test config command output."""

    def test_config_output_valid_json(self):
        """Test that config outputs valid JSON."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a temporary notes directory
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)

            result = runner.invoke(main, ['--notes-root', notes_dir, 'config'])

            # Should exit successfully
            assert result.exit_code == 0

            # Should output valid JSON
            try:
                config = json.loads(result.output)
            except json.JSONDecodeError:
                assert False, f"Output is not valid JSON: {result.output}"

            # Should be a dict
            assert isinstance(config, dict)

    def test_config_has_expected_keys(self):
        """Test that config output has expected keys."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a temporary notes directory
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)

            result = runner.invoke(main, ['--notes-root', notes_dir, 'config'])

            assert result.exit_code == 0

            config = json.loads(result.output)

            # Check for expected top-level keys
            assert 'mcpServers' in config
            assert isinstance(config['mcpServers'], dict)

            # Check for nvim-markdown-notes-memgraph server entry
            assert 'nvim-markdown-notes-memgraph' in config['mcpServers']

            server_config = config['mcpServers']['nvim-markdown-notes-memgraph']

            # Check for expected server configuration keys
            assert 'command' in server_config
            assert 'args' in server_config
            assert 'env' in server_config

            # Verify command is correct
            assert server_config['command'] == 'nvim-markdown-notes-memgraph'

            # Verify args include serve
            assert 'serve' in server_config['args']

            # Verify environment variables are present
            assert 'NOTES_ROOT' in server_config['env']
            assert 'MEMGRAPH_HOST' in server_config['env']
            assert 'MEMGRAPH_PORT' in server_config['env']

    def test_config_custom_memgraph_host_port(self):
        """Test config with custom Memgraph host and port."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a temporary notes directory
            import os
            notes_dir = os.path.join(os.getcwd(), 'notes')
            os.makedirs(notes_dir, exist_ok=True)

            result = runner.invoke(main, [
                '--notes-root', notes_dir,
                'config',
                '--memgraph-host', 'custom-host',
                '--memgraph-port', '9999'
            ])

            assert result.exit_code == 0

            config = json.loads(result.output)
            server_config = config['mcpServers']['nvim-markdown-notes-memgraph']

            # Verify custom host and port are set
            assert server_config['env']['MEMGRAPH_HOST'] == 'custom-host'
            assert server_config['env']['MEMGRAPH_PORT'] == '9999'

    def test_config_notes_root_in_env(self):
        """Test that notes root is properly included in config."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a temporary notes directory
            import os
            notes_dir = os.path.join(os.getcwd(), 'my-notes')
            os.makedirs(notes_dir, exist_ok=True)

            result = runner.invoke(main, ['--notes-root', notes_dir, 'config'])

            assert result.exit_code == 0

            config = json.loads(result.output)
            server_config = config['mcpServers']['nvim-markdown-notes-memgraph']

            # Verify notes root is set correctly
            assert notes_dir in server_config['env']['NOTES_ROOT']
