from pathlib import Path

import docutils
import sphinx

original_conf_py = Path(__file__).resolve().parent.parent / 'doc' / 'conf.py'
locals().update(sphinx.config.eval_config_file(str(original_conf_py), tags))

templates_path = ['_templates']
html_favicon = None

exclude_patterns = ['_build']

latex_documents = [(
    'index',  # main source file
    'nbsphinx-chapter.tex',  # output file
    '',  # unused
    '',  # unused
    'howto',  # use 'manual' to generate \chapter{}s instead of \section{}s
    True,  # toctree_only. Use True to hide contents of main source file
)]

latex_engine = 'lualatex'

# Additional configuration options can be added here.

###############################################################################
# The rest of this file is for handling the bibliography:

extensions.remove('sphinxcontrib.bibtex')
exclude_patterns.append('references.rst')
suppress_warnings = ['toc.excluded']


def cite_role(macroname):

    def role(name, rawtext, text, lineno, inliner, options=None, content=None):
        latex_code = rf'\{macroname}{{{text}}}'
        return [docutils.nodes.raw('', latex_code, format='latex')], []

    return role


def setup(app):
    app.add_role('cite', cite_role('parencite'))
    app.add_role('cite:t', cite_role('textcite'))
