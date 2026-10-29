# Quality Tooling Refresh

## Approved Scope

Refresh supported dependencies and existing quality tooling.
Preserve public APIs, generated artifacts and repository-specific boundaries.

## Acceptance

- Pinact remains locked to `4.1.1` with `lint` and `upgrade`.
- The full no-fix Trunk scan and declared project gates pass.
- Changed manifests have package-manager-generated lockfiles under repository policy.
- Advisory dispositions have specific evidence and affected knowledge claims are reconciled.

## Repository Boundaries

- Preserve the existing pip installation policy and lower-bound requirements unless dependency metadata or an advisory requires a change.
- Require `certifi>=2026.10.23` to exclude releases affected by `GHSA-6q48-6c7w-9gw2`.
- Generate `requirements-lock.txt` with `uv pip compile --universal --python-version 3.12`; both workflows install this file with pip.
- Preserve Trunk CLI `1.25.0`, plugin `v1.11.0`, and managed runtimes unless a demonstrated compatibility failure requires a change.
- Confirm the existing unit tests replace HTTP clients and git subprocesses before running them.
- Record the actual local Python version separately from CI's Python 3.12.
- Do not run the API-backed generator, access provider credentials, change generated SVG or image assets, or write to the `output` branch.
- Keep scanner coverage and justified exclusions intact; report unsupported or skipped targets explicitly.

## Publication

Push and PR creation require explicit repository-specific approval.
After approval, continue the requested hosted gates, merge, cleanup and memory recording.

## Filesystem Reader Follow-up

Use the reviewed standard-library filesystem reader and 17 regressions from the shared maintenance implementation.
Add its project-relative path to Trunk's `direct_configs` so the copy sandbox contains the reader.
Retain decoded results at file level when no literal position is available, omit secret values from messages and reject malformed conversion without partial clean output.
Run the exact test file in CI without changing the existing application or plugin commands.
Preserve public contracts, product source, manifests, locks, workflows that publish output, runtime pins, hook policies and exclusions.

## Offline scanner resource boundary

Run `python3 -B .trunk/configs/tests/test_trufflehog_to_sarif.py` for the 17 command-line reader regressions.
Source context is limited to 1 MiB plus a sentinel byte per read and at most eight cached files.
Oversized, unreadable, binary or decoded-only findings retain file-level diagnostics instead of disappearing.
Native Trunk paths and Unicode code-point columns are preserved.
The large-source and multi-file regressions measure traced Python allocations on ASCII fixtures; they do not establish a universal process RSS or I/O timeout bound.
Malformed scanner input fails the gate, and candidate credentials are never verified with a provider.
