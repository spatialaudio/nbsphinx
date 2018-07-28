# Copyright (c) 2015-2018 Matthias Geier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Jupyter Notebook Tools for Sphinx.

http://nbsphinx.readthedocs.io/

"""
__version__ = '0.3.4'

import copy
import json
import os
import re
import subprocess
try:
    from urllib.parse import unquote  # Python 3.x
except ImportError:
    from urllib2 import unquote  # Python 2.x

import docutils
from docutils.parsers import rst
import jinja2
import nbconvert
import nbformat
import sphinx
import sphinx.errors
import traitlets

_ipynbversion = 4

# See nbconvert/exporters/html.py:
DISPLAY_DATA_PRIORITY_HTML = (
    'application/javascript',
    'application/vnd.jupyter.widget-view+json',
    'application/vnd.jupyter.widget-state+json',
    'text/html',
    'text/markdown',
    'image/svg+xml',
    'text/latex',
    'image/png',
    'image/jpeg',
    'text/plain',
)
# See nbconvert/exporters/latex.py:
DISPLAY_DATA_PRIORITY_LATEX = (
    'text/latex',
    'application/pdf',
    'image/png',
    'image/jpeg',
    'image/svg+xml',
    'text/markdown',
    'text/plain',
)

RST_TEMPLATE = """
{% extends 'rst.tpl' %}


{% macro insert_empty_lines(text) %}
{%- set before, after = text | get_empty_lines %}
{%- if before %}
    :empty-lines-before: {{ before }}
{%- endif %}
{%- if after %}
    :empty-lines-after: {{ after }}
{%- endif %}
{%- endmacro %}


{% block any_cell %}
{%- if cell.metadata.nbsphinx != 'hidden' %}
{{ super() }}
{% endif %}
{%- endblock any_cell %}


{% block input -%}
.. nbinput:: {% if cell.metadata.magics_language -%}
{{ cell.metadata.magics_language }}
{%- elif nb.metadata.language_info -%}
{{ nb.metadata.language_info.pygments_lexer or nb.metadata.language_info.name }}
{%- else -%}
{{ resources.codecell_lexer }}
{%- endif -%}
{{ insert_empty_lines(cell.source) }}
{%- if cell.execution_count %}
    :execution-count: {{ cell.execution_count }}
{%- endif %}
{%- if not cell.outputs %}
    :no-output:
{%- endif %}
{%- if cell.source.strip() %}

{{ cell.source.strip('\n') | indent }}
{%- endif %}
{% endblock input %}


