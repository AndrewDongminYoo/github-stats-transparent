# Suggested Commands

Setup:

- `python3 -m venv .venv`
- `.venv/bin/pip install -r requirements.txt`

Testing:

- `python3 -m unittest -v test_github_stats.py`

Run locally:

- `python3 generate_images.py`
- `python3 github_stats.py`

Lint / format:

- `trunk check`
- `trunk check --fix`
- `trunk fmt`

Useful macOS shell commands:

- `pwd`
- `ls -la`
- `cd <path>`
- `rg -n "pattern" <path>`
- `rg --files`
- `find . -maxdepth 3 -type f`
- `git status --short`
- `git diff -- <path>`
