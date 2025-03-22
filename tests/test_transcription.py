"""
Tests for the transcription module that handles audio transcription and diarization.
"""

import os
import pytest
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow importing from root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcription import (
    transcribe_and_diarize,
    TranscriptionError,
    DiarizationError,
)


# Test audio file paths
WARNING_MP3 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "warning.mp3")
SIMPLE_DUET_MP3 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simple_duet.mp3")


@pytest.fixture
def mock_diarization_segments():
    """Mock diarization segments."""
    return [
        {"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"},
        {"start": 3.0, "end": 5.5, "speaker": "SPEAKER_01"},
        {"start": 6.0, "end": 8.5, "speaker": "SPEAKER_00"},
    ]


class TestTranscriptionWithMocks:
    """Tests for transcription module using mocks."""
    
    @patch("transcription.transcribe_audio")
    def test_transcribe_audio_internal(self, mock_transcribe):
        """Test transcribing audio file."""
        # Configure the mock
        mock_transcribe.return_value = "This is a test transcription."
        
        # Call the higher-level function which uses transcribe_audio
        with patch("transcription.diarize_audio") as mock_diarize:
            with patch("transcription.align_transcript_with_diarization") as mock_align:
                # Configure the mocks
                mock_diarize.return_value = [{"start": 0, "end": 1, "speaker": "Speaker 1"}]
                mock_align.return_value = "Speaker 1: This is a test transcription."
                
                # Call function
                result = transcribe_and_diarize(WARNING_MP3)
                
                # Verify mocks were called
                mock_transcribe.assert_called_once_with(WARNING_MP3)
                mock_diarize.assert_called_once()
                mock_align.assert_called_once()
                
                # Verify result
                assert "Speaker 1" in result
                assert "transcription" in result
        
    @patch("transcription.load_diarization_pipeline")
    def test_diarize_audio(self, mock_load_pipeline):
        """Test diarizing audio file."""
        # Configure the mock pipeline
        mock_pipeline = MagicMock()
        mock_diarization = MagicMock()
        
        # Set up the mock behavior for itertracks
        segments = [
            (MagicMock(start=0.0, end=2.5), 0, "SPEAKER_00"),
            (MagicMock(start=3.0, end=5.5), 1, "SPEAKER_01"),
            (MagicMock(start=6.0, end=8.5), 2, "SPEAKER_00"),
        ]
        mock_diarization.itertracks.return_value = segments
        mock_pipeline.return_value = mock_diarization
        mock_load_pipeline.return_value = mock_pipeline
        
        # Set up speaker names
        speaker_names = ["Alice", "Bob"]
        
        # Import here to avoid importing at module level which causes API key issues
        from transcription import diarize_audio
        
        # Set environment variable for HF token
        os.environ["HF_TOKEN"] = "test_token"
        
        # Call the function
        result = diarize_audio(WARNING_MP3, speaker_names)
        
        # Verify the result
        assert len(result) == 3
        assert result[0]["speaker"] == "Alice"
        assert result[1]["speaker"] == "Bob"
        assert result[2]["speaker"] == "Alice"
        
    @patch("transcription.transcribe_audio")
    @patch("transcription.diarize_audio")
    @patch("transcription.align_transcript_with_diarization")
    def test_transcribe_and_diarize(
        self, mock_align, mock_diarize, mock_transcribe, mock_diarization_segments
    ):
        """Test the complete transcribe and diarize process."""
        # Configure the mocks
        mock_transcribe.return_value = "This is a test transcription."
        mock_diarize.return_value = mock_diarization_segments
        mock_align.return_value = "Alice: This is a test.\nBob: Yes, it is."
        
        # Call the function
        result = transcribe_and_diarize(WARNING_MP3, ["Alice", "Bob"])
        
        # Verify the result
        assert result == "Alice: This is a test.\nBob: Yes, it is."
        mock_transcribe.assert_called_once_with(WARNING_MP3)
        mock_diarize.assert_called_once_with(WARNING_MP3, ["Alice", "Bob"])
        mock_align.assert_called_once_with(
            "This is a test transcription.", mock_diarization_segments
        )


@pytest.mark.integration
@pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ or "HF_TOKEN" not in os.environ,
    reason="API keys not available for integration test"
)
class TestTranscriptionIntegration:
    """Integration tests for transcription module using real API calls."""
    
    def test_warning_mp3_transcription(self):
        """Test transcribing the warning.mp3 file."""
        # This is a short test to verify our module works with real audio
        transcript = transcribe_and_diarize(WARNING_MP3)
        
        # Check that we got some output
        assert transcript is not None
        assert len(transcript) > 0
        
        # The warning.mp3 file should contain words like "warning" or "alert"
        lower_transcript = transcript.lower()
        assert any(word in lower_transcript for word in ["warning", "alert", "caution"])
    
    def test_simple_duet_with_speaker_names(self):
        """Test transcribing the simple_duet.mp3 file with speaker names."""
        # This tests a dialogue with speaker names
        transcript = transcribe_and_diarize(
            SIMPLE_DUET_MP3, speaker_names=["Singer 1", "Singer 2"]
        )
        
        # Check that we got some output
        assert transcript is not None
        assert len(transcript) > 0
        
        # Check that our speaker names were used
        assert "Singer 1" in transcript
        assert "Singer 2" in transcript


@patch("transcription.transcribe_audio")
@patch("transcription.diarize_audio")
def test_error_handling(mock_diarize, mock_transcribe):
    """Test error handling in the transcription module."""
    # Test transcription error
    mock_transcribe.side_effect = TranscriptionError("Transcription failed")
    with pytest.raises(TranscriptionError):
        transcribe_and_diarize(WARNING_MP3)
    
    # Test diarization error
    mock_transcribe.side_effect = None  # Reset the side effect
    mock_transcribe.return_value = "Test transcript"
    mock_diarize.side_effect = DiarizationError("Diarization failed")
    
    with pytest.raises(DiarizationError):
        transcribe_and_diarize(WARNING_MP3, [""])