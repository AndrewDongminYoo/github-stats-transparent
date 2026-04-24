# github-stats-transparent

[한국어 README](README-KR.md)

Transparent GitHub stats cards, with GitHub Actions pushing generated files to `output` in the default setup and local generation to `generated/` also supported.

This fork started from `rahul-jha98/github-stats-transparent`, but it now focuses on fixing the longstanding `Lines of code changed` problem by reimplementing the relevant `jstrieb/github-stats` Zig behavior in Python.

## What This Project Does

This repository generates transparent SVG cards for GitHub profile stats:

- an overview card with stars, forks, contributions, repositories, views, and `Lines of code changed`
- a language card that summarizes language usage across the collected repositories

In the default setup, GitHub Actions generates the cards and pushes them to the `output` branch under `generated/`, so they can be embedded in a profile README or any other markdown page. You can also run the generator locally, which writes the same files to the local `generated/` directory.

## Why This Fork Exists

The original transparent fork kept the transparent presentation layer, which was useful, but it also inherited the older Python implementation's long-running `Lines of code changed` accuracy issue.

That issue mattered because the overview card exposed a number that often dropped to zero or undercounted work for repositories where GitHub's repository stats API did not return usable contributor data in time.

This fork exists to keep the transparent cards while correcting that behavior in Python instead of requiring a separate Zig implementation.

## What Was Wrong in the Older Transparent Python Fork

The older Python transparent fork relied too heavily on the GitHub REST contributor stats endpoint:

- `/repos/{owner}/{repo}/stats/contributors` can return `202 Accepted` while GitHub is still computing repository statistics
- large or busy repositories can keep returning `202` long enough that the old behavior effectively failed for `Lines of code changed`
- when the API did not return usable data, the Python implementation had no equivalent of the more resilient upstream Zig recovery path

In practice, that made `Lines of code changed` the least trustworthy number on the card.

## How This Fork Fixes `Lines of code changed`

This fork ports the relevant recovery behavior from `jstrieb/github-stats` into Python:

1. It performs short random retries when the repository stats endpoint returns `202 Accepted`.
2. If the stats API still does not return usable data, or it responds with retryable rate-limit style failures such as `403` or `429`, it falls back to a git-based calculation.
3. The git fallback clones the repository in a lightweight bare form and runs `git log --numstat`, matching commits by the authenticated user's contributor email addresses.
4. If the token cannot return email addresses, the fallback uses the GitHub noreply address for the account as a last resort.

This is the core fix in the fork: the transparent Python version now follows the same general strategy that made the upstream Zig implementation more reliable for `Lines of code changed`.

The workflow also prints a sanitized one-line execution summary for this feature in this shape:

`Lines changed sources: API X | git fallback Y | failed Z`

That keeps the logs useful without dumping per-repository failure details into the workflow output.

## Setup

### GitHub Actions

1. Create a personal access token.
2. Recommended scopes:
   - `read:user`
   - `repo` if you want private-repository access
   - `user:email` if you want the git fallback to match against your full email list
3. Add the token to your repository secrets as `ACCESS_TOKEN`.
4. Optionally add any of the configuration secrets documented below.
5. Run the `Generate Stats Images` workflow manually once, or let the scheduled run generate the cards automatically.
6. Use the files published to the `output` branch under `generated/`.

### Local Execution

1. Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Run the generator with your token. `GITHUB_ACTOR` is optional locally; if it is unset, the script resolves the login from the authenticated viewer:

```bash
ACCESS_TOKEN=your_token_here python3 generate_images.py
```

For local execution, `git` must also be available because the `Lines of code changed` fallback depends on git history when the stats API is not sufficient.

## Token Scopes

This fork works best with a personal access token, but not every scope is strictly required in every setup.

- `read:user` is the recommended baseline for user-level GitHub profile data
- `repo` is needed if you want to include private repositories and their statistics
- `user:email` improves git fallback matching because the script can query your contributor email list, but the code can still fall back to your GitHub noreply address if `/user/emails` is unavailable

The script can also fall back to `GITHUB_TOKEN` if `ACCESS_TOKEN` is missing, but the most reliable documented setup for this fork remains a personal access token.

## Configuration Options

| Variable                 | Required                              | Description                                                                                                  |
| ------------------------ | ------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `ACCESS_TOKEN`           | Recommended for reliable use          | Personal access token used for API requests and git fallback authentication.                                 |
| `EXCLUDED`               | No                                    | Comma-separated repository names to exclude from stats collection.                                           |
| `EXCLUDED_LANGS`         | No                                    | Comma-separated language names to exclude from the language card.                                            |
| `COUNT_STATS_FROM_FORKS` | No                                    | Any non-empty value enables the broader repository set used by this fork's existing stats collection flow.   |
| `GITHUB_ACTOR`           | Provided by Actions, optional locally | GitHub login override for local runs. If unset, the script resolves the login from the authenticated viewer. |

## Limitations and Expected Behavior

- `Lines of code changed` is more reliable than the older transparent Python fork, but it still depends on GitHub API availability and repository clone access.
- Repositories that keep failing API and git fallback processing are counted in the sanitized summary as `failed` and contribute `0` to the final total.
- If your token cannot return email addresses, the fallback uses your GitHub noreply address, which can undercount commits authored with a different email.
- The `views` stat only reflects the GitHub traffic API window, which is limited to recent views rather than all-time views.
- Large accounts can take longer to process because retries and git fallback both add work by design.

## Contributing

Issues and pull requests are welcome.

Especially useful contributions include:

- stats accuracy improvements
- runtime or API efficiency improvements
- documentation improvements
- compatibility fixes for GitHub API behavior changes

If you find another case where `Lines of code changed` is still inaccurate, open an issue with reproduction details. If you already know the fix, send a pull request.
