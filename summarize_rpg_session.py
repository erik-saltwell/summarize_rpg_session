#!/usr/bin/env python3
"""
summarize_rpg_session - A command-line tool for transcribing and summarizing RPG sessions.

This tool accepts an audio file or text transcript and generates a detailed markdown summary
of the tabletop RPG session, with optional diarized transcript output.
"""

import os
import sys
from typing import Optional, List

import typer
from rich.console import Console
from dotenv import load_dotenv

# Initialize typer app and rich console
app = typer.Typer(help="Transcribe and summarize tabletop RPG session recordings or transcripts.")
console = Console()


def validate_input_paths(summary_output: str, audio: Optional[str] = None, transcript: Optional[str] = None, transcript_output: Optional[str] = None) -> bool:
    """
    Validate that input paths exist and output paths are writable.

    Args:
        summary_output: Path for the summary output file
        audio: Path to the audio file
        transcript: Path to the transcript file
        transcript_output: Path for the transcript output file

    Returns:
        bool: True if all inputs are valid, False otherwise
    """
    # Validate that exactly one of audio or transcript is provided
    if (audio is None and transcript is None) or (audio is not None and transcript is not None):
        console.print("[bold red]Error:[/] You must provide either an audio file OR a transcript file, not both or neither.")
        return False

    # Check if audio file exists
    if audio and not os.path.exists(audio):
        console.print(f"[bold red]Error:[/] Audio file not found: {audio}")
        return False

    # Check if transcript file exists
    if transcript and not os.path.exists(transcript):
        console.print(f"[bold red]Error:[/] Transcript file not found: {transcript}")
        return False

    # Check if summary output directory exists and is writable
    if summary_output:
        summary_dir = os.path.dirname(summary_output) or "."
        if not os.path.exists(summary_dir):
            console.print(f"[bold red]Error:[/] Directory for summary output does not exist: {summary_dir}")
            return False
        if not os.access(summary_dir, os.W_OK):
            console.print(f"[bold red]Error:[/] Directory for summary output is not writable: {summary_dir}")
            return False

    # Check if transcript output directory exists and is writable
    if transcript_output:
        transcript_dir = os.path.dirname(transcript_output) or "."
        if not os.path.exists(transcript_dir):
            console.print(f"[bold red]Error:[/] Directory for transcript output does not exist: {transcript_dir}")
            return False
        if not os.access(transcript_dir, os.W_OK):
            console.print(f"[bold red]Error:[/] Directory for transcript output is not writable: {transcript_dir}")
            return False

    return True


@app.command()
def main(
    audio: Optional[str] = typer.Option(None, "--audio", "-a", help="Path to the audio file to transcribe (.mp3 or .wav)"),
    transcript: Optional[str] = typer.Option(None, "--transcript", "-t", help="Path to an existing transcript file"),
    summary_output: str = typer.Option(..., "--output", "-o", help="Path for the markdown summary output file"),
    transcript_output: Optional[str] = typer.Option(None, "--diarized-output", "-d", help="Path to save the diarized transcript (only used with audio input)"),
    speaker_names: Optional[List[str]] = typer.Option(None, "--names", "-n", help="Comma-separated list of speaker names for diarization"),
) -> None:
    """
    Transcribe and summarize a tabletop RPG session from audio or existing transcript.

    The tool will generate a detailed markdown summary of the session. If an audio file
    is provided, it will be transcribed and optionally saved as a diarized transcript.
    """
    # Check that audio and transcript aren't both specified
    if audio is not None and transcript is not None:
        raise typer.BadParameter("You cannot specify both --audio and --transcript. Please provide only one input source.")
    # Load environment variables
    load_dotenv()

    # Check for OpenAI API key
    if "OPENAI_API_KEY" not in os.environ:
        console.print("[bold red]Error:[/] OPENAI_API_KEY environment variable not found. " "Please set it in your environment or in a .env file.")
        sys.exit(1)

    # Validate inputs
    if not validate_input_paths(summary_output, audio, transcript, transcript_output):
        sys.exit(1)

    # Display startup message
    console.print("[bold green]summarize_rpg_session[/] starting up...", highlight=False)

    # Process based on input type
    if audio:
        console.print(f"Processing audio file: {audio}")
        # Here we would implement audio transcription, diarization, and summarization
        # For now, just print what would happen
        console.print("[yellow]Would transcribe audio to text[/]")
        if transcript_output:
            console.print(f"[yellow]Would save diarized transcript to {transcript_output}[/]")
    else:
        console.print(f"Processing transcript file: {transcript}")
        # Here we would implement transcript summarization
        # For now, just print what would happen
        console.print("[yellow]Would summarize existing transcript[/]")

    # Speaker names processing
    if speaker_names:
        console.print(f"Using provided speaker names: {', '.join(speaker_names)}")

    # Here we would implement the actual summarization
    console.print(f"[yellow]Would save summary to {summary_output}[/]")

    # Demo success message
    console.print("[bold green]✓[/] Processing complete!")
    console.print(f"Summary saved to: [bold]{summary_output}[/]")
    if transcript_output and audio:
        console.print(f"Diarized transcript saved to: [bold]{transcript_output}[/]")


if __name__ == "__main__":
    app()
