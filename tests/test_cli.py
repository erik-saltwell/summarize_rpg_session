"""Tests for the CLI argument parsing in summarize_rpg_session."""

import os
from typer.testing import CliRunner
from unittest.mock import patch
import sys
from summarize_rpg_session import app, validate_input_paths

# Add parent directory to path to import the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Set up the test runner
runner = CliRunner()


class TestCommandLineParser:
    """Tests for the command line argument parser."""

    def test_help_option(self):
        """Test that the help option works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "--audio" in result.stdout
        assert "--transcript" in result.stdout
        assert "--output" in result.stdout

    def test_missing_required_output(self):
        """Test that the app fails when output is not provided."""
        result = runner.invoke(app, ["--audio", "test.mp3"])
        assert result.exit_code != 0
        assert "Error" in result.stdout

    def test_no_input_source(self):
        """Test that the app fails when neither audio nor transcript is provided."""
        with patch("os.environ", {"OPENAI_API_KEY": "test_key"}):
            with patch("os.path.exists", return_value=True):
                with patch("os.access", return_value=True):
                    result = runner.invoke(app, ["--output", "test.md"])
                    assert result.exit_code != 0
                    assert "You must provide either an audio file OR a transcript file" in result.stdout

    def test_both_input_sources_error(self):
        """Test that the app fails when both audio and transcript are provided."""
        result = runner.invoke(app, ["--audio", "test.mp3", "--transcript", "test.txt", "--output", "test.md"])
        assert result.exit_code != 0
        assert "You cannot specify both --audio and --transcript" in result.stdout

    def test_nonexistent_audio_file(self):
        """Test that the app fails when the audio file doesn't exist."""
        with patch("os.environ", {"OPENAI_API_KEY": "test_key"}):
            with patch("os.path.exists", side_effect=lambda path: False if path == "nonexistent.mp3" else True):
                with patch("os.access", return_value=True):
                    result = runner.invoke(app, ["--audio", "nonexistent.mp3", "--output", "test.md"])
                    assert result.exit_code != 0
                    assert "Audio file not found" in result.stdout

    def test_nonexistent_transcript_file(self):
        """Test that the app fails when the transcript file doesn't exist."""
        with patch("os.environ", {"OPENAI_API_KEY": "test_key"}):
            with patch("os.path.exists", side_effect=lambda path: False if path == "nonexistent.txt" else True):
                with patch("os.access", return_value=True):
                    result = runner.invoke(app, ["--transcript", "nonexistent.txt", "--output", "test.md"])
                    assert result.exit_code != 0
                    assert "Transcript file not found" in result.stdout

    def test_nonwritable_output_directory(self):
        """Test that the app fails when the output directory is not writable."""
        with patch("os.environ", {"OPENAI_API_KEY": "test_key"}):
            with patch("os.path.exists", return_value=True):
                with patch("os.access", return_value=False):
                    result = runner.invoke(app, ["--audio", "test.mp3", "--output", "/nonwritable/test.md"])
                    assert result.exit_code != 0
                    assert "not writable" in result.stdout

    def test_missing_api_key(self):
        """Test that the app fails when the API key is missing."""
        with patch("os.environ", {}):
            result = runner.invoke(app, ["--audio", "test.mp3", "--output", "test.md"])
            assert result.exit_code != 0
            assert "OPENAI_API_KEY environment variable not found" in result.stdout

    def test_audio_path_successful_validation(self):
        """Test successful validation with audio path."""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=True):
                assert validate_input_paths("output.md", "input.mp3", None, None) is True

    def test_transcript_path_successful_validation(self):
        """Test successful validation with transcript path."""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=True):
                assert validate_input_paths("output.md", None, "input.txt", None) is True

    def test_speaker_names_option(self):
        """Test that speaker names are accepted."""
        with patch("os.environ", {"OPENAI_API_KEY": "test_key"}):
            with patch("os.path.exists", return_value=True):
                with patch("os.access", return_value=True):
                    # We'll use a subprocess to run the command and capture its output
                    # This is because typer.testing.CliRunner doesn't handle list parameters well
                    with patch("sys.exit"):
                        with patch("rich.console.Console.print") as mock_print:
                            from summarize_rpg_session import main

                            main(audio="test.mp3", transcript=None, summary_output="test.md", transcript_output=None, speaker_names=["Alice", "Bob", "DM"])
                            # Check that the right message was printed
                            mock_print.assert_any_call("Using provided speaker names: Alice, Bob, DM")
