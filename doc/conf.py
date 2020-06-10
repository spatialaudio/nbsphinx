#!/usr/bin/env python3

import os

# Use sphinx-quickstart to create your own conf.py file!
# After that, you have to edit a few things.  See below.

# Select nbsphinx and, if needed, other Sphinx extensions:
extensions = [
    'nbsphinx',
    'sphinx_copybutton',  # for "copy to clipboard" buttons
    'sphinx.ext.mathjax',  # for math equations
    'sphinxcontrib.bibtex',  # for bibliographic references
    'sphinxcontrib.rsvgconverter',  # for SVG->PDF conversion in LaTeX output
    'sphinx_gallery.load_style',  # load CSS for gallery (needs SG >= 0.6)
    'sphinx_last_updated_by_git',  # get "last updated" from Git
]

# Default language for syntax highlighting in reST and Markdown cells:
highlight_language = 'none'

# Don't add .txt suffix to source files:
html_sourcelink_suffix = ''

# List of arguments to be passed to the kernel that executes the notebooks:
nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg', 'pdf'}",
    "--InlineBackend.rc={'figure.dpi': 96}",
]

# Environment variables to be passed to the kernel:
os.environ['MY_DUMMY_VARIABLE'] = 'Hello from conf.py!'

nbsphinx_thumbnails = {
    'gallery/thumbnail-from-conf-py': 'gallery/a-local-file.png',
    'gallery/*-rst': '_static/copy-button.svg',
}

# This is processed by Jinja2 and inserted before each notebook
nbsphinx_prolog = r"""
{% set docname = 'doc/' + env.doc2path(env.docname, base=None) %}

.. raw:: html

    <div class="admonition note">
      This page was generated from
      <a class="reference external" href="https://github.com/spatialaudio/nbsphinx/blob/{{ env.config.release|e }}/{{ docname|e }}">{{ docname|e }}</a>.
      Interactive online version:
      <span style="white-space: nowrap;"><a href="https://mybinder.org/v2/gh/spatialaudio/nbsphinx/{{ env.config.release|e }}?filepath={{ docname|e }}"><img alt="Binder badge" src="https://mybinder.org/badge_logo.svg" style="vertical-align:text-bottom"></a>.</span>
      <script>
        if (document.location.host) {
          $(document.currentScript).replaceWith(
            '<a class="reference external" ' +
            'href="https://nbviewer.jupyter.org/url' +
            (window.location.protocol == 'https:' ? 's/' : '/') +
            window.location.host +
            window.location.pathname.slice(0, -4) +
            'ipynb">View in <em>nbviewer</em></a>.'
          );
        }
      </script>
    </div>

.. raw:: latex

    \nbsphinxstartnotebook{\scriptsize\noindent\strut
    \textcolor{gray}{The following section was generated from
    \sphinxcode{\sphinxupquote{\strut {{ docname | escape_latex }}}} \dotfill}}
"""

# This is processed by Jinja2 and inserted after each notebook
nbsphinx_epilog = r"""
{% set docname = 'doc/' + env.doc2path(env.docname, base=None) %}
.. raw:: latex

    \nbsphinxstopnotebook{\scriptsize\noindent\strut
    \textcolor{gray}{\dotfill\ \sphinxcode{\sphinxupquote{\strut
    {{ docname | escape_latex }}}} ends here.}}
"""

mathjax_config = {
    'TeX': {'equationNumbers': {'autoNumber': 'AMS', 'useLabelIds': True}},
}

# Additional files needed for generating LaTeX/PDF output:
latex_additional_files = ['references.bib']

# Support for notebook formats other than .ipynb
nbsphinx_custom_formats = {
    '.pct.py': ['jupytext.reads', {'fmt': 'py:percent'}],
}

# -- The settings below this line are not specific to nbsphinx ------------

master_doc = 'index'

project = 'nbsphinx'
author = 'Matthias Geier'
copyright = '2020, ' + author
html_show_copyright = False

linkcheck_ignore = [
    r'http://localhost:\d+/',
    'https://github.com/spatialaudio/nbsphinx/compare/',
]

# -- Get version information and date from Git ----------------------------

try:
    from subprocess import check_output
    release = check_output(['git', 'describe', '--tags', '--always'])
    release = release.decode().strip()
    today = check_output(['git', 'show', '-s', '--format=%ad', '--date=short'])
    today = today.decode().strip()
except Exception:
    release = '<unknown>'
    today = '<unknown date>'

# -- Options for HTML output ----------------------------------------------

html_title = project + ' version ' + release

# -- Options for LaTeX output ---------------------------------------------

# See https://www.sphinx-doc.org/en/master/latex.html
latex_elements = {
    'papersize': 'a4paper',
    'printindex': '',
    'sphinxsetup': r"""
        %verbatimwithframe=false,
        %verbatimwrapslines=false,
        %verbatimhintsturnover=false,
        VerbatimColor={HTML}{F5F5F5},
        VerbatimBorderColor={HTML}{E0E0E0},
        noteBorderColor={HTML}{E0E0E0},
        noteborder=1.5pt,
        warningBorderColor={HTML}{E0E0E0},
        warningborder=1.5pt,
        warningBgColor={HTML}{FBFBFB},
    """,
    'preamble': r"""
\usepackage[sc,osf]{mathpazo}
\linespread{1.05}  % see http://www.tug.dk/FontCatalogue/urwpalladio/
\renewcommand{\sfdefault}{pplj}  % Palatino instead of sans serif
\IfFileExists{zlmtt.sty}{
    \usepackage[light,scaled=1.05]{zlmtt}  % light typewriter font from lmodern
}{
    \renewcommand{\ttdefault}{lmtt}  % typewriter font from lmodern
}
\usepackage{booktabs}  % for Pandas dataframes
""",
}

latex_documents = [
    (master_doc, 'nbsphinx.tex', project, author, 'howto'),
]

latex_show_urls = 'footnote'
latex_show_pagerefs = True

# -- Options for EPUB output ----------------------------------------------

# These are just defined to avoid Sphinx warnings related to EPUB:
version = release
suppress_warnings = ['epub.unknown_project_files']
