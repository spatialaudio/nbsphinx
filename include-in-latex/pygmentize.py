#!/usr/bin/env python3
from pathlib import Path

from sphinx import highlighting


def pygmentize(source, destination, lang=None):
    source = Path(source)
    destination = Path(destination)
    if lang is None:
        lang = source.suffix[1:]
    code = source.read_text()
    highlighter = highlighting.PygmentsBridge(
        'latex', latex_engine='lualatex')
    hlcode = highlighter.highlight_block(code, lang)
    hlcode = hlcode.replace(r'\begin{Verbatim}', r'\begin{sphinxVerbatim}')
    hlcode = hlcode.replace(r'\end{Verbatim}', r'\end{sphinxVerbatim}')
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(hlcode)


if __name__ == '__main__':
    pygmentize('pygmentize.py', 'pygmentize.py.tex')
    pygmentize('latexmkrc', 'latexmkrc.tex', lang='perl')
