.PHONY: test test-unit test-integration test-coverage install-dev

# Run all tests
test:
	pytest

# Run only unit tests
test-unit:
	pytest -m unit

# Run only integration tests
test-integration:
	pytest -m integration

# Run tests with coverage report
test-coverage:
	pytest --cov=app --cov-report=html --cov-report=term-missing

# Install development dependencies
install-dev:
	pip install -e ".[dev]"
