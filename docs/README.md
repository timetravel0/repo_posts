---
layout: default
title: Link Archive
---

<div align="center">

# Link Archive

[![Website](https://img.shields.io/website?url=https%3A%2F%2Ftimetravel0.github.io%2Frepo_posts%2F&label=site&style=for-the-badge)](https://timetravel0.github.io/repo_posts/)
[![RSS](https://img.shields.io/badge/RSS-feed-orange?logo=rss&style=for-the-badge)](https://timetravel0.github.io/repo_posts/feed.xml)
[![Status](https://img.shields.io/badge/Status-page-blue?style=for-the-badge)](https://timetravel0.github.io/repo_posts/status.html)
[![RSS Smoke](https://img.shields.io/github/actions/workflow/status/timetravel0/repo_posts/rss-smoke.yml?branch=main&label=RSS%20smoke&style=for-the-badge)](https://github.com/timetravel0/repo_posts/actions/workflows/rss-smoke.yml)
[![Related Data](https://img.shields.io/github/actions/workflow/status/timetravel0/repo_posts/generate-related-min.yml?branch=main&label=Related%20data&style=for-the-badge)](https://github.com/timetravel0/repo_posts/actions/workflows/generate-related-min.yml)
[![Pages](https://img.shields.io/github/deployments/timetravel0/repo_posts/github-pages?label=Pages&style=for-the-badge)](https://github.com/timetravel0/repo_posts/deployments/activity_log?environment=github-pages)
[![Feed 200](https://img.shields.io/website?url=https%3A%2F%2Ftimetravel0.github.io%2Frepo_posts%2Ffeed.xml&label=feed%20200&style=for-the-badge)](https://timetravel0.github.io/repo_posts/feed.xml)
[![License](https://img.shields.io/github/license/timetravel0/repo_posts?style=for-the-badge)](../LICENSE)

</div>

A searchable collection of public web links, automatically updated through the
**Add links** GitHub Actions workflow.

## Licensing
- Code and configuration in this repository are MIT licensed (see [LICENSE](../LICENSE)).
- Third-party text snippets in `docs/_posts/` are not covered by MIT and remain
  the property of their respective owners. See [CONTENT-LICENSE](../CONTENT-LICENSE.md).

## Latest Links

{% for post in site.posts %}
<article class="post">
  <p class="post-meta">{{ post.date | date: "%Y-%m-%d" }}</p>
  {{ post.content }}
  <h4><a href="{{ post.url | relative_url }}"></a></h4>
  <hr>
</article>
{% endfor %}

## About

This site archives useful public links. Each post includes:
- Source title and link
- Brief description
- Direct link to the source

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contribution Guidelines

We don't accept repository suggestions via Issues/PRs. The site is curated automatically. Please use issues only for site bugs and improvements.

If you want to propose a site/infrastructure change, open a focused issue with a clear description.

<!-- CI trigger: touch README to run generate-related and smoke tests -->
