# Testing Guide for Scribe

This document provides instructions for running tests across the Scribe monorepo.

## Overview

The project includes test infrastructure for:
- **Backend (Python/FastAPI)**: Unit and integration tests using pytest
- **UI Package (React)**: Component tests using Vitest and React Testing Library

## Backend Testing

### Setup

1. Navigate to the backend service:
   ```bash
   cd services/backend
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

   Or use the Makefile:
   ```bash
   make install-dev
   ```

### Running Tests

Using pytest directly:
```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/services/test_arxiv_service.py

# Run specific test
pytest tests/unit/services/test_arxiv_service.py::TestArxivService::test_search_papers_standard_query
```

Using Makefile shortcuts:
```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run tests with coverage report
make test-coverage
```

### Test Structure

```
services/backend/
├── pytest.ini              # Pytest configuration
├── Makefile               # Test shortcuts
└── tests/
    ├── conftest.py        # Shared fixtures
    ├── unit/              # Unit tests
    │   └── services/
    │       └── test_arxiv_service.py
    └── integration/       # Integration tests
        └── routers/
            └── test_papers.py
```

### Available Fixtures

- `test_db`: In-memory SQLite database for testing
- `client`: FastAPI TestClient with test database
- `mock_settings`: Mock application settings
- `sample_paper_data`: Sample paper data for tests
- `sample_chat_message`: Sample chat message for tests

### Test Markers

- `@pytest.mark.unit`: Unit tests (isolated, fast)
- `@pytest.mark.integration`: Integration tests (with database/API)
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.agent`: Tests for AI agents

## Frontend Testing

### Setup

1. Navigate to the UI package:
   ```bash
   cd packages/ui
   ```

2. Install test dependencies:
   ```bash
   pnpm add -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom jsdom
   ```

### Running Tests

```bash
# Run tests once
pnpm test

# Run tests in watch mode
pnpm test -- --watch

# Run tests with UI
pnpm test:ui

# Run tests with coverage
pnpm test:coverage
```

### Test Structure

```
packages/ui/
├── vitest.config.ts       # Vitest configuration
└── src/
    ├── __tests__/
    │   └── setup.ts       # Test setup file
    ├── Modal/
    │   ├── Modal.tsx
    │   └── Modal.test.tsx
    └── LoadingDots/
        ├── LoadingDots.tsx
        └── LoadingDots.test.tsx
```

### Writing Tests

Example component test:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('handles clicks', () => {
    const onClick = vi.fn();
    render(<MyComponent onClick={onClick} />);

    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
```

## Next Steps

### Immediate Priorities

1. **Install Frontend Test Dependencies**:
   ```bash
   cd packages/ui
   pnpm add -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom jsdom
   ```

2. **Add Coverage Tools** (optional):
   ```bash
   # Backend
   pip install pytest-cov

   # Frontend
   pnpm add -D @vitest/coverage-v8
   ```

3. **Run Initial Tests**:
   ```bash
   # Backend
   cd services/backend && pytest

   # Frontend
   cd packages/ui && pnpm test
   ```

### Future Improvements

- [ ] Add tests for AI agents (researcher, teacher, scribe)
- [ ] Add tests for database models
- [ ] Add E2E tests for the web app (Playwright/Cypress)
- [ ] Set up CI/CD pipeline with automated testing
- [ ] Add API endpoint tests for chat and scribe routes
- [ ] Add visual regression tests for UI components
- [ ] Increase test coverage to >80%
- [ ] Add performance benchmarks
- [ ] Add load testing for API endpoints
- [ ] Add mutation testing

## Continuous Integration

When setting up CI/CD (e.g., GitHub Actions), add these steps:

```yaml
# Backend tests
- name: Run Backend Tests
  run: |
    cd services/backend
    pip install -e ".[dev]"
    pytest --cov=app --cov-report=xml

# Frontend tests
- name: Run Frontend Tests
  run: |
    cd packages/ui
    pnpm install
    pnpm test -- --run
```

## Best Practices

1. **Test Organization**: Co-locate tests with source code when possible
2. **Naming**: Use descriptive test names that explain what is being tested
3. **Fixtures**: Reuse fixtures for common setup
4. **Mocking**: Mock external dependencies (APIs, LLMs) to keep tests fast
5. **Coverage**: Aim for >80% coverage on critical business logic
6. **Speed**: Keep unit tests fast (<1s), mark slow tests appropriately
7. **Isolation**: Each test should be independent and not rely on others
8. **Documentation**: Document complex test scenarios

## Troubleshooting

### Backend

**Issue**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Make sure you're in the `services/backend` directory and have installed the package with `pip install -e .`

**Issue**: Database errors
- **Solution**: The tests use an in-memory SQLite database. Ensure `test_db` fixture is used correctly.

### Frontend

**Issue**: `Cannot find module '@testing-library/react'`
- **Solution**: Install the test dependencies: `pnpm add -D @testing-library/react @testing-library/jest-dom`

**Issue**: CSS module errors
- **Solution**: The vitest config is set up to handle CSS modules. Ensure you're using `vitest.config.ts`.

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
