#!/usr/bin/env python3
"""
Transcription and diarization module for summarize_rpg_session.

This module handles audio transcription using OpenAI's gpt-4o-transcribe model
and speaker diarization using pyannote.audio.
"""

import os
import sys
import time
import argparse
from typing import Dict, List, Optional, Any

import openai
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.audio import TranscriptionVerbose

# pyannote.audio doesn't have type hints, so we use type: ignore
from pyannote.audio import Pipeline  # type: ignore

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2
OPENAI_TRANSCRIPTION_MODEL = "gpt-4o-transcribe"


class TranscriptionError(Exception):
    """Exception raised for errors during transcription."""

    pass


class DiarizationError(Exception):
    """Exception raised for errors during diarization."""

    pass


def load_diarization_pipeline() -> Pipeline:
    """
    Load the pyannote.audio diarization pipeline.

    Returns:
        Pipeline: The diarization pipeline

    Raises:
        DiarizationError: If the pipeline cannot be loaded
    """
    try:
        # Check for HF_TOKEN environment variable
        if "HF_TOKEN" not in os.environ:
            raise DiarizationError("HF_TOKEN environment variable not found. " "Please set it to your Hugging Face token to use pyannote.audio.")

        # Load the diarization pipeline from huggingface
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=os.environ["HF_TOKEN"])
        return pipeline
    except Exception as e:
        raise DiarizationError(f"Failed to load diarization pipeline: {str(e)}")


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio using OpenAI's gpt-4o-transcribe model.

    Args:
        audio_path: Path to the audio file

    Returns:
        str: The transcribed text

    Raises:
        TranscriptionError: If transcription fails
    """
    retries = 0
    last_error = None

    while retries < MAX_RETRIES:
        try:
            with open(audio_path, "rb") as audio_file:
                transcript: TranscriptionVerbose = openai.audio.transcriptions.create(
                    model=OPENAI_TRANSCRIPTION_MODEL,
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            if transcript.text is None:
                raise TranscriptionError("Transcription returned None text")

            return transcript.text

        except openai.RateLimitError:
            # For rate limit errors, wait and retry
            retries += 1
            wait_time = RETRY_DELAY * (2**retries)  # Exponential backoff
            time.sleep(wait_time)
            last_error = "Rate limit exceeded"

        except Exception as e:
            retries += 1
            time.sleep(RETRY_DELAY)
            last_error = str(e)

    # If we've exhausted retries, raise an exception
    raise TranscriptionError(f"Failed to transcribe audio after {MAX_RETRIES} attempts: {last_error}")


def diarize_audio(audio_path: str, speaker_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Perform speaker diarization on an audio file.

    Args:
        audio_path: Path to the audio file
        speaker_names: Optional list of speaker names to map to detected speakers

    Returns:
        List[Dict[str, Any]]: List of segments with speaker information

    Raises:
        DiarizationError: If diarization fails
    """
    try:
        # Load the diarization pipeline
        pipeline = load_diarization_pipeline()

        # Run diarization
        diarization = pipeline(audio_path)

        # Convert to list of segments
        segments: List[Dict[str, Any]] = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segment = {"start": turn.start, "end": turn.end, "speaker": speaker}
            segments.append(segment)

        # Map generic speaker labels to provided names if available
        if speaker_names:
            unique_speakers = sorted(list(set(s["speaker"] for s in segments)))
            name_mapping = {}

            # Map names to speakers (up to the number of available names)
            for i, speaker in enumerate(unique_speakers):
                if i < len(speaker_names):
                    name_mapping[speaker] = speaker_names[i]
                else:
                    # If we run out of names, use the original speaker label
                    name_mapping[speaker] = f"Speaker {i+1}"

            # Update segments with mapped names
            for segment in segments:
                segment["speaker"] = name_mapping[segment["speaker"]]
        else:
            # Use generic Speaker 1, Speaker 2, etc. if no names are provided
            unique_speakers = sorted(list(set(s["speaker"] for s in segments)))
            name_mapping = {speaker: f"Speaker {i+1}" for i, speaker in enumerate(unique_speakers)}

            for segment in segments:
                segment["speaker"] = name_mapping[segment["speaker"]]

        return segments

    except Exception as e:
        raise DiarizationError(f"Failed to diarize audio: {str(e)}")


