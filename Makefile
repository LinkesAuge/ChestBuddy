.PHONY: test test-unit test-integration test-ui test-e2e test-all clean

# Default target
test: test-unit

# Run unit tests
test-unit:
	python -m pytest tests/unit -v

# Run integration tests
test-integration:
	python -m pytest tests/integration -v

# Run UI tests
test-ui:
	python -m pytest tests/ui -v

# Run end-to-end tests
test-e2e:
	python -m pytest tests/e2e -v

# Run all tests
test-all:
	python -m pytest tests -v

# Run tests with coverage
test-coverage:
	python -m pytest tests --cov=chestbuddy --cov-report=html --cov-report=term

# Run tests for a specific file
test-file:
	python -m pytest $(file) -v

# Clean up temporary files
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 