import pytest
import asyncio

from src.utils.file_utils import (
    parse_html_pages,
    extract_html_content_async,
    extract_layout_properties_async,
    find_and_duplicate_nav_line,
    write_nav_line,
    remove_nav_line_by_href,
)


def test_parse_html_pages_various_patterns():
    htmls = [
        "/some/path/30_0_adt.html",
        "/another/dir/12_adt.html",
        "/weird/name/index.html",
    ]
    mapping = asyncio.run(parse_html_pages(htmls))

    assert mapping["/some/path/30_0_adt.html"] == "page 29.1"
    assert mapping["/another/dir/12_adt.html"] == "page 11"
    assert mapping["/weird/name/index.html"] == "page 0"


@pytest.mark.asyncio
async def test_extract_html_content_async_translations():
    html = (
        '<div>'
        '  <p data-id="t1">Orig</p>'
        '  <span data-aria-id="a1">X</span>'
        '  <input data-placeholder-id="p1" />'
        '  <script>var a=1;</script>'
        '</div>'
    )
    translations = {"t1": "Hello", "a1": "World", "p1": "Type here"}
    extracted = await extract_html_content_async(html, translations)

    # Should collect three entries with translated values
    assert {"t1": "Hello"} in extracted
    assert {"a1": "World"} in extracted
    assert {"p1": "Type here"} in extracted


@pytest.mark.asyncio
async def test_extract_layout_properties_async_structure():
    html = (
        '<div class="outer" style="margin:0">'
        '  some text'
        '  <section class="inner" style="padding:4px">'
        '    <p>child</p>'
        "  </section>"
        "</div>"
    )

    cleaned, elements = await extract_layout_properties_async(
        html,
        include_element_type=True,
        include_dimensions=True,
        include_classes=True,
        include_styles=True,
        include_position=True,
    )

    assert isinstance(cleaned, str)
    assert isinstance(elements, list)
    # There should be a root [document] element and also a div and section captured
    assert elements[0].get("tag") in {"[document]", None}
    div_el = next((el for el in elements if el.get("tag") == "div"), None)
    assert div_el is not None
    assert "classes" in div_el and "outer" in div_el["classes"]
    assert "styles" in div_el and div_el["styles"].get("margin") == "0"
    assert any(el.get("tag") == "section" for el in elements)


def test_nav_line_helpers():
    nav = (
        '<nav>\n'
        '  <ul>\n'
        '    <li><a href="los_biomas.html">Los biomas</a></li>\n'
        '  </ul>\n'
        '</nav>'
    )
    new_line = asyncio.run(
        find_and_duplicate_nav_line(nav, "los_biomas.html", "new_file.html")
    )
    assert 'href="new_file.html"' in new_line

    updated = asyncio.run(write_nav_line(nav, new_line))
    assert 'href="new_file.html"' in updated

    removed = asyncio.run(remove_nav_line_by_href(updated, "los_biomas.html"))
    assert 'href="los_biomas.html"' not in removed
