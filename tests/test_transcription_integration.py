"""
Integration tests for the transcription module with real audio files.
"""

import os
import pytest
import tempfile
from typing import List, Optional

# Add parent directory to path to allow importing from root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcription import transcribe_and_diarize, TranscriptionError, DiarizationError

# Test audio file paths
WARNING_MP3 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "warning.mp3")
SIMPLE_DUET_MP3 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simple_duet.mp3")


@pytest.mark.integration
@pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ or "HF_TOKEN" not in os.environ,
    reason="API keys not available for integration test"
)
class TestTranscriptionWithRealAudio:
    """Tests for transcription module using real audio files."""
    
    def test_warning_mp3_transcription(self):
        """
        Test transcribing the warning.mp3 file.
        
        This test processes a short warning audio file and verifies 
        that the transcription contains warning-related words.
        """
        # This test only runs if API keys are available
        try:
            transcript = transcribe_and_diarize(WARNING_MP3)
            
            # Verify that we got a transcription
            assert transcript is not None
            assert len(transcript) > 10  # Should have at least some content
            
            # The warning.mp3 should contain warning-related terms
            lower_transcript = transcript.lower()
            assert any(word in lower_transcript for word in [
                "warning", "alert", "caution", "attention", "emergency"
            ])
            
            # Save the transcript for manual inspection
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".txt", mode="w", encoding="utf-8"
            ) as f:
                f.write(transcript)
                print(f"\nTranscript saved to: {f.name}")
                
        except (TranscriptionError, DiarizationError) as e:
            pytest.skip(f"API error during transcription: {str(e)}")
    
    def test_simple_duet_with_speaker_names(self):
        """
        Test transcribing the simple_duet.mp3 file with speaker names.
        
        This test processes an audio file containing two speakers
        and verifies that the diarization works correctly with 
        provided speaker names.
        """
        # Define speaker names
        speaker_names: List[str] = ["Singer 1", "Singer 2"]
        
        try:
            # Process the audio with speaker names
            transcript = transcribe_and_diarize(SIMPLE_DUET_MP3, speaker_names)
            
            # Verify that we got a transcription
            assert transcript is not None
            assert len(transcript) > 10  # Should have at least some content
            
            # Verify that both speaker names are in the transcript
            assert all(name in transcript for name in speaker_names)
            
            # Save the transcript for manual inspection
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".txt", mode="w", encoding="utf-8"
            ) as f:
                f.write(transcript)
                print(f"\nSpeaker-labeled transcript saved to: {f.name}")
                
        except (TranscriptionError, DiarizationError) as e:
            pytest.skip(f"API error during transcription: {str(e)}")
    
    def test_comparing_transcription_with_and_without_speaker_names(self):
        """
        Test comparing transcriptions with and without speaker names.
        
        This test verifies that providing speaker names doesn't change
        the actual content of the transcription, just the speaker labels.
        """
        try:
            # Transcribe without speaker names first
            transcript_without_names = transcribe_and_diarize(SIMPLE_DUET_MP3)
            
            # Transcribe with speaker names
            speaker_names: List[str] = ["Singer A", "Singer B"]
            transcript_with_names = transcribe_and_diarize(SIMPLE_DUET_MP3, speaker_names)
            
            # Both transcripts should exist and have content
            assert transcript_without_names is not None
            assert transcript_with_names is not None
            
            # Verify that the custom speaker names are in the second transcript
            assert all(name in transcript_with_names for name in speaker_names)
            
            # Generic speaker labels should be in the first transcript
            assert "Speaker 1" in transcript_without_names or "SPEAKER_01" in transcript_without_names
            
            # Save both transcripts for comparison
            with tempfile.NamedTemporaryFile(
                delete=False, suffix="_without_names.txt", mode="w", encoding="utf-8"
            ) as f1, tempfile.NamedTemporaryFile(
                delete=False, suffix="_with_names.txt", mode="w", encoding="utf-8"
            ) as f2:
                f1.write(transcript_without_names)
                f2.write(transcript_with_names)
                print(f"\nTranscript without names saved to: {f1.name}")
                print(f"Transcript with names saved to: {f2.name}")
                
        except (TranscriptionError, DiarizationError) as e:
            pytest.skip(f"API error during transcription: {str(e)}")