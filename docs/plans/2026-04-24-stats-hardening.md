# Stats Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove private-repo names from normal stats logs, add aggregate `lines_changed` source reporting, apply small safe runtime optimizations, and rewrite the English/Korean READMEs to explain the Zig-derived fix and welcome further contributions.

**Architecture:** Keep the existing async flow intact and make the changes local to the current stats pipeline. Track one per-run `lines_changed` summary inside `Stats`, suppress repo-specific retry/clone logs for that path, expose one sanitized summary string, and have `generate_images.py` print it once after image generation. Rewrite docs in parallel with the code changes, but do not add new subsystems or change SVG behavior.

**Tech Stack:** Python 3, `asyncio`, `aiohttp`, `requests`, `unittest`, Markdown

---

## File Structure

- Modify: `github_stats.py`
  Add `lines_changed` result accounting, sanitized summary formatting, and quiet handling for repo-specific retry/fallback paths.
- Modify: `generate_images.py`
  Reuse `lines_changed` values locally, print one aggregate summary after generation, and avoid repeated property access in overview rendering.
- Modify: `test_github_stats.py`
  Add summary-classification, redaction, and caching regression tests.
- Create: `test_generate_images.py`
  Add tests for single-access overview rendering and sanitized summary printing.
- Modify: `README.md`
  Replace the current translated content with an English project README tailored to this fork.
- Create: `README-KR.md`
  Add a Korean companion README with the same structure and a slightly more operational tone.

### Task 1: Lock In Summary and Redaction Tests

**Files:**
- Modify: `test_github_stats.py`

- [ ] **Step 1: Write the failing tests for `lines_changed` summary accounting**

```python
class StatsTests(unittest.IsolatedAsyncioTestCase):
    async def test_lines_changed_summary_counts_api_fallback_and_failures(self):
        stats = Stats("octocat", "token", None)
        stats._repos = {"owner/api", "owner/fallback", "owner/fail"}
        stats.queries = _FakeQueries(
            responses={
                "/repos/owner/api/stats/contributors": [
                    (
                        200,
                        [
                            {
                                "author": {"login": "octocat"},
                                "weeks": [{"a": 4, "d": 1}],
                            }
                        ],
                    )
                ],
                "/repos/owner/fallback/stats/contributors": [(202, {})] * 10,
                "/repos/owner/fail/stats/contributors": [(500, {"message": "boom"})],
            }
        )
        stats._get_lines_changed_from_git = mock.AsyncMock(
            return_value=(3, 2, "git_fallback")
        )

        with mock.patch("github_stats.asyncio.sleep", new=mock.AsyncMock()):
            result = await stats.lines_changed
            summary = await stats.lines_changed_summary

        self.assertEqual(result, (7, 3))
        self.assertEqual(
            summary,
            {"api_success": 1, "git_fallback_success": 1, "failed": 1},
        )

    async def test_lines_changed_summary_redacts_repository_names(self):
        stats = Stats("octocat", "token", None)
        stats._lines_changed = (7, 3)
        stats._lines_changed_summary = {
            "api_success": 2,
            "git_fallback_success": 1,
            "failed": 1,
        }

        summary = await stats.lines_changed_summary_text

        self.assertEqual(
            summary,
            "Lines changed sources: API 2 | git fallback 1 | failed 1",
        )
        self.assertNotIn("owner/api", summary)
        self.assertNotIn("owner/fallback", summary)

    async def test_lines_changed_result_is_reused_after_first_calculation(self):
        stats = Stats("octocat", "token", None)
        stats._repos = {"owner/repo"}
        stats._fetch_lines_changed = mock.AsyncMock(return_value=(1, 1, "api"))

        first = await stats.lines_changed
        second = await stats.lines_changed

        self.assertEqual(first, (1, 1))
        self.assertEqual(second, (1, 1))
        stats._fetch_lines_changed.assert_awaited_once_with("owner/repo")
```

- [ ] **Step 2: Run the stats test file to confirm the new tests fail**

Run: `python3 -m unittest -v test_github_stats.py`  
Expected: `FAIL` or `ERROR` because `Stats` does not yet expose `lines_changed_summary`, `lines_changed_summary_text`, or the new `(additions, deletions, source)` return shape.

- [ ] **Step 3: Commit the failing-test checkpoint**

