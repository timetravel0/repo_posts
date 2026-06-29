from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_link_ingestion_workflow_exposes_multiline_input():
    workflow = (ROOT / ".github/workflows/add-links.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "links:" in workflow
    assert "python tools/add_links.py --urls-env LINKS" in workflow
    assert "contents: write" in workflow
    assert "git status --porcelain -- docs/_posts" in workflow


def test_templates_and_feed_have_no_content_images():
    paths = [
        ROOT / "docs/_layouts/default.html",
        ROOT / "docs/_includes/post_card.html",
        ROOT / "docs/_includes/related_item.html",
        ROOT / "docs/feed.xml",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "<img" not in combined
    assert "post.image" not in combined
    assert "page.image" not in combined
    assert "media:thumbnail" not in combined


def test_posts_no_longer_reference_images():
    for post in (ROOT / "docs/_posts").glob("*.md"):
        assert "\nimage:" not in post.read_text(encoding="utf-8", errors="ignore")


def test_image_pipeline_is_removed():
    assert not (ROOT / "tools/generate_image_dims.py").exists()
    assert not (ROOT / "docs/_data/image_dims.json").exists()
    assert not (ROOT / ".github/workflows/image-compress.yml").exists()
