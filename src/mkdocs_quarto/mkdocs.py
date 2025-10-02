from pathlib import Path
import tempfile
import quarto
from mkdocs.plugins import BasePlugin
from mkdocs.config.base import Config
from mkdocs.config import config_options
from mkdocs.structure.files import Files, File
from mkdocs.structure.pages import Page
import os
import posixpath
import shutil
import subprocess


class QuartoPluginConfig(Config):
    foo = config_options.Type(str, default="a default value")


class QuartoPlugin(BasePlugin[QuartoPluginConfig]):
    def on_files(self, files: Files, config):
        for file in files:
            if _is_quarto_page(file.src_uri):
                file.dest_uri = Path(file.dest_uri).stem + ".html"
                file.is_documentation_page = lambda: True
        return files

    def on_page_read_source(self, page: Page, config) -> str:
        if page.file.src_uri.endswith(".ipynb"):
            return _quarto_convert(page.file.abs_src_path)
        else:
            return None

    def on_page_markdown(self, markdown: str, page: Page, config, files: Files) -> str:
        if not _is_quarto_page(page.file.src_uri):
            return markdown

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_path = tmpdir_path / (posixpath.basename(page.file.src_uri) + ".qmd")
            output_path = tmpdir_path / Path(page.file.name).stem

            print(markdown)

            input_path.write_text(markdown, encoding="utf-8", newline="\n")

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

            markdown = output_path.read_text(encoding="utf-8")

            # quarto may produce extra figures, etc within the tmpdir
            # we must copy and add those files to the mkdocs files collection
            for item in tmpdir_path.rglob("*"):
                if item.is_file() and item != input_path and item != output_path:
                    relative_path = item.relative_to(tmpdir_path)
                    destination = Path(config["site_dir"]) / relative_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(item.read_bytes())

                    # This is a bit hacky since we already copied the files to the site_dir.
                    # But makes the warnings about missing links disapperar.
                    files.append(
                        File(
                            src_dir=config["site_dir"],
                            path=relative_path,
                            dest_dir=config["site_dir"],
                            use_directory_urls=config["use_directory_urls"],
                        )
                    )

        return markdown


def _is_quarto_page(uri: str) -> bool:
    return uri.endswith(".qmd") or uri.endswith(".ipynb")


def _quarto_convert(src_uri: str) -> str:
    """
    Copies a quarto file to a temporary location and then
    converts it to markdown using quarto convert CLI.
    Returns the converted markdown as a string.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / posixpath.basename(src_uri)
        output_path = tmpdir_path / (Path(src_uri).stem + ".md")

        shutil.copy(src_uri, input_path)

        previous_cwd = Path.cwd()
        try:
            os.chdir(tmpdir_path)

            args = ["convert", input_path.name, "--output", output_path.name]
            process = subprocess.Popen([quarto.quarto.find_quarto()] + args)
            process.wait()
        finally:
            os.chdir(previous_cwd)

        markdown = output_path.read_text(encoding="utf-8")
        print(markdown)
        return markdown
