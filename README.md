<div align="center">

# Link Archive

[![Website](https://img.shields.io/website?url=https%3A%2F%2Ftimetravel0.github.io%2Frepo_posts%2F&label=site&style=for-the-badge)](https://timetravel0.github.io/repo_posts/)
[![RSS](https://img.shields.io/badge/RSS-feed-orange?logo=rss&style=for-the-badge)](https://timetravel0.github.io/repo_posts/feed.xml)
[![Status](https://img.shields.io/badge/Status-page-blue?style=for-the-badge)](https://timetravel0.github.io/repo_posts/status.html)
[![RSS Smoke](https://img.shields.io/github/actions/workflow/status/timetravel0/repo_posts/rss-smoke.yml?branch=main&label=RSS%20smoke&style=for-the-badge)](https://github.com/timetravel0/repo_posts/actions/workflows/rss-smoke.yml)
[![Related Data](https://img.shields.io/github/actions/workflow/status/timetravel0/repo_posts/generate-related-min.yml?branch=main&label=Related%20data&style=for-the-badge)](https://github.com/timetravel0/repo_posts/actions/workflows/generate-related-min.yml)
[![Pages](https://img.shields.io/github/deployments/timetravel0/repo_posts/github-pages?label=Pages&style=for-the-badge)](https://github.com/timetravel0/repo_posts/deployments/activity_log?environment=github-pages)
[![Feed 200](https://img.shields.io/website?url=https%3A%2F%2Ftimetravel0.github.io%2Frepo_posts%2Ffeed.xml&label=feed%20200&style=for-the-badge)](https://timetravel0.github.io/repo_posts/feed.xml)
[![License](https://img.shields.io/github/license/timetravel0/repo_posts?style=for-the-badge)](LICENSE)

</div>

Live site: https://timetravel0.github.io/repo_posts/

- Feed (Atom): https://timetravel0.github.io/repo_posts/feed.xml
- Status: Built via GitHub Pages (workflow in `.github/workflows/Deploy Jekyll site`).

## How things update
- The **Add links** workflow turns submitted URLs into posts and commits them.
- A push changing `docs/_posts/**` refreshes search and semantic data.
- A push changing `docs/**` builds and deploys the site to GitHub Pages.

## What this repo is
A Jekyll site stored under `docs/` using the Minimal theme. Each post represents
an external HTTP(S) link. Existing GitHub repository posts remain compatible,
while new entries can point to any public website.

- Layout override: `docs/_layouts/default.html`.
- Homepage: `docs/index.md` (lists posts, adds anchors, and an RSS link).
- Issue template: `.github/ISSUE_TEMPLATE/bug_report.yml`.

## Add links without editing Markdown

Open **Actions → Add links → Run workflow**, then paste one or more URLs
separated by spaces.
Metadata is read from Open Graph or standard HTML tags and the workflow commits
the generated posts to `main`.

Optional overrides use this format:

```text
https://example.com/page | Custom title | Custom description
```

The same importer can be run locally:

```bash
python tools/add_links.py https://example.com/page https://example.org/another
```

Only public HTTP(S) destinations are accepted. Local, private, credentialed, and
non-web URLs are rejected.

## Contribution policy
Use the owner-only **Add links** workflow to curate links. Issues remain reserved
for site bugs and improvements.

## Deploy
- Trigger: push to `main` builds `docs/` and deploys to Pages.
- Workflow: `.github/workflows/pages-min.yml`.

## Structure
```
repo_posts/
  docs/
    _posts/      # content
    assets/      # CSS, JavaScript and generated search/semantic data
    _layouts/    # layout override
    index.md     # homepage
  .github/
    ISSUE_TEMPLATE/
    workflows/
```

## License
MIT for code/config — see LICENSE.

Content licensing — see CONTENT-LICENSE.md. Third‑party text in `docs/_posts/`
remains the property of its respective owners.

For current coverage stats, see the [Status page](https://timetravel0.github.io/repo_posts/status.html).

## Liquid numeric gotcha (percentages)
Liquid math is integer by default. If you compute a percentage like:

```
{{ s.related_renderable | times: 100 | divided_by: s.posts }}%
```

it truncates to an integer. To get a decimal percentage, make one operand a float:

```
{{ s.related_renderable | times: 100.0 | divided_by: s.posts | round: 1 }}%
```

or:

```
{{ s.related_renderable | times: 1.0 | divided_by: s.posts | times: 100 | round: 1 }}%
```