```bash
git add test_github_stats.py
git commit -m "test: add lines changed summary regressions"
```

### Task 2: Implement Quiet `lines_changed` Accounting in `Stats`

**Files:**
- Modify: `github_stats.py`
- Test: `test_github_stats.py`

- [ ] **Step 1: Add summary state and async accessors in `Stats`**

```python
class Stats(object):
    def __init__(...):
        ...
        self._lines_changed = None
        self._lines_changed_summary = None

    def _new_lines_changed_summary(self) -> Dict[str, int]:
        return {
            "api_success": 0,
            "git_fallback_success": 0,
            "failed": 0,
        }

    @property
    async def lines_changed_summary(self) -> Dict[str, int]:
        if self._lines_changed_summary is not None:
            return self._lines_changed_summary
        await self.lines_changed
        assert self._lines_changed_summary is not None
        return self._lines_changed_summary

    @property
    async def lines_changed_summary_text(self) -> str:
        summary = await self.lines_changed_summary
        return (
            "Lines changed sources: "
            f"API {summary['api_success']} | "
            f"git fallback {summary['git_fallback_success']} | "
            f"failed {summary['failed']}"
        )
```

- [ ] **Step 2: Make REST retries for repo stats quiet and return a source tag**

```python
async def query_rest_response(
    self,
    path: str,
    params: Optional[Dict] = None,
    max_attempts: int = 10,
    retry_statuses: Optional[Set[int]] = None,
    verbose: bool = True,
) -> Tuple[int, object]:
    ...
    if r.status in retry_statuses and attempt + 1 < max_attempts:
        if verbose:
            print(
                f"{path} returned {r.status}. Retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{max_attempts})..."
            )
        await asyncio.sleep(delay)
        continue
    ...
    if last_status in retry_statuses and verbose:
        print(
            f"Too many {last_status}s for {path}. Falling back to git clone if applicable."
        )

async def _fetch_lines_changed(self, repo: str) -> Tuple[int, int, str]:
    status, response = await self.queries.query_rest_response(
        f"/repos/{repo}/stats/contributors",
        max_attempts=10,
        retry_statuses={202, 403, 429},
        verbose=False,
    )
    if status == 200 and isinstance(response, list):
        ...
        return additions, deletions, "api"
    if status in {202, 403, 429}:
        return await self._get_lines_changed_from_git(repo)
    return 0, 0, "failed"
```

- [ ] **Step 3: Remove repo-specific fallback prints and aggregate the summary once**

```python
@property
async def lines_changed(self) -> Tuple[int, int]:
    if self._lines_changed is not None:
        return self._lines_changed

    repos = list(await self.repos)
    results = await asyncio.gather(*[self._fetch_lines_changed(repo) for repo in repos])
    summary = self._new_lines_changed_summary()
    total_additions = 0
    total_deletions = 0

    for additions, deletions, source in results:
        total_additions += additions
        total_deletions += deletions
        if source == "api":
            summary["api_success"] += 1
        elif source == "git_fallback":
            summary["git_fallback_success"] += 1
        else:
            summary["failed"] += 1

    self._lines_changed = (total_additions, total_deletions)
    self._lines_changed_summary = summary
    return self._lines_changed

async def _get_lines_changed_from_git(self, repo: str) -> Tuple[int, int, str]:
    if shutil.which("git") is None:
        return 0, 0, "failed"

    login = await self._get_login()
    emails = await self._get_user_emails()
    async with self._clone_semaphore:
        result = await asyncio.to_thread(
            self._get_lines_changed_from_git_sync,
            repo,
            emails,
            login,
        )
    if result is None:
        return 0, 0, "failed"
    additions, deletions = result
    return additions, deletions, "git_fallback"
```

- [ ] **Step 4: Update git fallback helpers so failures are classified without leaking repo names**

```python
def _get_lines_changed_from_git_sync(
    self, repo: str, emails: List[str], login: str
) -> Optional[Tuple[int, int]]:
    ...
    if clone.returncode != 0:
        return None
    ...
    if log.returncode != 0:
        return None
    ...
    return additions, deletions
```

- [ ] **Step 5: Run the stats tests and confirm they pass**

Run: `python3 -m unittest -v test_github_stats.py`  
Expected: all tests in `test_github_stats.py` pass, including the three new summary/caching assertions.