{% macro insert_nboutput(datatype, output, cell) -%}
.. nboutput::
{%- if datatype == 'text/plain' %}{# nothing #}
{%- else %} rst
{%- endif %}
{%- if output.output_type == 'execute_result' and cell.execution_count %}
    :execution-count: {{ cell.execution_count }}
{%- endif %}
{%- if output != cell.outputs[-1] %}
    :more-to-come:
{%- endif %}
{%- if output.name == 'stderr' %}
    :class: stderr
{%- endif %}
{%- if datatype == 'text/plain' -%}
{{ insert_empty_lines(output.data[datatype]) }}

{{ output.data[datatype].strip(\n) | indent }}
{%- elif datatype in ['image/svg+xml', 'image/png', 'image/jpeg', 'application/pdf'] %}

    .. image:: {{ output.metadata.filenames[datatype] | posix_path }}
{%- elif datatype in ['text/markdown'] %}

{{ output.data['text/markdown'] | markdown2rst | indent }}
{%- elif datatype in ['text/latex'] %}

    .. math::
        :nowrap:

{{ output.data['text/latex'] | indent | indent }}
{%- elif datatype == 'text/html' %}

    .. raw:: html

{{ output.data['text/html'] | indent | indent }}
{%- elif datatype == 'application/javascript' %}

    .. raw:: html

        <div></div>
        <script type="text/javascript">
        var element = document.currentScript.previousSibling.previousSibling;
{{ output.data['application/javascript'] | indent | indent }}
        </script>
{%- elif datatype.startswith('application/vnd.jupyter') and datatype.endswith('+json') %}

    .. raw:: html

        <script type="{{ datatype }}">{{ output.data[datatype] | json_dumps }}</script>
{%- elif datatype == 'ansi' %}

    .. rst-class:: highlight

    .. raw:: html

        <pre>
{{ output.data[datatype] | ansi2html | indent | indent }}
        </pre>

    .. raw:: latex

        %
        \\begin{OriginalVerbatim}[commandchars=\\\\\\{\\}]
{{ output.data[datatype] | escape_latex | ansi2latex | indent | indent }}
        \\end{OriginalVerbatim}
        % The following \\relax is needed to avoid problems with adjacent ANSI
        % cells and some other stuff (e.g. bullet lists) following ANSI cells.
        % See https://github.com/sphinx-doc/sphinx/issues/3594
        \\relax
{% else %}

    .. nbwarning:: Data type cannot be displayed: {{ datatype }}
{%- endif %}
{% endmacro %}


{% block nboutput -%}
{%- set html_datatype, latex_datatype = output | get_output_type %}
{%- if html_datatype == latex_datatype %}
{{ insert_nboutput(html_datatype, output, cell) }}
{%- else %}
.. only:: html

{{ insert_nboutput(html_datatype, output, cell) | indent }}
.. only:: latex

{{ insert_nboutput(latex_datatype, output, cell) | indent }}
{%- endif %}
{% endblock nboutput %}


{% block execute_result %}{{ self.nboutput() }}{% endblock execute_result %}
{% block display_data %}{{ self.nboutput() }}{% endblock display_data %}
{% block stream %}{{ self.nboutput() }}{% endblock stream %}
{% block error %}{{ self.nboutput() }}{% endblock error %}


{% block markdowncell %}
{%- if 'nbsphinx-toctree' in cell.metadata %}
{{ cell | extract_toctree }}
{%- else %}
{{ super() }}
{% endif %}
{% endblock markdowncell %}


{% block rawcell %}
{%- set raw_mimetype = cell.metadata.get('raw_mimetype', '').lower() %}
{%- if raw_mimetype == '' %}
.. raw:: html

{{ cell.source | indent }}

.. raw:: latex

{{ cell.source | indent }}
{%- elif raw_mimetype == 'text/html' %}
.. raw:: html

{{ cell.source | indent }}
{%- elif raw_mimetype == 'text/latex' %}
.. raw:: latex

{{ cell.source | indent }}
{%- elif raw_mimetype == 'text/markdown' %}
{{ cell.source | markdown2rst }}
{%- elif raw_mimetype == 'text/restructuredtext' %}
{{ cell.source }}
{% endif %}
{% endblock rawcell %}


{% block footer %}

{% if 'application/vnd.jupyter.widget-state+json' in nb.metadata.widgets %}

.. raw:: html

    <script type="application/vnd.jupyter.widget-state+json">
    {{ nb.metadata.widgets['application/vnd.jupyter.widget-state+json'] | json_dumps }}
    </script>
{% endif %}
{{ super() }}
{% endblock footer %}
"""


LATEX_PREAMBLE = r"""
% Jupyter Notebook prompt colors
\definecolor{nbsphinxin}{HTML}{303F9F}
\definecolor{nbsphinxout}{HTML}{D84315}
% ANSI colors for output streams and traceback highlighting
\definecolor{ansi-black}{HTML}{3E424D}
\definecolor{ansi-black-intense}{HTML}{282C36}
\definecolor{ansi-red}{HTML}{E75C58}
\definecolor{ansi-red-intense}{HTML}{B22B31}
\definecolor{ansi-green}{HTML}{00A250}
\definecolor{ansi-green-intense}{HTML}{007427}
\definecolor{ansi-yellow}{HTML}{DDB62B}
\definecolor{ansi-yellow-intense}{HTML}{B27D12}
\definecolor{ansi-blue}{HTML}{208FFB}
\definecolor{ansi-blue-intense}{HTML}{0065CA}
\definecolor{ansi-magenta}{HTML}{D160C4}
\definecolor{ansi-magenta-intense}{HTML}{A03196}
\definecolor{ansi-cyan}{HTML}{60C6C8}
\definecolor{ansi-cyan-intense}{HTML}{258F8F}
\definecolor{ansi-white}{HTML}{C5C1B4}
\definecolor{ansi-white-intense}{HTML}{A1A6B2}
\definecolor{ansi-default-inverse-fg}{HTML}{FFFFFF}
\definecolor{ansi-default-inverse-bg}{HTML}{000000}

% Define "notice" environment, which was removed in Sphinx 1.7.
% At some point, "notice" should be replaced by "sphinxadmonition",
% which is available since Sphinx 1.5.
\makeatletter
\@ifundefined{notice}{%
\newenvironment{notice}{\begin{sphinxadmonition}}{\end{sphinxadmonition}}%
}{}
\makeatother
"""


CSS_STRING = """
/* CSS for nbsphinx extension */

/* remove conflicting styling from Sphinx themes */
div.nbinput,
div.nbinput div.prompt,
div.nbinput div.input_area,
div.nbinput div[class*=highlight],
div.nbinput div[class*=highlight] pre,
div.nboutput,
div.nbinput div.prompt,
div.nbinput div.output_area,
div.nboutput div[class*=highlight],
div.nboutput div[class*=highlight] pre {
    background: none;
    border: none;
    padding: 0 0;
    margin: 0;
    box-shadow: none;
}

/* avoid gaps between output lines */
div.nboutput div[class*=highlight] pre {
    line-height: normal;
}

/* input/output containers */
div.nbinput,
div.nboutput {
    display: -webkit-flex;
    display: flex;
    align-items: flex-start;
    margin: 0;
    width: 100%%;
}
@media (max-width: %(nbsphinx_responsive_width)s) {
    div.nbinput,
    div.nboutput {
        flex-direction: column;
    }
}

/* input container */
div.nbinput {
    padding-top: 5px;
}

/* last container */
div.nblast {
    padding-bottom: 5px;
}

/* input prompt */
div.nbinput div.prompt pre {
    color: #303F9F;
}

/* output prompt */
div.nboutput div.prompt pre {
    color: #D84315;
}

/* all prompts */
div.nbinput div.prompt,
div.nboutput div.prompt {
    min-width: %(nbsphinx_prompt_width)s;
    padding-top: 0.4em;
    padding-right: 0.4em;
    text-align: right;
    flex: 0;
}
@media (max-width: %(nbsphinx_responsive_width)s) {
    div.nbinput div.prompt,
    div.nboutput div.prompt {
        text-align: left;
        padding: 0.4em;
    }
    div.nboutput div.prompt.empty {
        padding: 0;
    }
}

/* disable scrollbars on prompts */
div.nbinput div.prompt pre,
div.nboutput div.prompt pre {
    overflow: hidden;
}

/* input/output area */
div.nbinput div.input_area,
div.nboutput div.output_area {
    padding: 0.4em;
    -webkit-flex: 1;
    flex: 1;
    overflow: auto;
}
@media (max-width: %(nbsphinx_responsive_width)s) {
    div.nbinput div.input_area,
    div.nboutput div.output_area {
        width: 100%%;
    }
}

/* input area */
div.nbinput div.input_area {
    border: 1px solid #cfcfcf;
    border-radius: 2px;
    background: #f7f7f7;
}

/* override MathJax center alignment in output cells */
div.nboutput div[class*=MathJax] {
    text-align: left !important;
}

/* override sphinx.ext.pngmath center alignment in output cells */
div.nboutput div.math p {
    text-align: left;
}

/* standard error */
div.nboutput div.output_area.stderr {
    background: #fdd;
}

/* ANSI colors */
.ansi-black-fg { color: #3E424D; }
.ansi-black-bg { background-color: #3E424D; }
.ansi-black-intense-fg { color: #282C36; }
.ansi-black-intense-bg { background-color: #282C36; }
.ansi-red-fg { color: #E75C58; }
.ansi-red-bg { background-color: #E75C58; }
.ansi-red-intense-fg { color: #B22B31; }
.ansi-red-intense-bg { background-color: #B22B31; }
.ansi-green-fg { color: #00A250; }
.ansi-green-bg { background-color: #00A250; }
.ansi-green-intense-fg { color: #007427; }
.ansi-green-intense-bg { background-color: #007427; }
.ansi-yellow-fg { color: #DDB62B; }
.ansi-yellow-bg { background-color: #DDB62B; }
.ansi-yellow-intense-fg { color: #B27D12; }
.ansi-yellow-intense-bg { background-color: #B27D12; }
.ansi-blue-fg { color: #208FFB; }
.ansi-blue-bg { background-color: #208FFB; }
.ansi-blue-intense-fg { color: #0065CA; }
.ansi-blue-intense-bg { background-color: #0065CA; }
.ansi-magenta-fg { color: #D160C4; }
.ansi-magenta-bg { background-color: #D160C4; }
.ansi-magenta-intense-fg { color: #A03196; }
.ansi-magenta-intense-bg { background-color: #A03196; }
.ansi-cyan-fg { color: #60C6C8; }
.ansi-cyan-bg { background-color: #60C6C8; }
.ansi-cyan-intense-fg { color: #258F8F; }
.ansi-cyan-intense-bg { background-color: #258F8F; }
.ansi-white-fg { color: #C5C1B4; }
.ansi-white-bg { background-color: #C5C1B4; }
.ansi-white-intense-fg { color: #A1A6B2; }
.ansi-white-intense-bg { background-color: #A1A6B2; }

.ansi-default-inverse-fg { color: #FFFFFF; }
.ansi-default-inverse-bg { background-color: #000000; }

.ansi-bold { font-weight: bold; }
.ansi-underline { text-decoration: underline; }
"""

CSS_STRING_READTHEDOCS = """
/* CSS overrides for sphinx_rtd_theme */

/* 24px margin */
.nbinput.nblast,
.nboutput.nblast {
    margin-bottom: 19px;  /* padding has already 5px */
}

/* ... except between code cells! */
.nblast + .nbinput {
    margin-top: -19px;
}

.admonition > p:before {
    margin-right: 4px;  /* make room for the exclamation icon */
}
"""

CSS_STRING_CLOUD = """
/* CSS overrides for cloud theme */

/* nicer titles and more space for info and warning logos */

div.admonition p.admonition-title {
    background: rgba(0, 0, 0, .05);
    margin: .5em -1em;
    margin-top: -.5em !important;
    padding: .5em .5em .5em 2.65em;
}

/* indent single paragraph */
div.admonition {
    text-indent: 20px;
}
/* don't indent multiple paragraphs */
div.admonition > p {
    text-indent: 0;
}
/* remove excessive padding */
div.admonition.inline-title p.admonition-title {
    padding-left: .2em;
}
"""


class Exporter(nbconvert.RSTExporter):
    """Convert Jupyter notebooks to reStructuredText.

    Uses nbconvert to convert Jupyter notebooks to a reStructuredText
    string with custom reST directives for input and output cells.

    Notebooks without output cells are automatically executed before
    conversion.

    """

    def __init__(self, execute='auto', kernel_name='', execute_arguments=[],
                 allow_errors=False, timeout=30, codecell_lexer='none'):
        """Initialize the Exporter."""
        self._execute = execute
        self._kernel_name = kernel_name
        self._execute_arguments = execute_arguments
        self._allow_errors = allow_errors
        self._timeout = timeout
        self._codecell_lexer = codecell_lexer
        loader = jinja2.DictLoader({'nbsphinx-rst.tpl': RST_TEMPLATE})
        super(Exporter, self).__init__(
            template_file='nbsphinx-rst.tpl', extra_loaders=[loader],
            config=traitlets.config.Config(
                {'HighlightMagicsPreprocessor': {'enabled': True}}),
            filters={
                'convert_pandoc': convert_pandoc,
                'markdown2rst': markdown2rst,
                'get_empty_lines': _get_empty_lines,
                'extract_toctree': _extract_toctree,
                'get_output_type': _get_output_type,
                'json_dumps': json.dumps,
            })

    def from_notebook_node(self, nb, resources=None, **kw):
        nb = copy.deepcopy(nb)
        if resources is None:
            resources = {}
        else:
            resources = copy.deepcopy(resources)
        # Set default codecell lexer
        resources['codecell_lexer'] = self._codecell_lexer

        nbsphinx_metadata = nb.metadata.get('nbsphinx', {})

        execute = nbsphinx_metadata.get('execute', self._execute)
        if execute not in ('always', 'never', 'auto'):
            raise ValueError('invalid execute option: {!r}'.format(execute))
        auto_execute = (
            execute == 'auto' and
            # At least one code cell actually containing source code:
            any(c.source for c in nb.cells if c.cell_type == 'code') and
            # No outputs, not even a prompt number:
            not any(c.get('outputs') or c.get('execution_count')
                    for c in nb.cells if c.cell_type == 'code')
        )
        if auto_execute or execute == 'always':
            allow_errors = nbsphinx_metadata.get(
                'allow_errors', self._allow_errors)
            timeout = nbsphinx_metadata.get('timeout', self._timeout)
            pp = nbconvert.preprocessors.ExecutePreprocessor(
                kernel_name=self._kernel_name,
                extra_arguments=self._execute_arguments,
                allow_errors=allow_errors, timeout=timeout)
            nb, resources = pp.preprocess(nb, resources)

        # Call into RSTExporter
        rststr, resources = super(Exporter, self).from_notebook_node(
            nb, resources, **kw)

        orphan = nbsphinx_metadata.get('orphan', False)
        if orphan is True:
            resources['nbsphinx_orphan'] = True
        elif orphan is not False:
            raise ValueError('invalid orphan option: {!r}'.format(orphan))

        return rststr, resources


class NotebookParser(rst.Parser):
    """Sphinx source parser for Jupyter notebooks.

    Uses nbsphinx.Exporter to convert notebook content to a
    reStructuredText string, which is then parsed by Sphinx's built-in
    reST parser.

    """

    supported = 'jupyter_notebook',

    def get_transforms(self):
        """List of transforms for documents parsed by this parser."""
        return rst.Parser.get_transforms(self) + [
            CreateNotebookSectionAnchors,
            ReplaceAlertDivs,
            CopyLinkedFiles,
        ]

    def parse(self, inputstring, document):
        """Parse *inputstring*, write results to *document*.

        *inputstring* is either the JSON representation of a notebook,
        or a paragraph of text coming from the Sphinx translation
        machinery.

        Note: For now, the translation strings use reST formatting,
        because the NotebookParser uses reST as intermediate
        representation.
        However, there are plans to remove this intermediate step
        (https://github.com/spatialaudio/nbsphinx/issues/36), and after
        that, the translated strings will most likely be parsed as
        CommonMark.

        """
        try:
            nb = nbformat.reads(inputstring, as_version=_ipynbversion)
        except Exception:
            # NB: The use of the RST parser is temporary!
            rst.Parser.parse(self, inputstring, document)
            return
        env = document.settings.env
        srcdir = os.path.dirname(env.doc2path(env.docname))
        auxdir = os.path.join(env.doctreedir, 'nbsphinx')
        sphinx.util.ensuredir(auxdir)

        resources = {}
        # Working directory for ExecutePreprocessor
        resources['metadata'] = {'path': srcdir}
        # Sphinx doesn't accept absolute paths in images etc.
        resources['output_files_dir'] = os.path.relpath(auxdir, srcdir)
        resources['unique_key'] = re.sub('[/ ]', '_', env.docname)

        exporter = Exporter(
            execute=env.config.nbsphinx_execute,
            kernel_name=env.config.nbsphinx_kernel_name,
            execute_arguments=env.config.nbsphinx_execute_arguments,
            allow_errors=env.config.nbsphinx_allow_errors,
            timeout=env.config.nbsphinx_timeout,
            codecell_lexer=env.config.nbsphinx_codecell_lexer,
        )

        try:
            rststring, resources = exporter.from_notebook_node(nb, resources)
        except nbconvert.preprocessors.execute.CellExecutionError as e:
            lines = str(e).split('\n')
            lines[0] = 'CellExecutionError in {}:'.format(
                env.doc2path(env.docname, base=None))
            lines.append("You can ignore this error by setting the following "
                         "in conf.py:\n\n    nbsphinx_allow_errors = True\n")
            raise NotebookError('\n'.join(lines))
        except Exception as e:
            raise NotebookError(type(e).__name__ + ' in ' +
                                env.doc2path(env.docname, base=None) + ':\n' +
                                str(e))

        # Create additional output files (figures etc.),
        # see nbconvert.writers.FilesWriter.write()
        for filename, data in resources.get('outputs', {}).items():
            dest = os.path.normpath(os.path.join(srcdir, filename))
            with open(dest, 'wb') as f:
                f.write(data)

        if resources.get('nbsphinx_orphan', False):
            rst.Parser.parse(self, ':orphan:', document)
        if env.config.nbsphinx_prolog:
            rst.Parser.parse(
                self,
                jinja2.Template(env.config.nbsphinx_prolog).render(env=env),
                document)
        rst.Parser.parse(self, rststring, document)
        if env.config.nbsphinx_epilog:
            rst.Parser.parse(
                self,
                jinja2.Template(env.config.nbsphinx_epilog).render(env=env),
                document)


class NotebookError(sphinx.errors.SphinxError):
    """Error during notebook parsing."""

    category = 'Notebook error'


class CodeNode(docutils.nodes.Element):
    """A custom node that contains a literal_block node."""

    @classmethod
    def create(cls, text, language='none', **kwargs):
        """Create a new CodeNode containing a literal_block node.

        Apparently, this cannot be done in CodeNode.__init__(), see:
        https://groups.google.com/forum/#!topic/sphinx-dev/0chv7BsYuW0

        """
        node = docutils.nodes.literal_block(text, text, language=language,
                                            **kwargs)
        return cls(text, node)


class AdmonitionNode(docutils.nodes.Element):
    """A custom node for info and warning boxes."""


# See http://docutils.sourceforge.net/docs/howto/rst-directives.html

class NbInput(rst.Directive):
    """A notebook input cell with prompt and code area."""

    required_arguments = 0
    optional_arguments = 1  # lexer name
    final_argument_whitespace = False
    option_spec = {
        'execution-count': rst.directives.positive_int,
        'empty-lines-before': rst.directives.nonnegative_int,
        'empty-lines-after': rst.directives.nonnegative_int,
        'no-output': rst.directives.flag,
    }
    has_content = True

    def run(self):
        """This is called by the reST parser."""
        execution_count = self.options.get('execution-count')
        classes = ['nbinput']
        if 'no-output' in self.options:
            classes.append('nblast')
        container = docutils.nodes.container(classes=classes)

        # Input prompt
        text = 'In [{}]:'.format(execution_count if execution_count else ' ')
        container += CodeNode.create(text, classes=['prompt'])
        latex_prompt = text + ' '

        # Input code area
        text = '\n'.join(self.content.data)
        node = CodeNode.create(
            text, language=self.arguments[0] if self.arguments else 'none',
            classes=['input_area'])
        _set_empty_lines(node, self.options)
        node.attributes['latex_prompt'] = latex_prompt
        container += node
        self.state.document['nbsphinx_include_css'] = True
        return [container]


class NbOutput(rst.Directive):
    """A notebook output cell with optional prompt."""

    required_arguments = 0
    optional_arguments = 1  # 'rst' or nothing (which means literal text)
    final_argument_whitespace = False
    option_spec = {
        'execution-count': rst.directives.positive_int,
        'more-to-come': rst.directives.flag,
        'empty-lines-before': rst.directives.nonnegative_int,
        'empty-lines-after': rst.directives.nonnegative_int,
        'class': rst.directives.unchanged,
    }
    has_content = True

    def run(self):
        """This is called by the reST parser."""
        outputtype = self.arguments[0] if self.arguments else ''
        execution_count = self.options.get('execution-count')
        classes = ['nboutput']
        if 'more-to-come' not in self.options:
            classes.append('nblast')
        container = docutils.nodes.container(classes=classes)

        # Optional output prompt
        if execution_count:
            text = 'Out[{}]:'.format(execution_count)
            container += CodeNode.create(text, classes=['prompt'])
            latex_prompt = text + ' '
        else:
            # Empty container for HTML:
            container += rst.nodes.container(classes=['prompt', 'empty'])
            latex_prompt = ''

        # Output area
        if outputtype == 'rst':
            classes = [self.options.get('class', ''), 'output_area']
            output_area = docutils.nodes.container(classes=classes)
            sphinx.util.nodes.nested_parse_with_titles(
                self.state, self.content, output_area)
            container += output_area
        else:
            text = '\n'.join(self.content.data)
            node = CodeNode.create(text, classes=['output_area'])
            _set_empty_lines(node, self.options)
            node.attributes['latex_prompt'] = latex_prompt
            container += node
        self.state.document['nbsphinx_include_css'] = True
        return [container]


class _NbAdmonition(rst.Directive):
    """Base class for NbInfo and NbWarning."""

    required_arguments = 0
    optional_arguments = 0
    option_spec = {}
    has_content = True

    def run(self):
        """This is called by the reST parser."""
        node = AdmonitionNode(classes=['admonition', self._class])
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


class NbInfo(_NbAdmonition):
    """An information box."""

    _class = 'note'


class NbWarning(_NbAdmonition):
    """A warning box."""

    _class = 'warning'


def convert_pandoc(text, from_format, to_format):
    """Simple wrapper for markdown2rst.

    In nbconvert version 5.0, the use of markdown2rst in the RST
    template was replaced by the new filter function convert_pandoc.

    """
    if from_format != 'markdown' and to_format != 'rst':
        raise ValueError('Unsupported conversion')
    return markdown2rst(text)


def markdown2rst(text):
    """Convert a Markdown string to reST via pandoc.

    This is very similar to nbconvert.filters.markdown.markdown2rst(),
    except that it uses a pandoc filter to convert raw LaTeX blocks to
    "math" directives (instead of "raw:: latex" directives).

    NB: At some point, pandoc changed its behavior!  In former times,
    it converted LaTeX math environments to RawBlock ("latex"), at some
    later point this was changed to RawInline ("tex").
    Either way, we convert it to Math/DisplayMath.

    """

    def displaymath(text):
        return {
            't': 'Math',
            'c': [
                {'t': 'DisplayMath', 'c': []},
                # Special marker characters are removed below:
                '\x0e:nowrap:\x0f\n\n' + text,
            ]
        }

    def rawlatex2math_hook(obj):
        if obj.get('t') == 'RawBlock' and obj['c'][0] == 'latex':
            obj['t'] = 'Para'
            obj['c'] = [displaymath(obj['c'][1])]
        elif obj.get('t') == 'RawInline' and obj['c'][0] == 'tex':
            obj = displaymath(obj['c'][1])
        return obj

    def rawlatex2math(text):
        json_data = json.loads(text, object_hook=rawlatex2math_hook)
        return json.dumps(json_data)

    rststring = pandoc(text, 'markdown', 'rst', filter_func=rawlatex2math)
    return re.sub(r'^\n( *)\x0e:nowrap:\x0f$',
                  r'\1:nowrap:',
                  rststring,
                  flags=re.MULTILINE)


def pandoc(source, fmt, to, filter_func=None):
    """Convert a string in format `from` to format `to` via pandoc.

    This is based on nbconvert.utils.pandoc.pandoc() and extended to
    allow passing a filter function.

    """
    def encode(text):
        return text if isinstance(text, bytes) else text.encode('utf-8')

    def decode(data):
        return data.decode('utf-8') if isinstance(data, bytes) else data

    nbconvert.utils.pandoc.check_pandoc_version()
    v = nbconvert.utils.pandoc.get_pandoc_version()
    cmd = ['pandoc']
    if nbconvert.utils.version.check_version(v, '2.0'):
        # see issue #155
        cmd += ['--eol', 'lf']
    cmd1 = cmd + ['--from', fmt, '--to', 'json']
    cmd2 = cmd + ['--from', 'json', '--to', to]

    p = subprocess.Popen(cmd1, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    json_data, _ = p.communicate(encode(source))

    if filter_func:
        json_data = encode(filter_func(decode(json_data)))

    p = subprocess.Popen(cmd2, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = p.communicate(json_data)
    return decode(out).rstrip('\n')


def _extract_toctree(cell):
    """Extract links from Markdown cell and create toctree."""
    lines = ['.. toctree::']
    options = cell.metadata['nbsphinx-toctree']
    try:
        for option, value in options.items():
            if value is True:
                lines.append(':{}:'.format(option))
            elif value is False:
                pass
            else:
                lines.append(':{}: {}'.format(option, value))
    except AttributeError:
        raise ValueError(
            'invalid nbsphinx-toctree option: {!r}'.format(options))

    text = nbconvert.filters.markdown2rst(cell.source)
    settings = docutils.frontend.OptionParser(
        components=(rst.Parser,)).get_default_values()
    toctree_node = docutils.utils.new_document('extract_toctree', settings)
    parser = rst.Parser()
    parser.parse(text, toctree_node)

    if 'caption' not in options:
        for sec in toctree_node.traverse(docutils.nodes.section):
            assert sec.children
            assert isinstance(sec.children[0], docutils.nodes.title)
            title = sec.children[0].astext()
            lines.append(':caption: ' + title)
            break
    lines.append('')  # empty line
    for ref in toctree_node.traverse(docutils.nodes.reference):
        lines.append(ref.astext().replace('\n', '') +
                     ' <' + unquote(ref.get('refuri')) + '>')
    return '\n    '.join(lines)


def _get_empty_lines(text):
    """Get number of empty lines before and after code."""
    before = len(text) - len(text.lstrip('\n'))
    after = len(text) - len(text.strip('\n')) - before
    return before, after


def _get_output_type(output):
    """Choose appropriate output data types for HTML and LaTeX."""
    if output.output_type == 'stream':
        html_datatype = latex_datatype = 'ansi'
        text = output.text
        output.data = {'ansi': text[:-1] if text.endswith('\n') else text}
    elif output.output_type == 'error':
        html_datatype = latex_datatype = 'ansi'
        output.data = {'ansi': '\n'.join(output.traceback)}
    else:
        for datatype in DISPLAY_DATA_PRIORITY_HTML:
            if datatype in output.data:
                html_datatype = datatype
                break
        else:
            html_datatype = ', '.join(output.data.keys())
        for datatype in DISPLAY_DATA_PRIORITY_LATEX:
            if datatype in output.data:
                latex_datatype = datatype
                break
        else:
            latex_datatype = ', '.join(output.data.keys())
    return html_datatype, latex_datatype


def _set_empty_lines(node, options):
    """Set "empty lines" attributes on a CodeNode.

    See http://stackoverflow.com/q/34050044/500098.

    """
    for attr in 'empty-lines-before', 'empty-lines-after':
        value = options.get(attr, 0)
        if value:
            node.attributes[attr] = value


def _local_file_from_reference(node, document):
    """Get local file path from reference and split it into components."""
    # NB: Anonymous hyperlinks must be already resolved at this point!
    refuri = node.get('refuri')
    if not refuri:
        refname = node.get('refname')
        if refname:
            refid = document.nameids.get(refname)
        else:
            # NB: This can happen for anonymous hyperlinks
            refid = node.get('refid')
        target = document.ids.get(refid)
        if not target:
            # No corresponding target, Sphinx may warn later
            return '', '', ''
        refuri = target.get('refuri')
        if not refuri:
            # Target doesn't have URI
            return '', '', ''
    if '://' in refuri:
        # Not a local link
        return '', '', ''
    elif refuri.startswith('#') or refuri.startswith('mailto:'):
        # Not a local link
        return '', '', ''

    # NB: We look for "fragment identifier" before unquoting
    match = re.match(r'^([^#]+)(\.[^#]+)(#.+)$', refuri)
    if match:
        base = unquote(match.group(1))
        # NB: The suffix and "fragment identifier" are not unquoted
        suffix = match.group(2)
        fragment = match.group(3)
    else:
        base, suffix = os.path.splitext(refuri)
        base = unquote(base)
        fragment = ''
    return base, suffix, fragment


class RewriteLocalLinks(docutils.transforms.Transform):
    """Turn links to source files into ``:doc:``/``:ref:`` links.

    Links to subsections are possible with ``...#Subsection-Title``.
    These links use the labels created by CreateSectionLabels.

    Links to subsections use ``:ref:``, links to whole source files use
    ``:doc:``.  Latter can be useful if you have an ``index.rst`` but
    also want a distinct ``index.ipynb`` for use with Jupyter.
    In this case you can use such a link in a notebook::

        [Back to main page](index.ipynb)

    In Jupyter, this will create a "normal" link to ``index.ipynb``, but
    in the files generated by Sphinx, this will become a link to the
    main page created from ``index.rst``.

    """

    default_priority = 500  # After AnonymousHyperlinks (440)

    def apply(self):
        env = self.document.settings.env
        for node in self.document.traverse(docutils.nodes.reference):
            base, suffix, fragment = _local_file_from_reference(node,
                                                                self.document)
            if not base:
                continue

            for s in env.config.source_suffix:
                if suffix.lower() == s.lower():
                    target = base
                    if fragment:
                        target_ext = suffix + fragment
                        reftype = 'ref'
                        refdomain = 'std'
                    else:
                        target_ext = ''
                        reftype = 'doc'
                        if hasattr(sphinx.util, 'status_iterator'):
                            # Sphinx >= 1.6
                            refdomain = 'std'
                        else:
                            refdomain = None
                    break
            else:
                continue  # Not a link to a potential Sphinx source file

            target_docname = nbconvert.filters.posix_path(os.path.normpath(
                os.path.join(os.path.dirname(env.docname), target)))
            if target_docname in env.found_docs:
                reftarget = '/' + target_docname + target_ext
                if reftype == 'ref':
                    reftarget = reftarget.lower()
                linktext = node.astext()
                xref = sphinx.addnodes.pending_xref(
                    reftype=reftype, reftarget=reftarget, refdomain=refdomain,
                    refwarn=True, refexplicit=True, refdoc=env.docname)
                xref += docutils.nodes.Text(linktext, linktext)
                node.replace_self(xref)


class CreateNotebookSectionAnchors(docutils.transforms.Transform):
    """Create section anchors for Jupyter notebooks.

    Note: Sphinx lower-cases the HTML section IDs, Jupyter doesn't.
    This transform creates anchors in the Jupyter style.

    """

    default_priority = 200  # Before CreateSectionLabels (250)

    def apply(self):
        for section in self.document.traverse(docutils.nodes.section):
            title = section.children[0].astext()
            link_id = title.replace(' ', '-')
            section['ids'] = [link_id]


class CreateSectionLabels(docutils.transforms.Transform):
    """Make labels for each document and each section thereof.

    These labels are referenced in RewriteLocalLinks but can also be
    used manually with ``:ref:``.

    """

    default_priority = 250  # Before references.PropagateTargets (260)

    def apply(self):
        env = self.document.settings.env
        file_ext = os.path.splitext(env.doc2path(env.docname))[1]
        i_still_have_to_create_the_document_label = True
        for section in self.document.traverse(docutils.nodes.section):
            assert section.children
            assert isinstance(section.children[0], docutils.nodes.title)
            title = section.children[0].astext()
            link_id = section['ids'][0]
            label = '/' + env.docname + file_ext + '#' + link_id
            label = label.lower()
            env.domaindata['std']['labels'][label] = (
                env.docname, link_id, title)
            env.domaindata['std']['anonlabels'][label] = (
                env.docname, link_id)

            # Create a label for the whole document using the first section:
            if i_still_have_to_create_the_document_label:
                label = '/' + env.docname.lower() + file_ext
                env.domaindata['std']['labels'][label] = (
                    env.docname, '', title)
                env.domaindata['std']['anonlabels'][label] = (
                    env.docname, '')
                i_still_have_to_create_the_document_label = False


class CreateDomainObjectLabels(docutils.transforms.Transform):
    """Create labels for domain-specific object signatures."""

    default_priority = 250  # About the same as CreateSectionLabels

    def apply(self):
        env = self.document.settings.env
        file_ext = os.path.splitext(env.doc2path(env.docname))[1]
        for sig in self.document.traverse(sphinx.addnodes.desc_signature):
            try:
                title = sig['ids'][0]
            except IndexError:
                # Object has same name as another, so skip it
                continue
            link_id = title.replace(' ', '-')
            sig['ids'] = [link_id]
            label = '/' + env.docname + file_ext + '#' + link_id
            label = label.lower()
            env.domaindata['std']['labels'][label] = (
                env.docname, link_id, title)
            env.domaindata['std']['anonlabels'][label] = (
                env.docname, link_id)


class ReplaceAlertDivs(docutils.transforms.Transform):
    """Replace certain <div> elements with AdmonitionNode containers.

    This is a quick-and-dirty work-around until a proper
    Mardown/CommonMark extension for note/warning boxes is available.

    """

    default_priority = 500  # Doesn't really matter

    _start_re = re.compile(
        r'\s*<div\s*class\s*=\s*(?P<q>"|\')([a-z\s-]*)(?P=q)\s*>\s*\Z',
        flags=re.IGNORECASE)
    _class_re = re.compile(r'\s*alert\s*alert-(info|warning)\s*\Z')
    _end_re = re.compile(r'\s*</div\s*>\s*\Z', flags=re.IGNORECASE)

    def apply(self):
        start_tags = []
        for node in self.document.traverse(docutils.nodes.raw):
            if node['format'] != 'html':
                continue
            start_match = self._start_re.match(node.astext())
            if not start_match:
                continue
            class_match = self._class_re.match(start_match.group(2))
            if not class_match:
                continue
            admonition_class = class_match.group(1)
            if admonition_class == 'info':
                admonition_class = 'note'
            start_tags.append((node, admonition_class))

        # Reversed order to allow nested <div> elements:
        for node, admonition_class in reversed(start_tags):
            content = []
            for sibling in node.traverse(include_self=False, descend=False,
                                         siblings=True, ascend=False):
                end_tag = (isinstance(sibling, docutils.nodes.raw) and
                           sibling['format'] == 'html' and
                           self._end_re.match(sibling.astext()))
                if end_tag:
                    admonition_node = AdmonitionNode(
                        classes=['admonition', admonition_class])
                    admonition_node.extend(content)
                    parent = node.parent
                    parent.replace(node, admonition_node)
                    for n in content:
                        parent.remove(n)
                    parent.remove(sibling)
                    break
                else:
                    content.append(sibling)


class CopyLinkedFiles(docutils.transforms.Transform):
    """Mark linked (local) files to be copied to the HTML output."""

    default_priority = 600  # After RewriteLocalLinks

    def apply(self):
        env = self.document.settings.env
        for node in self.document.traverse(docutils.nodes.reference):
            base, suffix, fragment = _local_file_from_reference(node,
                                                                self.document)
            if not base:
                continue  # Not a local link
            relpath = base + suffix + fragment
            file = os.path.normpath(
                os.path.join(os.path.dirname(env.docname), relpath))
            if not os.path.isfile(os.path.join(env.srcdir, file)):
                env.app.warn('file not found: {!r}'.format(file),
                             env.doc2path(env.docname))
                continue  # Link is ignored
            elif file.startswith('..'):
                env.app.warn(
                    'link outside of source directory: {!r}'.format(file),
                    env.doc2path(env.docname))
                continue  # Link is ignored
            if not hasattr(env, 'nbsphinx_files'):
                env.nbsphinx_files = {}
            env.nbsphinx_files.setdefault(env.docname, []).append(file)


def builder_inited(app):
    # Add LaTeX definitions to preamble
    latex_elements = app.builder.config.latex_elements
    latex_elements['preamble'] = '\n'.join([
        LATEX_PREAMBLE,
        latex_elements.get('preamble', ''),
    ])

    # Set default value for CSS prompt width
    if app.config.nbsphinx_prompt_width is None:
        app.config.nbsphinx_prompt_width = {
            'agogo': '7ex',
            'alabaster': '8ex',
            'better': '8ex',
            'classic': '7ex',
            'cloud': '8ex',
            'dotted': '8ex',
            'haiku': '7ex',
            'julia': '7ex',
            'nature': '8ex',
            'pyramid': '8ex',
            'redcloud': '8ex',
            'sphinx_py3doc_enhanced_theme': '8ex',
            'sphinx_rtd_theme': '8ex',
            'traditional': '6ex',
        }.get(app.config.html_theme, '9ex')


def html_page_context(app, pagename, templatename, context, doctree):
    """Add CSS string to HTML pages that contain code cells."""
    style = ''
    if doctree and doctree.get('nbsphinx_include_css'):
        style += CSS_STRING % app.config
    if doctree and app.config.html_theme in ('sphinx_rtd_theme', 'julia'):
        style += CSS_STRING_READTHEDOCS
    if doctree and app.config.html_theme in ('cloud', 'redcloud'):
        style += CSS_STRING_CLOUD
    if style:
        context['body'] = '\n<style>' + style + '</style>\n' + context['body']


def html_collect_pages(app):
    """This event handler is abused to copy local files around."""
    files = set()
    for file_list in getattr(app.env, 'nbsphinx_files', {}).values():
        files.update(file_list)
    try:
        status_iterator = sphinx.util.status_iterator
    except AttributeError:
        status_iterator = app.status_iterator  # For Sphinx < 1.6
    for file in status_iterator(files, 'copying linked files... ',
                                sphinx.util.console.brown, len(files)):
        target = os.path.join(app.builder.outdir, file)
        sphinx.util.ensuredir(os.path.dirname(target))
        try:
            sphinx.util.copyfile(os.path.join(app.env.srcdir, file), target)
        except OSError as err:
            app.warn('cannot copy local file {!r}: {}'.format(file, err))
    return []  # No new HTML pages are created


def env_purge_doc(app, env, docname):
    """Remove list of local files for a given document."""
    try:
        del env.nbsphinx_files[docname]
    except (AttributeError, KeyError):
        pass


def depart_code_html(self, node):
    """Add empty lines before and after the code."""
    text = self.body[-1]
    text = text.replace('<pre>',
                        '<pre>\n' + '\n' * node.get('empty-lines-before', 0))
    text = text.replace('</pre>',
                        '\n' * node.get('empty-lines-after', 0) + '</pre>')
    self.body[-1] = text


def visit_code_latex(self, node):
    """Avoid creating a separate prompt node.

    The prompt (which is stored in the "latex_prompt" attribute) will be
    pre-pended in the main code node.

    """
    if 'latex_prompt' not in node.attributes:
        raise docutils.nodes.SkipNode()
    self.pushbody([])  # See popbody() below


def depart_code_latex(self, node):
    """Some changes to code blocks.

    * Remove the frame (by changing Verbatim -> OriginalVerbatim)
    * Add empty lines before and after the code
    * Add prompt to the first line, empty space to the following lines

    """
    lines = ''.join(self.popbody()).split('\n')
    out = []
    assert lines[0] == ''
    out.append(lines[0])
    if lines[1].startswith(r'\fvset{'):  # Sphinx >= 1.6.6
        out.append(lines[1])
        del lines[1]
    if lines[1].startswith(r'\begin{sphinxVerbatim}'):  # Sphinx >= 1.5
        out.append(lines[1].replace('sphinxVerbatim', 'Verbatim'))
    elif lines[1].startswith(r'\begin{Verbatim}'):  # Sphinx < 1.5
        out.append(lines[1].replace('Verbatim', 'OriginalVerbatim'))
    else:
        assert False
    code_lines = (
        [''] * node.get('empty-lines-before', 0) +
        lines[2:-2] +
        [''] * node.get('empty-lines-after', 0)
    )
    prompt = node.get('latex_prompt')
    color = 'nbsphinxin' if prompt.startswith('In') else 'nbsphinxout'
    prefix = r'\textcolor{' + color + '}{' + prompt + '}' if prompt else ''
    for line in code_lines[:1]:
        out.append(prefix + line)
    prefix = ' ' * len(prompt)
    for line in code_lines[1:]:
        out.append(prefix + line)
    if lines[-2].startswith(r'\end{sphinxVerbatim}'):  # Sphinx >= 1.5
        out.append(lines[-2].replace('sphinxVerbatim', 'Verbatim'))
    elif lines[-2].startswith(r'\end{Verbatim}'):  # Sphinx < 1.5
        out.append(lines[-2].replace('Verbatim', 'OriginalVerbatim'))
    else:
        assert False
    assert lines[-1] == ''
    out.append(lines[-1])
    self.body.append('\n'.join(out))


def visit_admonition_html(self, node):
    self.body.append(self.starttag(node, 'div'))
    if len(node.children) >= 2:
        node[0]['classes'].append('admonition-title')
        html_theme = self.settings.env.config.html_theme
        if html_theme in ('sphinx_rtd_theme', 'julia'):
            node.children[0]['classes'].extend(['fa', 'fa-exclamation-circle'])


def depart_admonition_html(self, node):
    self.body.append('</div>\n')


def visit_admonition_latex(self, node):
    # See http://tex.stackexchange.com/q/305898/13684:
    self.body.append('\n\\begin{notice}{' + node['classes'][1] + '}{}\\unskip')


def depart_admonition_latex(self, node):
    self.body.append('\\end{notice}\n')


def do_nothing(self, node):
    pass


def _add_notebook_parser(app):
    """Ugly hack to modify source_suffix and source_parsers.

    Once https://github.com/sphinx-doc/sphinx/pull/2209 is merged (and
    some additional time has passed), this should be replaced by ::

        app.add_source_parser('.ipynb', NotebookParser)

    See also https://github.com/sphinx-doc/sphinx/issues/2162.

    """
    source_suffix = app.config._raw_config.get('source_suffix', ['.rst'])
    if isinstance(source_suffix, sphinx.config.string_types):
        source_suffix = [source_suffix]
    if '.ipynb' not in source_suffix:
        source_suffix.append('.ipynb')
        app.config._raw_config['source_suffix'] = source_suffix
    source_parsers = app.config._raw_config.get('source_parsers', {})
    if '.ipynb' not in source_parsers and 'ipynb' not in source_parsers:
        source_parsers['.ipynb'] = NotebookParser
        app.config._raw_config['source_parsers'] = source_parsers


def setup(app):
    """Initialize Sphinx extension."""
    try:
        # Available since Sphinx 1.8:
        app.add_source_suffix('.ipynb', 'jupyter_notebook')
        app.add_source_parser(NotebookParser)
    except AttributeError:
        _add_notebook_parser(app)

    app.add_config_value('nbsphinx_execute', 'auto', rebuild='env')
    app.add_config_value('nbsphinx_kernel_name', '', rebuild='env')
    app.add_config_value('nbsphinx_execute_arguments', [], rebuild='env')
    app.add_config_value('nbsphinx_allow_errors', False, rebuild='')
    app.add_config_value('nbsphinx_timeout', 30, rebuild='')
    app.add_config_value('nbsphinx_codecell_lexer', 'none', rebuild='env')
    # Default value is set in builder_inited():
    app.add_config_value('nbsphinx_prompt_width', None, rebuild='html')
    app.add_config_value('nbsphinx_responsive_width', '540px', rebuild='html')
    app.add_config_value('nbsphinx_prolog', None, rebuild='env')
    app.add_config_value('nbsphinx_epilog', None, rebuild='env')

    app.add_directive('nbinput', NbInput)
    app.add_directive('nboutput', NbOutput)
    app.add_directive('nbinfo', NbInfo)
    app.add_directive('nbwarning', NbWarning)
    app.add_node(CodeNode,
                 html=(do_nothing, depart_code_html),
                 latex=(visit_code_latex, depart_code_latex))
    app.add_node(AdmonitionNode,
                 html=(visit_admonition_html, depart_admonition_html),
                 latex=(visit_admonition_latex, depart_admonition_latex))
    app.connect('builder-inited', builder_inited)
    app.connect('html-page-context', html_page_context)
    app.connect('html-collect-pages', html_collect_pages)
    app.connect('env-purge-doc', env_purge_doc)
    app.add_transform(CreateSectionLabels)
    app.add_transform(CreateDomainObjectLabels)
    app.add_transform(RewriteLocalLinks)

    # Make docutils' "code" directive (generated by markdown2rst/pandoc)
    # behave like Sphinx's "code-block",
    # see https://github.com/sphinx-doc/sphinx/issues/2155:
    rst.directives.register_directive('code', sphinx.directives.code.CodeBlock)

    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
        'env_version': 1,
    }