def align_transcript_with_diarization(transcript: str, diarization_segments: List[Dict[str, Any]]) -> str:
    """
    Align transcript text with diarization segments to create a diarized transcript.

    Args:
        transcript: The transcribed text
        diarization_segments: List of segments with speaker information

    Returns:
        str: The diarized transcript with speaker labels
    """
    # For this implementation, we'll use a simple approach with OpenAI
    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": (
            "You are an expert at aligning transcripts with speaker diarization data. "
            "Your task is to take a raw transcript and speaker segments, then produce "
            "a clean, diarized transcript that correctly attributes dialogue to speakers."
        ),
    }

    user_message: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": (
            f"Here is the raw transcript:\n\n{transcript}\n\n"
            f"Here are the speaker segments with timestamps:\n\n{diarization_segments}\n\n"
            "Please create a diarized transcript in the format:\n"
            "Speaker Name: Their dialogue\n"
            "Another Speaker: Their response\n\n"
            "Make sure to maintain the chronological order and attribute each line to the correct speaker."
        ),
    }

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[system_message, user_message],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if content is None:
            # Fallback to a simple timestamp-based alignment if content is None
            return create_fallback_diarized_transcript(transcript, diarization_segments)
        return content

    except Exception:
        # Fallback to a simple timestamp-based alignment if the AI approach fails
        return create_fallback_diarized_transcript(transcript, diarization_segments)


def create_fallback_diarized_transcript(transcript: str, diarization_segments: List[Dict[str, Any]]) -> str:
    """
    Create a simple diarized transcript based on time segments as a fallback method.

    Args:
        transcript: The transcribed text
        diarization_segments: List of segments with speaker information

    Returns:
        str: A basic diarized transcript
    """
    # This is a very basic fallback that assumes the transcript has timestamps
    # It's not ideal but provides some level of speaker attribution
    lines = []
    current_speaker = None

    for segment in diarization_segments:
        speaker = segment["speaker"]
        start_time = segment["start"]
        # We don't use end_time, but we could enhance this in the future
        # end_time = segment["end"]

        # Format timestamp
        start_str = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"

        # If speaker changes, add a new line with speaker name
        if speaker != current_speaker:
            lines.append(f"\n[{start_str}] {speaker}:")
            current_speaker = speaker
        else:
            # If same speaker continues, just add the timestamp
            lines.append(f"\n[{start_str}] ")

    # Combine the lines
    diarized_text = "".join(lines)

    # Append a note about the fallback method
    diarized_text += "\n\n[Note: This is a simplified diarization using timestamps only. " "For a more accurate result, please retry the process.]"

    return diarized_text


def transcribe_and_diarize(audio_path: str, speaker_names: Optional[List[str]] = None) -> str:
    """
    Transcribe audio and perform speaker diarization.

    Args:
        audio_path: Path to the audio file
        speaker_names: Optional list of speaker names to map to detected speakers

    Returns:
        str: The diarized transcript with speaker annotations

    Raises:
        TranscriptionError: If transcription fails
        DiarizationError: If diarization fails
    """
    # Step 1: Transcribe the audio
    transcript = transcribe_audio(audio_path)

    # Step 2: Perform speaker diarization
    diarization_segments = diarize_audio(audio_path, speaker_names)

    # Step 3: Align transcript with diarization data
    diarized_transcript = align_transcript_with_diarization(transcript, diarization_segments)

    return diarized_transcript


if __name__ == "__main__":
    # This allows for testing the module directly
    parser = argparse.ArgumentParser(description="Transcribe and diarize an audio file")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--output", "-o", help="Path to save the diarized transcript")
    parser.add_argument("--names", "-n", nargs="+", help="Speaker names to use for diarization")

    args = parser.parse_args()

    try:
        print(f"Transcribing and diarizing {args.audio_path}...")
        diarized_transcript = transcribe_and_diarize(args.audio_path, args.names)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(diarized_transcript)
            print(f"Diarized transcript saved to: {args.output}")
        else:
            print(diarized_transcript)

    except (TranscriptionError, DiarizationError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