- [ ] **Step 6: Commit the `Stats` implementation**

```bash
git add github_stats.py test_github_stats.py
git commit -m "feat: add sanitized lines changed summary"
```

### Task 3: Add Entry-Point Summary Output and Small Speed Cleanup

**Files:**
- Modify: `generate_images.py`
- Create: `test_generate_images.py`

- [ ] **Step 1: Write the failing tests for sanitized summary printing and single `lines_changed` access**

```python
import asyncio
import unittest
from unittest import mock

import generate_images


class _FakeStats:
    def __init__(self):
        self.lines_changed_calls = 0

    @property
    async def name(self):
        return "Octocat"

    @property
    async def stargazers(self):
        return 1

    @property
    async def forks(self):
        return 2

    @property
    async def total_contributions(self):
        return 3

    @property
    async def lines_changed(self):
        self.lines_changed_calls += 1
        return (7, 3)

    @property
    async def views(self):
        return 4

    @property
    async def all_repos(self):
        return {"owner/repo"}

    @property
    async def lines_changed_summary_text(self):
        return "Lines changed sources: API 2 | git fallback 1 | failed 0"


class GenerateImagesTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_overview_reads_lines_changed_once(self):
        stats = _FakeStats()
        template = "{{ name }} {{ stars }} {{ forks }} {{ contributions }} {{ lines_changed }} {{ views }} {{ repos }}"

        with mock.patch("builtins.open", mock.mock_open(read_data=template)), mock.patch(
            "generate_images.generate_output_folder"
        ):
            await generate_images.generate_overview(stats)

        self.assertEqual(stats.lines_changed_calls, 1)

    async def test_print_lines_changed_summary_emits_one_sanitized_line(self):
        stats = _FakeStats()

        with mock.patch("builtins.print") as print_mock:
            await generate_images.print_lines_changed_summary(stats)

        print_mock.assert_called_once_with(
            "Lines changed sources: API 2 | git fallback 1 | failed 0"
        )
```

- [ ] **Step 2: Run the new generate-images test file to confirm it fails**

Run: `python3 -m unittest -v test_generate_images.py`  
Expected: `FAIL` because `print_lines_changed_summary()` does not exist yet and `generate_overview()` still reads `await s.lines_changed` twice.

- [ ] **Step 3: Implement the local caching and one-line summary printer**

```python
async def generate_overview(s: Stats) -> None:
    with open("templates/overview.svg", "r", encoding="utf-8") as f:
        output = f.read()

    lines_changed = await s.lines_changed
    changed = lines_changed[0] + lines_changed[1]
    output = re.sub("{{ name }}", await s.name, output)
    output = re.sub("{{ stars }}", f"{await s.stargazers:,}", output)
    output = re.sub("{{ forks }}", f"{await s.forks:,}", output)
    output = re.sub("{{ contributions }}", f"{await s.total_contributions:,}", output)
    output = re.sub("{{ lines_changed }}", f"{changed:,}", output)
    output = re.sub("{{ views }}", f"{await s.views:,}", output)
    output = re.sub("{{ repos }}", f"{len(await s.all_repos):,}", output)
    ...

async def print_lines_changed_summary(s: Stats) -> None:
    print(await s.lines_changed_summary_text)

async def main() -> None:
    ...
    async with aiohttp.ClientSession() as session:
        s = Stats(...)
        await asyncio.gather(generate_languages(s), generate_overview(s))
        await print_lines_changed_summary(s)
```

- [ ] **Step 4: Run both test modules and confirm they pass together**

Run: `python3 -m unittest -v test_github_stats.py test_generate_images.py`  
Expected: both test modules pass with no repo names in printed summary output.

- [ ] **Step 5: Commit the entry-point cleanup**

```bash
git add generate_images.py test_generate_images.py
git commit -m "perf: summarize lines changed sources once"
```

### Task 4: Rewrite the Project Documentation

**Files:**
- Modify: `README.md`
- Create: `README-KR.md`

- [ ] **Step 1: Rewrite `README.md` as the primary English document**

