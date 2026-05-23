from pathlib import Path


def test_demo_upload_page_has_extension_surface_marker() -> None:
    html = Path("demo/upload_page.html").read_text(encoding="utf-8")

    assert 'data-contextguard-surface="demo_upload"' in html


def test_demo_upload_page_has_paste_and_file_targets() -> None:
    html = Path("demo/upload_page.html").read_text(encoding="utf-8")

    assert 'id="demo-paste-target"' in html
    assert "<textarea" in html
    assert 'id="demo-file-input"' in html
    assert 'type="file"' in html


def test_demo_upload_page_mentions_all_demo_cases() -> None:
    html = Path("demo/upload_page.html").read_text(encoding="utf-8")

    assert "Case A" in html
    assert "Case B" in html
    assert "Case C" in html


def test_demo_upload_page_uses_real_newlines_for_case_b_sample() -> None:
    html = Path("demo/upload_page.html").read_text(encoding="utf-8")

    assert 'join("\\\\n")' not in html
    assert 'join("\\n")' in html
