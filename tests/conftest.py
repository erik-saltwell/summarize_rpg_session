"""Test configuration for the summarize_rpg_session tests."""

import os
import pytest
import tempfile
from unittest.mock import MagicMock
from typing import List, Dict, Any, Iterator


@pytest.fixture
def temp_file() -> Iterator[str]:
    """Create a temporary file for testing."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def temp_dir() -> Iterator[str]:
    """Create a temporary directory for testing."""
    path = tempfile.mkdtemp()
    yield path
    os.rmdir(path)


@pytest.fixture
def mock_transcript_content() -> str:
    """Sample transcript content for testing."""
    return """
    This is a sample transcript of an RPG session.
    GM: Welcome to today's session. Last time, you were exploring the ancient ruins.
    Player 1: I'd like to check if there are any hidden doors or passages.
    Player 2: While they're doing that, I'll keep watch for any monsters.
    GM: Player 1, roll a perception check.
    Player 1: I got a 15.
    GM: You notice a small crack in the wall that seems out of place.
    """


@pytest.fixture
def mock_diarized_transcript() -> str:
    """Sample diarized transcript for testing."""
    return """
    GM: Welcome to today's session. Last time, you were exploring the ancient ruins.
    Player 1: I'd like to check if there are any hidden doors or passages.
    Player 2: While they're doing that, I'll keep watch for any monsters.
    GM: Player 1, roll a perception check.
    Player 1: I got a 15.
    GM: You notice a small crack in the wall that seems out of place.
    """


@pytest.fixture
def mock_openai_audio_response() -> MagicMock:
    """Create a mock OpenAI API response for audio transcription."""
    response = MagicMock()
    response.text = "This is a mock transcription of an audio file."
    return response


@pytest.fixture
def mock_diarization_segments() -> List[Dict[str, Any]]:
    """Create mock diarization segments."""
    return [
        {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_01"},
        {"start": 5.5, "end": 10.0, "speaker": "SPEAKER_02"}, 
        {"start": 10.5, "end": 15.0, "speaker": "SPEAKER_01"},
        {"start": 15.5, "end": 20.0, "speaker": "SPEAKER_03"},
        {"start": 20.5, "end": 25.0, "speaker": "SPEAKER_01"},
    ]
