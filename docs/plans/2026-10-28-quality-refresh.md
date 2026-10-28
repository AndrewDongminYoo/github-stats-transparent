# Quality Tooling Refresh Plan

## Work

1. Verify repository identity, instructions, current changes and Oracle precedent.
2. Refresh compatible dependency and linter versions with existing package managers.
3. Run the declared local gates and `trunk check --all --no-fix`.
4. Reconcile affected knowledge and review the scoped candidate.
5. Commit locally and prepare visible evidence before requesting publication approval.

## Declared Gates

1. Generate the universal Python 3.12 lock with `uv pip compile requirements.txt --universal --python-version 3.12 --output-file requirements-lock.txt`; regenerate into a temporary evidence file and compare dependency content.
2. Install locked dependencies in an ignored virtual environment → verify: `.venv/bin/python -m pip install -r requirements-lock.txt` and `.venv/bin/python -m pip check`.
3. Inspect the resolved dependency graph and primary package metadata → verify: `.venv/bin/python -m pip inspect --local` and PyPI release metadata, including known vulnerabilities and Python compatibility for locked versions.
4. Run the offline unit suite after checking its HTTP and git mocks → verify: `.venv/bin/python -m unittest`.
5. Run all enabled repository checks without fixes → verify: `trunk check --all --no-fix --jobs=2` and inspect actual executed commands and scanner targets.
6. Reconcile affected validation claims and review the diff → verify: documentation paths and commands against the workflow, test fixtures and Trunk configuration, then `git diff --check`.
