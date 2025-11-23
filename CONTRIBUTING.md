# Contributing to TwisterLab

Thank you for your interest in contributing to TwisterLab! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- kubectl (for Kubernetes development)
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/TwisterLab.git
   cd TwisterLab
   ```

3. Set up the upstream remote:

   ```bash
   git remote add upstream https://github.com/youneselfakir0/TwisterLab.git
   ```

## Development Setup

### Local Development Environment

1. **Install dependencies:**

   ```bash
   make install
   ```

2. **Set up development environment:**

   ```bash
   make dev
   ```

3. **Run the application:**

   ```bash
   # API will be available at http://localhost:8000
   # Grafana at http://localhost:3001
   # Prometheus at http://localhost:9090
   ```

### Kubernetes Development

For full Kubernetes development:

```bash
# Deploy to local k3s cluster
make k8s-deploy

# Check status
make k8s-status

# View logs
make logs
```

## Development Workflow

### Branch Naming

Use descriptive branch names following this pattern:

- `feature/description-of-feature`
- `bugfix/issue-description`
- `hotfix/critical-fix`
- `docs/update-documentation`

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

Examples:
```
feat(api): add user authentication endpoint
fix(mcp): resolve connection timeout issue
docs(readme): update installation instructions
```

## Code Standards

### Python Standards

- **Formatting:** Black (88 characters line length)
- **Linting:** Ruff
- **Type checking:** MyPy
- **Imports:** Absolute imports from project root

### Code Quality

- All functions must have type hints
- Comprehensive error handling
- Async/await for agent operations
- Structured logging with context
- Unit test coverage > 80%

### Architecture Guidelines

- **Agents:** Inherit from `TwisterAgent` base class
- **API:** Follow RESTful conventions
- **MCP:** Implement Model Context Protocol standards
- **K8s:** Use declarative manifests
- **Security:** Validate inputs, use secrets management

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=src/twisterlab --cov-report=html
```

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── fixtures/      # Test data and fixtures
```

### Test Requirements

- Unit tests for all new functions
- Integration tests for API endpoints
- E2E tests for critical workflows
- Mock external dependencies

## Submitting Changes

### Pull Request Process

1. **Create a branch** from `main`:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code standards

3. **Test your changes**:

   ```bash
   make test
   make lint
   ```

4. **Update documentation** if needed

5. **Commit your changes**:

   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

### PR Requirements

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] PR template filled out
- [ ] Related issues linked
- [ ] Self-review completed

## Documentation

### Documentation Structure

```text
docs/
├── guides/         # User guides
├── api/           # API documentation
├── architecture/  # System architecture
└── development/   # Development guides
```

### Documentation Standards

- Use Markdown for all documentation
- Include code examples where relevant
- Keep screenshots up to date
- Use consistent formatting
- Link related documentation

### API Documentation

- OpenAPI/Swagger specifications
- Example requests/responses
- Authentication requirements
- Rate limiting information

## Getting Help

### Communication Channels

- **Issues:** Bug reports and feature requests
- **Discussions:** General questions and ideas
- **Pull Requests:** Code review and contributions

### Labels

Common issue labels:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Beginner-friendly tasks
- `help wanted`: Community contributions welcome

## Recognition

Contributors are recognized through:

- GitHub contributor statistics
- Mention in release notes
- Attribution in documentation
- Community recognition

Thank you for contributing to TwisterLab! 🚀
