# Stats Hardening Design

## Summary

This fork will harden `github-stats-transparent` in three areas:

1. Remove per-repository log output that can leak private repository names into GitHub Actions logs.
2. Improve generation speed with small, low-risk optimizations around repeated `lines_changed` access and summary reporting.
3. Rewrite the documentation so the project clearly explains that it fixes the longstanding `Lines of code changed` issue in `rahul-jha98/github-stats-transparent` by reimplementing the relevant `jstrieb/github-stats` Zig behavior in Python.

The implementation will stay intentionally conservative. It will not redesign the entire stats pipeline or add a large caching subsystem.

## Background

This repository started as a fork of `rahul-jha98/github-stats-transparent`, which itself is based on `jstrieb/github-stats`.

The main functional gap was inaccurate `Lines of code changed` output. The fix already introduced in this fork follows the upstream Zig implementation in two key ways:

- short random retries for GitHub `stats/contributors` `202 Accepted` responses instead of exponential backoff
- git-based fallback using contributor email matching when the GitHub stats API does not produce usable data

Now that the calculation path is fixed, the remaining work is to make the behavior safer and easier to understand.

## Goals

- Remove repository names from normal progress logs.
- Preserve useful visibility by reporting aggregate counts only:
  - repositories handled through the stats API
  - repositories handled through git fallback
  - repositories that still failed completely
- Reduce avoidable overhead without expanding scope into a heavy refactor.
- Replace the current translated README with cleaner, project-specific documentation.
- Add an explicit invitation for issues and pull requests.

## Non-Goals

- No complete rewrite of the request scheduler.
- No aggressive concurrency redesign for API and git fallback work.
- No new `CONTRIBUTING.md` in this pass.
- No changes to SVG templates or visual output format.

## Design Decisions

### 1. Logging policy

Current code prints repository-specific progress such as retry messages, clone messages, and failures. That is useful for debugging but unsafe for Actions logs when private repositories are involved.

The new policy is:

- do not print repository names during normal execution
- do not print per-repository retry progress
- do not print per-repository clone progress
- print one final `lines_changed` summary with aggregate counts only

The final report should expose only:

- API success count
- git fallback success count
- complete failure count

This keeps the logs actionable without leaking repository identity.

### 2. Speed optimization scope

Optimization will stay in the "balanced" range:

- ensure `lines_changed` results are computed once and reused
- ensure the execution summary is produced from already-collected state instead of triggering extra work
- remove noisy log I/O that provides little value and can slow Actions output
- keep git fallback concurrency capped and unchanged unless a small targeted adjustment is clearly safe

The implementation should not introduce a larger task orchestration layer.

### 3. Documentation structure

The documentation will be split into:

- `README.md`: primary English project document
- `README-KR.md`: Korean companion document

`README.md` should explain:

- what the project does
- why this fork exists
- what was wrong in the older Python transparent fork
- how this fork resolved the `Lines of code changed` issue using logic ported from `jstrieb/github-stats`
- installation and required token scopes
- configuration options
- limitations and expected behavior
- invitation for bug reports and pull requests

`README-KR.md` should mirror the same structure in Korean with slightly more operational guidance where useful.

The existing warning about private repository names leaking through logs should be removed because the new logging policy is specifically designed to eliminate that risk in normal operation.

## File-Level Plan

### `github_stats.py`

- add internal execution-summary state for the `lines_changed` pipeline
- classify each repository result as:
  - API success
  - git fallback success
  - failure
- remove or replace repo-specific `print()` calls with quiet internal accounting
- expose one summary output path that reports only aggregate counts

### `generate_images.py`

- avoid repeated access patterns that unnecessarily await the same values multiple times
- emit the final aggregate `lines_changed` summary once, after stats generation has completed

### `test_github_stats.py`

- add tests that prove summary counts are classified correctly
- add tests that prove repo names are not emitted in normal summary logging
- add tests that prove `lines_changed` results are reused instead of recomputed

### `README.md`

- replace the current translated document with a full English rewrite tailored to this fork

### `README-KR.md`

- add a Korean rewrite aligned with the English README

## Testing Strategy

Before implementation is considered complete:

- run `python3 -m unittest -v test_github_stats.py`
- run `python3 -m py_compile github_stats.py generate_images.py test_github_stats.py`
- optionally run `python3 generate_images.py` in an environment with valid GitHub credentials to confirm the new end-of-run summary output

## Risks and Mitigations

### Loss of debugging detail

Removing per-repo logs reduces immediate visibility when a single repository misbehaves.

Mitigation:

- keep the result buckets explicit
- preserve code structure so targeted debug logs can be temporarily reintroduced locally when needed

### Behavior drift in `lines_changed`

The logging cleanup must not alter the actual counting behavior.

Mitigation:

- add focused tests around classification and caching
- avoid mixing correctness changes with large refactors

## Success Criteria

This work is successful when:

- normal Actions logs no longer reveal repository names from the stats pipeline
- users can still see how many repositories succeeded through API, succeeded through fallback, or failed
- generation time is modestly improved without destabilizing the code
- both READMEs clearly explain the fork's purpose and the upstream Zig-based fix
- the docs clearly welcome further contributions
