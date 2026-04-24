# github-stats-transparent

Purpose: generate transparent GitHub stats SVG images for a user/repository setup, primarily via GitHub Actions.

Tech stack:

- Python 3
- asyncio
- aiohttp
- requests
- unittest
- Markdown docs
- GitHub Actions
- Trunk for linting/formatting

Key entrypoints:

- `generate_images.py`: main image generation entrypoint; reads GitHub-related env vars and writes `generated/*.svg`
- `github_stats.py`: core API/query/stat aggregation logic; also has a standalone debug-style main
- `test_github_stats.py`: async unit tests for stats hardening and fallback behavior

Repo layout:

- `github_stats.py`: core stats/query implementation
- `generate_images.py`: SVG generation from templates
- `templates/`: SVG templates
- `docs/specs/` and `docs/plans/`: design and implementation notes
- `.github/workflows/main.yml`: scheduled/manual image generation workflow
- `.trunk/`: lint/format configuration

Environment notes:

- Local interpreter is expected at `.venv/bin/python` per `.vscode/settings.json`
- Main runtime env vars are `ACCESS_TOKEN` or `GITHUB_TOKEN`, plus optional `EXCLUDED`, `EXCLUDED_LANGS`, and `COUNT_STATS_FROM_FORKS`
- System is Darwin (macOS)
