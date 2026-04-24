import asyncio
import subprocess
import sys
import types
import unittest
from unittest import mock

sys.modules.setdefault(
    "aiohttp",
    types.SimpleNamespace(
        ClientError=Exception,
        ClientSession=object,
    ),
)
sys.modules.setdefault(
    "requests",
    types.SimpleNamespace(
        get=lambda *args, **kwargs: None,
        post=lambda *args, **kwargs: None,
    ),
)

from github_stats import Stats


class _FakeResponse:
    def __init__(self, status: int):
        self.status = status


class _FakeSession:
    async def get(self, *args, **kwargs):
        return _FakeResponse(202)


class _FakeQueries:
    def __init__(self, responses=None):
        self.access_token = "token"
        self.semaphore = asyncio.Semaphore(10)
        self.session = _FakeSession()
        self._responses = responses or {}

    async def query_rest(self, path, params=None):
        responses = self._responses.get(path, [])
        if responses:
            value = responses.pop(0)
            if isinstance(value, tuple):
                return value[1]
            return value
        return {}

    async def query_rest_response(
        self, path, params=None, max_attempts=10, retry_statuses=None
    ):
        responses = self._responses.get(path, [])
        if responses:
            value = responses.pop(0)
            if isinstance(value, tuple):
                return value
            return 200, value
        return 200, {}


async def _run_immediately(func, *args, **kwargs):
    return func(*args, **kwargs)


class StatsTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_lines_changed_uses_cached_login_when_username_missing(self):
        stats = Stats(None, "token", None)
        stats._login = "octocat"
        stats.queries = _FakeQueries(
            responses={
                "/repos/owner/repo/stats/contributors": [
                    (
                        200,
                        [
                            {
                                "author": {"login": "octocat"},
                                "weeks": [{"a": 5, "d": 2}],
                            }
                        ],
                    )
                ],
            }
        )

        result = await stats._fetch_lines_changed("owner/repo")

        self.assertEqual(result, (5, 2))

    async def test_lines_changed_falls_back_to_git_when_stats_api_never_finishes(self):
        stats = Stats("octocat", "token", None)
        stats._repos = {"owner/repo"}
        stats.queries = _FakeQueries(
            responses={
                "/repos/owner/repo/stats/contributors": [(202, {})] * 10,
            }
        )
        stats._get_lines_changed_from_git = mock.AsyncMock(return_value=(7, 3))

        with mock.patch("github_stats.asyncio.sleep", new=mock.AsyncMock()):
            result = await stats.lines_changed

        self.assertEqual(result, (7, 3))
        stats._get_lines_changed_from_git.assert_awaited_once_with("owner/repo")

    async def test_get_user_emails_falls_back_to_noreply_address(self):
        stats = Stats("octocat", "token", None)
        stats.queries = _FakeQueries(
            responses={
                "/user/emails": [(403, {"message": "Forbidden"})],
            }
        )

        result = await stats._get_user_emails()

        self.assertEqual(result, ["octocat@users.noreply.github.com"])

    async def test_git_fallback_sums_numstat_for_all_known_emails(self):
        stats = Stats("octocat", "token", None)

        with mock.patch.object(
            stats,
            "_get_user_emails",
            new=mock.AsyncMock(return_value=["one@example.com", "two@example.com"]),
        ), mock.patch(
            "github_stats.shutil.which", return_value="/usr/bin/git"
        ), mock.patch(
            "github_stats.asyncio.to_thread", side_effect=_run_immediately
        ), mock.patch(
            "github_stats.subprocess.run"
        ) as run_mock:
            run_mock.side_effect = [
                subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="5\t3\tfoo.py\n-\t4\tbin.dat\n2\t1\tbar.py\n",
                    stderr="",
                ),
            ]

            result = await stats._get_lines_changed_from_git("owner/repo")

        self.assertEqual(result, (7, 8))
        log_command = run_mock.call_args_list[1].args[0]
        self.assertEqual(log_command[:4], ["git", "-C", log_command[2], "log"])
        self.assertEqual(log_command.count("--author"), 2)
        self.assertIn("one@example.com", log_command)
        self.assertIn("two@example.com", log_command)

    async def test_git_fallback_uses_cached_login_when_username_missing(self):
        stats = Stats(None, "token", None)
        stats._login = "octocat"

        with mock.patch.object(
            stats,
            "_get_user_emails",
            new=mock.AsyncMock(return_value=["one@example.com"]),
        ), mock.patch(
            "github_stats.shutil.which", return_value="/usr/bin/git"
        ), mock.patch(
            "github_stats.asyncio.to_thread", side_effect=_run_immediately
        ), mock.patch(
            "github_stats.subprocess.run"
        ) as run_mock:
            run_mock.side_effect = [
                subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="1\t1\tfoo.py\n",
                    stderr="",
                ),
            ]

            result = await stats._get_lines_changed_from_git("owner/repo")

        self.assertEqual(result, (1, 1))
        clone_command = run_mock.call_args_list[0].args[0]
        self.assertIn("https://octocat:token@github.com/owner/repo.git", clone_command)


if __name__ == "__main__":
    unittest.main()
