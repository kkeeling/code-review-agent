# Engineering Conventions

## Conventions

> When writing code, follow these conventions.

- Write simple, verbose code over terse, compact, dense code.
- Write unit tests for all functions.

## Project Structure

- `code-review-agent.py` – Entire Agent
- `README.md` – Project Documentation
- `CONVENTIONS.md` – Engineering Conventions
- `requirements.txt` – Project Dependencies
- `pyproject.toml` – Project Configuration

## Naming Conventions

> When naming things, follow these conventions.

- Use `camelCase` for variable names
- Use `PascalCase` for class names
- Use `PascalCase` for component names
- Use `PascalCase` for module names
- Use `PascalCase` for hook names
- Use `PascalCase` for context names
- Use `kebab-case` for file names
- Use `SNAKE_CASE` for constants
- Use `camelCase` for function names
- Use `camelCase` for method names
- Use `camelCase` for property names
- Use `PascalCase` for interface names
- Use `PascalCase` for type names
- Use `kebab-case` for CSS class names
- Use `kebab-case` for HTML attributes

## Package Management

> When managing packages, follow these conventions.

- Use `conda` for virtual environments
- Use `pip` for package management

## Testing Conventions

> When writing tests, follow these conventions.

- Use `pytest` for testing

## Implementation Conventions

> When implementing code, follow these conventions.

- Use `with Halo` to wrap functions that take a long time to execute.
- Use `with Halo` to wrap functions that fetch data from the internet.
