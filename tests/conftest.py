"""Test configuration for the summarize_rpg_session tests."""

import os
import pytest
import tempfile

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    path = tempfile.mkdtemp()
    yield path
    os.rmdir(path)