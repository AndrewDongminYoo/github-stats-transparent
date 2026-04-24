# Task Completion

When finishing a task in this repo:

- run relevant unit tests, at minimum `python3 -m unittest -v test_github_stats.py` for current Python logic changes
- if formatting/lint-sensitive files changed, run `trunk check` and `trunk fmt` or `trunk check --fix` as appropriate
- if workflow or image-generation behavior changed, verify the related entrypoint locally when practical with `python3 generate_images.py` and the required env vars
- review `git diff --stat` / `git diff` for unintended changes
- avoid committing `.serena/cache/` or `.serena/project.local.yml`
