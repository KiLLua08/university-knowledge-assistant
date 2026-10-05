"""
Test package import and basic functionality.
This is a minimal test to establish the testing foundation.
"""

import pytest


def test_package_import():
    """Test that the package can be imported."""
    try:
        import university_knowledge_assistant
        assert university_knowledge_assistant.__version__ == "0.1.0"
    except ImportError as e:
        pytest.fail(f"Failed to import package: {e}")


def test_version_exists():
    """Test that version is defined."""
    from university_knowledge_assistant import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)
