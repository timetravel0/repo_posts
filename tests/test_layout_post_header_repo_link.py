from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / 'docs' / '_layouts' / 'default.html'


def test_layout_post_header_prefers_external_url_with_legacy_fallback():
    html = LAYOUT.read_text(encoding='utf-8')
    assert "page.collection == 'posts'" in html
    assert '_source_url = page.external_url' in html
    assert "_href_parts = _html | split: 'href=\"'" in html
    assert "_source_url = _href_parts[1] | split: '\"' | first" in html
    assert '<a href="{{ _source_url }}" target="_blank" rel="noopener">Visit source</a>' in html
    assert "contains 'github.com'" not in html
