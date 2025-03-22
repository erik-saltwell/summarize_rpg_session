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
from rich.progress import Progress
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
    transcript_content = None
    
    if audio:
        console.print(f"Processing audio file: {audio}")
        
        try:
            # Import the transcription module here to avoid circular imports
            from transcription import transcribe_and_diarize, TranscriptionError, DiarizationError
            
            # Convert speaker_names from None or List[str] to List[str] or None
            speaker_name_list = speaker_names if speaker_names else None
            
            # Perform transcription and diarization with progress feedback
            with console.status("[bold blue]Transcribing audio...", spinner="dots") as status:
                console.print("[bold]Starting transcription and diarization process[/]")
                try:
                    transcript_content = transcribe_and_diarize(audio, speaker_name_list)
                    console.print("[bold green]✓[/] Transcription and diarization complete!")
                except TranscriptionError as e:
                    console.print(f"[bold red]Transcription error:[/] {str(e)}")
                    raise
                except DiarizationError as e:
                    console.print(f"[bold red]Diarization error:[/] {str(e)}")
                    raise
            
            # Save the diarized transcript if requested
            if transcript_output:
                with open(transcript_output, "w", encoding="utf-8") as f:
                    f.write(transcript_content)
                console.print(f"Diarized transcript saved to: [bold]{transcript_output}[/]")
            
        except (TranscriptionError, DiarizationError) as e:
            console.print(f"[bold red]Error during transcription/diarization:[/] {str(e)}")
            sys.exit(1)
            
    else:
        console.print(f"Processing transcript file: {transcript}")
        
        # Read the provided transcript file
        try:
            with open(transcript, "r", encoding="utf-8") as f:
                transcript_content = f.read()
            console.print(f"Loaded transcript from: [bold]{transcript}[/]")
        except Exception as e:
            console.print(f"[bold red]Error reading transcript file:[/] {str(e)}")
            sys.exit(1)

    # Speaker names processing
    if speaker_names:
        console.print(f"Using provided speaker names: {', '.join(speaker_names)}")

    # TODO: Implement summarization in a separate module
    # For now, just save a placeholder summary
    try:
        # Create a simple placeholder summary with the first few lines
        summary_text = f"""# RPG Session Summary

This is a placeholder summary. The full summarization functionality will be implemented in a future update.

## Session Overview

The session transcript contains approximately {len(transcript_content.split())} words.

## Notable Moments

First few lines of the transcript:

```
{transcript_content[:500] + "..." if len(transcript_content) > 500 else transcript_content}
```
"""
        
        # Write the summary to the output file
        with open(summary_output, "w", encoding="utf-8") as f:
            f.write(summary_text)
        
        # Success message
        console.print("[bold green]✓[/] Processing complete!")
        console.print(f"Summary saved to: [bold]{summary_output}[/]")
        
    except Exception as e:
        console.print(f"[bold red]Error writing summary:[/] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    app()
