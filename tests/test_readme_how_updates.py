from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / 'README.md'


def test_readme_has_how_things_update_section():
    t = README.read_text(encoding='utf-8')
    assert '## How things update' in t
    assert '**Add links** workflow' in t
    assert 'refreshes search and semantic data' in t
    assert 'Status page' in t  # link to status page for coverage stats
