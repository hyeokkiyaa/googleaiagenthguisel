from pathlib import Path


def test_dashboard_page_has_required_operational_regions() -> None:
    html = Path("dashboard/index.html").read_text(encoding="utf-8")

    assert 'id="metric-total"' in html
    assert 'id="metric-block"' in html
    assert 'id="metric-warn"' in html
    assert 'id="incident-list"' in html
    assert 'id="incident-detail"' in html


def test_dashboard_page_has_rule_ai_and_productivity_sections() -> None:
    html = Path("dashboard/index.html").read_text(encoding="utf-8")

    assert 'id="rule-ai-comparison"' in html
    assert 'id="productivity-impact"' in html
    assert 'id="incident-timeline"' in html


def test_dashboard_page_loads_dashboard_core() -> None:
    html = Path("dashboard/index.html").read_text(encoding="utf-8")

    assert '<script src="./dashboard_core.js"></script>' in html
    assert "http://127.0.0.1:8765" in html

