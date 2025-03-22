Below is the updated engineering requirements document with an added section specifying the LLM models for transcription and summarization:

---

# Engineering Requirements Document for summarize_rpg_session

## Table of Contents
- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Packages and Dependencies](#packages-and-dependencies)
- [LLM Models for Transcription and Summarization](#llm-models-for-transcription-and-summarization)
- [Core Architecture and Design Patterns](#core-architecture-and-design-patterns)
- [File System Organization](#file-system-organization)
- [Development Practices](#development-practices)
- [Testing Strategy](#testing-strategy)
- [Secrets Management](#secrets-management)
- [Type Hints and Code Quality](#type-hints-and-code-quality)
- [Error Handling and API Rate Limits](#error-handling-and-api-rate-limits)

## Overview
**summarize_rpg_session** is a Unix-based command-line tool designed to transcribe and summarize tabletop roleplaying game (RPG) sessions. The application converts an audio file or an existing transcript into a detailed, diarized transcript (with speaker labels) and a comprehensive markdown summary using OpenAI’s LLM APIs. This document outlines the engineering requirements including architecture, package choices, testing strategies, and best practices.

## Technology Stack
- **Programming Language:** Python **3.11.11**
- **Command-Line Parsing:** [Typer](https://typer.tiangolo.com/)
- **Console Output and Progress Indicators:** [Rich](https://rich.readthedocs.io/)
- **LLM Access:** [OpenAI Python SDK](https://github.com/openai/openai-python)
- **Environment Variables:** [python-dotenv](https://pypi.org/project/python-dotenv/)
- **Testing Framework:** [pytest](https://docs.pytest.org/)
- **Environment & Dependency Management:**  
  - Use **uv** for environment management and dependency management.
  - Use a **virtual environment** to isolate project dependencies.
- **Dependency Management:** `uv` and configuration files (e.g., `pyproject.toml` or `requirements.txt` maintained by uv).

## Packages and Dependencies
The application will utilize the following key packages:
- **Typer:** For parsing command-line arguments and building the CLI interface.
- **Rich:** For enhanced console output, including progress bars, status messages, and logs.
- **OpenAI:** To interact with OpenAI's transcription (`gpt-4o-transcribe`) and summarization APIs.
- **python-dotenv:** To load sensitive information (e.g., API keys) from a `.env` file.
- **pytest:** For unit and integration testing.
- **uv:** For managing the Python virtual environment and project dependencies.
- **Other Utility Libraries:** Standard libraries (e.g., `logging`, `os`, `sys`, `typing`) for error handling and system operations.

## LLM Models for Transcription and Summarization
For this application, specific OpenAI models are designated for transcription and summarization:

- **Transcription:**  
  The application will use OpenAI's **`gpt-4o-transcribe`** model. This model is specifically designed for audio transcription and is deployed in the cloud. It supports input audio formats such as `.wav` and `.mp3` and returns an accurate textual transcript. The implementation will handle API rate limits through a retry mechanism with exponential backoff.

- **Summarization:**  
  For generating detailed session summaries, the application will utilize OpenAI's **`gpt-4`** model.  
  In cases where the transcript is very long and exceeds the context window, the application may consider using **`gpt-4-32k`** to accommodate a larger amount of text. The summarization prompt will instruct the model to produce a comprehensive Markdown summary that includes detailed descriptions of plot points, character actions, and key dialogue (including quotes for memorable lines).

## Core Architecture and Design Patterns

The application is structured into modular components. In addition to separation of concerns, the following design patterns are recommended:

### Core Design Patterns
- **Factory Pattern:**  
  Encapsulate the creation of service instances (e.g., transcription, diarization, summarization) based on configuration. This allows for easy swapping between different implementations.

- **Strategy Pattern:**  
  Enable interchangeable algorithms for tasks such as summarization and diarization, chosen at runtime based on configuration or user input.

- **Dependency Injection:**  
  Decouple module dependencies (like configuration, API clients, logging) by injecting them into components. This facilitates easier testing with mock implementations.

- **Facade Pattern:**  
  Provide a simplified interface to the subsystems (transcription, diarization, summarization) so that the main controller can operate without needing to understand the intricacies of each module.

- **Adapter Pattern:**  
  Translate external service responses (e.g., OpenAI API) into the internal format expected by the application modules.

### Updated Architecture Using These Patterns

1. **CLI Module (`cli.py`):**  
   - **Responsibility:** Parse command-line arguments using Typer and initialize the application.
   - **Design:** Uses Dependency Injection to pass configuration and service instances to the main controller.

2. **Main Application / Controller (`main.py`):**  
   - **Responsibility:** Orchestrate the workflow (transcription, diarization, summarization).
   - **Design:**  
     - Implements the **Facade Pattern** to provide a simplified interface for the entire process.
     - Receives service instances (via factories) through Dependency Injection.

3. **Service Factories and Strategies:**  
   - **Transcription Factory:**  
     - **Responsibility:** Create and return a transcription service instance (e.g., an OpenAI-based service).
     - **Design:** Uses the Factory Pattern to choose the appropriate strategy.
   - **Diarization Strategy:**  
     - **Responsibility:** Process raw transcripts to assign speaker labels.
     - **Design:** Uses the Strategy Pattern to switch between different diarization approaches.
   - **Summarization Factory/Strategy:**  
     - **Responsibility:** Provide a summarization service instance.
     - **Design:** Utilizes both Factory and Strategy patterns for different summarization methods (detailed vs. brief).

4. **Configuration Module (`config.py`):**  
   - **Responsibility:** Load settings and API keys from the `.env` file using python-dotenv.
   - **Design:** Implemented as a Singleton or module-level configuration that is shared across the application.

5. **Utility Module (`utils.py`):**  
   - **Responsibility:** Provide helper functions for file I/O, logging, and displaying progress (via Rich).
   - **Design:** May use the Adapter Pattern to standardize outputs from third-party libraries.

### Component Interaction Diagram (Textual Representation)
```
           +--------------+
           |    cli.py    | <----- User Input (Typer CLI)
           +------+-------+
                  |
                  v
       +----------+----------+
       |   Main Controller   | <-- Facade & Dependency Injection
       |      (main.py)      |
       +-----+-------+-------+
             |       |       
             v       v      
    +-------------------------+         +------------------------+
    | Transcription Service   | <----->   | Summarization Service  |
    | (Factory & Strategy)    |         | (Factory & Strategy)   |
    +-------------------------+         +------------------------+
             |
             v
    +-------------------------+
    | Diarization Service     | <-----> (Strategy Pattern for multiple methods)
    +-------------------------+
             |
             v
    +-------------------------+
    | Utility & Config Module | <-- Loads .env, displays progress with Rich
    +-------------------------+
```

## File System Organization
Below is the suggested directory structure for the project. The **README.md** file is included at the root and should contain installation instructions and usage documentation:

```
summarize_rpg_session/
├── README.md              # Contains installation and usage instructions
├── pyproject.toml         # Managed by uv for dependency management
├── .env.example           # Example file for environment variables
├── src/
│   ├── __init__.py
│   ├── main.py            # Entry point (Facade) that ties modules together
│   ├── cli.py             # CLI definitions using Typer
│   ├── transcription.py   # Transcription functions/classes (Factory & Strategy)
│   ├── diarization.py     # Diarization functions (Strategy Pattern)
│   ├── summarization.py   # Summarization logic (Factory & Strategy)
│   ├── config.py          # Loads configuration from .env using python-dotenv
│   └── utils.py           # Utility functions (logging, progress, adapters)
└── tests/
    ├── __init__.py
    ├── test_transcription.py
    ├── test_diarization.py
    ├── test_summarization.py
    ├── test_cli.py
    └── conftest.py       # Shared fixtures and test configurations
```

## Development Practices
- **Use of Type Hints:**  
  All functions, classes, and modules must include type hints to improve maintainability and clarity. For example:
  ```python
  def transcribe_audio(file_path: str) -> str:
      # type: (str) -> str
      ...
  ```
- **Code Style:**  
  Follow PEP 8 guidelines and use linters (e.g., `flake8`, `black`) to ensure consistent code style.
- **Documentation:**  
  Include comprehensive docstrings in all modules and functions detailing purpose, parameters, return types, and exceptions.

## Testing Strategy
- **Unit Testing:**  
  Use `pytest` to write unit tests for each module. Tests should cover:
  - Input validation and error handling in the CLI.
  - Correct API calls and responses for transcription.
  - Accuracy of diarization logic.
  - Summarization output formatting and content.
- **Integration Testing:**  
  Develop integration tests to simulate end-to-end usage (e.g., using a sample audio file or transcript).
- **Mocking External APIs:**  
  Use libraries like `pytest-mock` to simulate OpenAI API responses, ensuring tests are deterministic.
- **Test Coverage:**  
  Aim for high test coverage across modules. Tests are managed locally since CI/CD is not required for personal use.

## Secrets Management
- **Storing API Keys and Sensitive Data:**  
  Store all secrets (e.g., `OPENAI_API_KEY`) in a `.env` file located at the project’s root.
- **Example `.env` File:**
  ```ini
  OPENAI_API_KEY=your_openai_api_key_here
  ```
- **Loading Secrets:**  
  The `config.py` module will use python-dotenv to load these variables securely.
- **Security Best Practices:**  
  - Add the `.env` file to `.gitignore` to avoid accidental commits.
  - Document the setup of the `.env` file in the README.

## Type Hints and Code Quality
- **Mandatory Type Hints:**  
  All functions and methods must include type annotations for parameters and return types.
- **Example Function Signature:**
  ```python
  from typing import Optional

  def summarize_transcript(transcript: str, detail_level: int = 1) -> str:
      """
      Generate a detailed summary of the provided transcript.
      
      :param transcript: The full session transcript as a string.
      :param detail_level: Level of detail for the summary.
      :return: A markdown formatted summary.
      """
      # type: (str, int) -> str
      ...
  ```
- **Static Type Checking:**  
  Use tools like `mypy` during development to catch type errors early.

## Error Handling and API Rate Limits
- **Graceful Error Handling:**  
  Each module must implement error handling with clear and informative messages.  
  - For instance, if the transcription API returns a rate limit error (HTTP 429), implement exponential backoff before retrying.
  - Utilize Python’s `logging` module to log errors, warnings, and key informational messages.
- **Retries for API Calls:**  
  Implement a retry mechanism with a maximum retry count and delay logic in modules that interact with external APIs.
- **User Feedback:**  
  Use Rich’s progress indicators and status outputs to inform the user of any errors and the steps taken to address them.

---

