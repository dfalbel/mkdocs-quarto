from __future__ import annotations

from pathlib import Path
import os
import tempfile

import quarto
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class QuartoExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.preprocessors.register(QuartoPreprocessor(md), "quarto_preprocessor", 100)


class QuartoPreprocessor(Preprocessor):
    def run(self, lines: list[str]) -> list[str]:
        return quarto_render_markdown(lines)


def quarto_render_markdown(md: list[str]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / "input.qmd"
        output_path = tmpdir_path / "output.md"

        with input_path.open("w", encoding="utf-8", newline="") as input_file:
            for line in md:
                input_file.write(line)
                if not line.endswith("\n"):
                    input_file.write("\n")

        previous_cwd = Path.cwd()
        try:
            os.chdir(tmpdir_path)
            quarto.render(
                input_path.name,
                output_format="gfm",
                output_file=output_path.name,
            )
        finally:
            os.chdir(previous_cwd)

        rendered_text = output_path.read_text(encoding="utf-8")
        return rendered_text.splitlines()
