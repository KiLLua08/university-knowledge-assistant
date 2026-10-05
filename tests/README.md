# Tests

This directory contains the test suite for the university knowledge assistant.

## Purpose
- Unit tests for individual components
- Integration tests for pipelines
- End-to-end tests for the system
- Performance benchmarks

## Structure
```
tests/
├── __init__.py
├── test_config.py
├── test_data_ingestion.py
├── test_preprocessing.py
├── test_embeddings.py
├── test_retrieval.py
└── test_integration.py
```

## Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_preprocessing.py

# Run with coverage
pytest --cov=src/university_knowledge_assistant
```

## Guidelines
- Write tests for new functionality
- Maintain high test coverage
- Tests should be fast and reliable
- Mock external dependencies when appropriate

---

**Status:** Foundation only - Awaiting implementation
