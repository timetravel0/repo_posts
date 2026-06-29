from datetime import datetime, timezone

import pytest

from tools.add_links import (
    LinkError,
    LinkSpec,
    MetadataParser,
    PageMetadata,
    build_post,
    normalize_url,
    parse_specs,
)


def test_normalize_url_accepts_general_web_links_and_removes_fragments():
    assert normalize_url("example.com/article/#section") == "https://example.com/article"
    assert normalize_url("https://EXAMPLE.com/?q=one#part") == "https://example.com/?q=one"


def test_normalize_url_rejects_credentials_and_non_http_protocols():
    with pytest.raises(LinkError):
        normalize_url("ftp://example.com/file")
    with pytest.raises(LinkError):
        normalize_url("https://user:secret@example.com/")


def test_parse_specs_supports_optional_title_and_description():
    specs = parse_specs(["https://example.com/a | Custom title | Custom description"])
    assert specs == [
        LinkSpec("https://example.com/a", "Custom title", "Custom description")
    ]


def test_parse_specs_supports_space_separated_batch():
    specs = parse_specs(["https://example.com/a https://example.org/b"])
    assert [spec.url for spec in specs] == [
        "https://example.com/a",
        "https://example.org/b",
    ]


def test_metadata_parser_reads_open_graph_with_html_fallback():
    parser = MetadataParser()
    parser.feed(
        '<html><head><title>Fallback</title>'
        '<meta property="og:title" content="Open Graph title">'
        '<meta name="description" content="Description"></head></html>'
    )
    assert parser.meta["og:title"] == "Open Graph title"
    assert parser.meta["description"] == "Description"
    assert parser.document_title == "Fallback"


def test_build_post_uses_explicit_generic_link_fields_without_image():
    post = build_post(
        LinkSpec("https://example.com/article"),
        PageMetadata("Example article", "A useful page"),
        datetime(2026, 6, 29, 18, 30, tzinfo=timezone.utc),
    )
    assert 'title: "Example article"' in post
    assert 'external_url: "https://example.com/article"' in post
    assert "source_type: web" in post
    assert 'description: "A useful page"' in post
    assert "# [Example article](<https://example.com/article>)" in post
    assert "image:" not in post
