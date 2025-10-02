from markdown import Markdown

from markdown_quarto.extension import QuartoExtension, quarto_render_markdown


def _run_block_processor(*lines: str) -> list[str]:
    markdown = Markdown()
    processor = QuartoBlockProcessor(markdown)
    return processor.run(list(lines))


def test_quarto_render_markdown_basic():
    lines = ["# Title", "", "Body without newline"]
    body_lines = quarto_render_markdown(lines)

    assert "# Title" in body_lines
    assert "Body without newline" in body_lines


def test_quarto_render_markdown_python_chunk():
    lines = [
        "```{python}\n",
        "for number in range(3):\n",
        "    print(number)\n",
        "```\n",
    ]

    body_lines = quarto_render_markdown(lines)

    assert "``` python" in body_lines
    assert "    0" in body_lines
    assert "    1" in body_lines
    assert "    2" in body_lines


def test_markdown_with_quarto_extension_compiles_chunk():
    document = """```{python}
for number in range(3):
    print(number)
```
"""

    markdown = Markdown(extensions=[QuartoExtension(), "fenced_code", "attr_list"])
    html = markdown.convert(document)

    assert '<code class="language-python">for number in range(3):' in html
    assert "<pre><code>0" in html
    for expected in ("0", "1", "2"):
        assert expected in html