```md
# github-stats-transparent

Transparent GitHub stats cards generated with GitHub Actions.

This fork started from `rahul-jha98/github-stats-transparent`, but it now includes a Python reimplementation of the relevant `jstrieb/github-stats` Zig logic for `Lines of code changed`.

## Why this fork exists

The original transparent fork kept the presentation layer but inherited the long-standing `Lines of code changed` accuracy problem from the older Python implementation.

This fork fixes that by porting two behaviors from the upstream Zig version:

- short random retries for `202 Accepted` repository stats responses
- git-based fallback using contributor email matching when the stats API does not return usable data

## Features

- transparent SVG cards for overview and language usage
- support for private repositories through a personal access token
- more reliable `Lines of code changed` calculation
- sanitized summary logging for `lines_changed` execution

## Setup

1. Create a personal access token with `read:user`, `repo`, and `user:email`.
2. Add it as the `ACCESS_TOKEN` repository secret.
3. Optionally configure `EXCLUDED`, `EXCLUDED_LANGS`, and `COUNT_STATS_FROM_FORKS`.
4. Run the workflow or execute `python3 generate_images.py`.

## Contributing

Issues and pull requests are welcome, especially for:

- stats accuracy improvements
- runtime improvements
- documentation improvements
- compatibility fixes for GitHub API changes
```

- [ ] **Step 2: Add `README-KR.md` with the same structure in Korean**

```md
# github-stats-transparent 한국어 안내

GitHub Actions로 투명 배경의 GitHub 통계 카드를 생성하는 프로젝트입니다.

이 포크는 `rahul-jha98/github-stats-transparent`에서 출발했지만, 현재는 `Lines of code changed` 문제를 해결하기 위해 `jstrieb/github-stats`의 Zig 구현 핵심 로직을 Python으로 다시 옮긴 버전입니다.

## 이 포크가 필요한 이유

기존 투명 테마 포크는 시각적 출력은 유지했지만, `Lines of code changed` 집계는 오래된 Python 구현의 한계를 그대로 안고 있었습니다.

이 저장소는 다음 두 가지를 적용해 그 문제를 해결합니다.

- `202 Accepted` 응답에 대한 짧은 랜덤 재시도
- 통계 API가 끝까지 준비되지 않을 때 git 로그와 contributor email을 이용한 폴백 계산

## 설정 방법

1. `read:user`, `repo`, `user:email` 권한이 있는 Personal Access Token을 생성합니다.
2. 저장소 시크릿에 `ACCESS_TOKEN`으로 등록합니다.
3. 필요하면 `EXCLUDED`, `EXCLUDED_LANGS`, `COUNT_STATS_FROM_FORKS`를 설정합니다.
4. Actions 워크플로 또는 `python3 generate_images.py`로 이미지를 생성합니다.

## 기여

이슈와 PR은 언제든지 환영합니다. 특히 다음과 같은 기여에 열려 있습니다.

- 통계 정확도 개선
- 실행 속도 개선
- 문서 개선
- GitHub API 변경 대응
```

- [ ] **Step 3: Run a quick content review on both READMEs**

Run: `sed -n '1,240p' README.md`  
Run: `sed -n '1,240p' README-KR.md`  
Expected: both files clearly mention the Zig-derived fix, setup requirements, sanitized logging, and that further contributions are welcome.

- [ ] **Step 4: Commit the documentation rewrite**

```bash
git add README.md README-KR.md
git commit -m "docs: rewrite project readmes"
```

### Task 5: Final Verification

**Files:**
- Modify: `github_stats.py`
- Modify: `generate_images.py`
- Modify: `test_github_stats.py`
- Create: `test_generate_images.py`
- Modify: `README.md`
- Create: `README-KR.md`

- [ ] **Step 1: Run the full unit-test suite**

Run: `python3 -m unittest -v test_github_stats.py test_generate_images.py`  
Expected: all tests pass.

- [ ] **Step 2: Run Python syntax validation**

Run: `python3 -m py_compile github_stats.py generate_images.py test_github_stats.py test_generate_images.py`  
Expected: command exits successfully with no output.

- [ ] **Step 3: Optionally run the generator with a valid token**

Run: `python3 generate_images.py`  
Expected: `generated/overview.svg` and `generated/languages.svg` are updated, and the terminal ends with one sanitized line such as `Lines changed sources: API 12 | git fallback 3 | failed 0`.

- [ ] **Step 4: Commit the final verified state**

```bash
git add github_stats.py generate_images.py test_github_stats.py test_generate_images.py README.md README-KR.md
git commit -m "feat: harden stats logging and docs"
```
