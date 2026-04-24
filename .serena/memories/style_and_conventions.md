# Style And Conventions

Python style in this repo is straightforward and conservative:

- module-level docstrings are used
- snake_case for functions, methods, variables, and helper names
- UPPER_SNAKE_CASE for environment variable names
- explicit typing is common (`Dict`, `List`, `Optional`, `Set`, `Tuple`)
- class-based organization for core logic (`Queries`, `Stats`)
- async/await is used for network-facing logic
- tests use `unittest`, especially `IsolatedAsyncioTestCase`

Editing guidance:

- preserve existing naming and docstring tone
- prefer small, targeted changes over broad refactors
- follow existing fallback/error-handling patterns around GitHub API access
- keep README/docs concise and aligned with current workflow/env var names
