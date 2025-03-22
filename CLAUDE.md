# CLAUDE.md - Guidelines for Agentic Coding Assistants

## Build/Test Commands
- Run application: `python hello.py`
- Manage environment: 'uv'
- Add dependency: 'uv add <dpendency>'
- Install dependencies: `uv sync`
- Run tests: `pytest`
- Run single test: `pytest tests/path_to_test.py::test_function_name`
- Run with coverage: `pytest --cov=summarize_rpg_session`
- Format code: `black .`
- Lint code: `ruff check .`
- Type check: `mypy .`

## Code Style Guidelines
- **Formatting**: Follow PEP 8, use Black for auto-formatting
- **Imports**: Group standard library, third-party, and local imports with a blank line between groups
- **Typing**: Use type hints for all function parameters and return values
- **Naming**: 
  - snake_case for variables, functions, methods
  - CamelCase for classes
  - UPPER_CASE for constants
- **Documentation**: Docstrings for modules, classes, functions (Google style)
- **Error handling**: Use specific exceptions, handle exceptions at appropriate levels
- **Testing**: Write unit tests for all new functionality

This project is a Python application for transcribing and summarizing recordings or transcripts of tabletop roleplaying game sessions.