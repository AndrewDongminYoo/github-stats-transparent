import sys
import types
import unittest
from unittest import mock

sys.modules.setdefault(
    "aiohttp",
    types.SimpleNamespace(
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

import generate_images  # noqa: E402


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

    @property
    async def lines_changed_failure_summary_text(self):
        return None


class _FailureStats(_FakeStats):
    @property
    async def lines_changed_failure_summary_text(self):
        return "Lines changed failure causes: git unavailable 1 | clone failed 1"


class GenerateImagesTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_overview_reads_lines_changed_once(self):
        stats = _FakeStats()
        template = (
            "{{ name }} {{ stars }} {{ forks }} {{ contributions }} "
            "{{ lines_changed }} {{ views }} {{ repos }}"
        )

        with mock.patch(
            "builtins.open", mock.mock_open(read_data=template)
        ), mock.patch("generate_images.generate_output_folder"):
            await generate_images.generate_overview(stats)

        self.assertEqual(stats.lines_changed_calls, 1)

    async def test_print_lines_changed_summary_emits_one_sanitized_line(self):
        stats = _FakeStats()

        with mock.patch("builtins.print") as print_mock:
            await generate_images.print_lines_changed_summary(stats)

        print_mock.assert_called_once_with(
            "Lines changed sources: API 2 | git fallback 1 | failed 0"
        )

    async def test_print_lines_changed_summary_emits_optional_failure_line(self):
        stats = _FailureStats()

        with mock.patch("builtins.print") as print_mock:
            await generate_images.print_lines_changed_summary(stats)

        self.assertEqual(
            print_mock.call_args_list,
            [
                mock.call("Lines changed sources: API 2 | git fallback 1 | failed 0"),
                mock.call(
                    "Lines changed failure causes: git unavailable 1 | clone failed 1"
                ),
            ],
        )
