# Copyright (c) 2015 Matthias Geier
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

http://nbsphinx.rtfd.org/

"""
__version__ = '0.1.0'

import docutils
from docutils.parsers import rst
import jinja2
import nbconvert
import nbformat
import os
import sphinx

_ipynbversion = 4

RST_TEMPLATE = """
{% extends 'rst.tpl' %}


{% macro insert_empty_lines(text) %}
{%- set before, after = resources.get_empty_lines(text) %}
{%- if before %}
    :empty-lines-before: {{ before }}
{%- endif %}
{%- if after %}
    :empty-lines-after: {{ after }}
{%- endif %}
{%- endmacro %}


{% block input -%}
.. nbinput:: {% if nb.metadata.language_info.pygments_lexer -%}
{{ nb.metadata.language_info.pygments_lexer }}
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


{% block nboutput -%}
{%- if output.output_type == 'stream' %}
    {%- set datatype = 'text/plain' %}
    {%- set outputdata = output.text[:-1] %}{# trailing \n is stripped #}
{%- elif output.output_type == 'error' %}
    {%- set datatype = 'ansi' %}
    {%- set outputdata = '\n'.join(output.traceback) %}
{%- else %}
    {%- set datatype = (output.data | filter_data_type)[0] %}
    {%- set outputdata = output.data[datatype] %}
{%- endif %}
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
    :class: output_stderr
{%- endif %}
{%- if datatype == 'text/plain' -%}
{{ insert_empty_lines(outputdata) }}

{{ outputdata.strip(\n) | indent }}
{%- elif datatype in ['image/svg+xml', 'image/png', 'image/jpeg'] %}

    .. image:: {{ output.metadata.filenames[datatype] | urlencode }}
{%- elif datatype in ['text/markdown'] %}

{{ output.data['text/markdown'] | markdown2rst | indent }}
{%- elif datatype in ['text/latex'] %}

    .. math::

{{ output.data['text/latex'] | strip_dollars | indent | indent }}
{%- elif datatype == 'text/html' %}

    .. raw:: html

{{ output.data['text/html'] | indent | indent }}
{%- elif datatype == 'ansi' %}

    .. raw:: html

        <pre>
{{ outputdata | ansi2html | indent | indent }}
        </pre>

    .. raw:: latex

        \\begin{OriginalVerbatim}[commandchars=\\\\\\{\\}]
{{ outputdata | ansi2latex | indent | indent }}
        \\end{OriginalVerbatim}
{%- else %}

    WARNING! Data type not implemented: {{ datatype }}
{%- endif %}
{% endblock nboutput %}


{% block execute_result %}{{ self.nboutput() }}{% endblock execute_result %}
{% block display_data %}{{ self.nboutput() }}{% endblock display_data %}
{% block stream %}{{ self.nboutput() }}{% endblock stream %}
{% block error %}{{ self.nboutput() }}{% endblock error %}


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
"""


LATEX_PREAMBLE = r"""
% Notebook prompt colors
\definecolor{nbsphinxin}{rgb}{0.0, 0.0, 0.5}
\definecolor{nbsphinxout}{rgb}{0.545, 0.0, 0.0}
% ANSI colors for traceback highlighting
\definecolor{red}{rgb}{.6,0,0}
\definecolor{green}{rgb}{0,.65,0}
\definecolor{brown}{rgb}{0.6,0.6,0}
\definecolor{blue}{rgb}{0,.145,.698}
\definecolor{purple}{rgb}{.698,.145,.698}
\definecolor{cyan}{rgb}{0,.698,.698}
\definecolor{lightgray}{gray}{0.5}
\definecolor{darkgray}{gray}{0.25}
\definecolor{lightred}{rgb}{1.0,0.39,0.28}
\definecolor{lightgreen}{rgb}{0.48,0.99,0.0}
\definecolor{lightblue}{rgb}{0.53,0.81,0.92}
\definecolor{lightpurple}{rgb}{0.87,0.63,0.87}
\definecolor{lightcyan}{rgb}{0.5,1.0,0.83}
"""


CSS_STRING = """
/* CSS for nbsphinx extension */

/* remove conflicting styling from Sphinx themes */
div.nbinput div,
div.nbinput div pre,
div.nboutput div,
div.nboutput div pre {
    background: none;
    border: none;
    padding: 0 0;
    margin: 0;
    box-shadow: none;
}

/* input/output containers */
div.nbinput,
div.nboutput {
    display: -webkit-flex;
    display: flex;
    align-items: top;
    margin: 0;
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
div.nbinput > :first-child pre {
    color: navy;
}

/* output prompt */
div.nboutput > :first-child pre {
    color: darkred;
}

/* all prompts */
div.nbinput > :first-child,
div.nboutput > :first-child {
    min-width: 11ex;
    padding-top: 0.4em;
    padding-right: 0.4em;
    text-align: right;
    flex: 0;
}

/* input/output area */
div.nbinput > :nth-child(2),
div.nboutput > :nth-child(2) {
    padding: 0.4em;
    -webkit-flex: 1;
    flex: 1;
}

/* input area */
div.nbinput > :nth-child(2) {
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
div.nboutput  > :nth-child(2).output_stderr {
    background: #fdd;
}

/* ANSI colors */
.ansired { color: darkred; }
.ansigreen { color: darkgreen; }
.ansicyan { color: steelblue; }
.ansiblue { color: darkblue; }
.ansiyellow { color: #c4a000; }
.ansiblack { color: black; }
.ansipurple { color: darkviolet; }
.ansigray { color: gray; }  /* nbconvert CSS */
.ansigrey { color: gray; }  /* nbconvert HTML output */
.ansibold { font-weight: bold; }
"""


class NotebookParser(rst.Parser):
    """Sphinx source parser for Jupyter notebooks.

    Uses nbconvert to convert the notebook content to reStructuredText,
    which is then parsed by Sphinx's built-in reST parser.  An extended
    Jinja2 template is provided that uses custom reST directives for
    input and output cells.  Notebooks without output cells are
    automatically executed before conversion.

    """

    def get_transforms(self):
        """List of transforms for documents parsed by this parser."""
        return rst.Parser.get_transforms(self) + [RewriteNotebookLinks]

    def parse(self, inputstring, document):
        """Parse `inputstring`, write results to `document`."""
        nb = nbformat.reads(inputstring, as_version=_ipynbversion)
        nbsphinx_metadata = nb.metadata.get('nbsphinx', {})
        resources = {}
        env = document.settings.env
        srcdir = os.path.dirname(env.doc2path(env.docname))
        auxdir = os.path.join(env.doctreedir, 'nbsphinx')
        sphinx.util.ensuredir(auxdir)

        # Execute notebook only if there are no outputs:
        if not any(c.outputs for c in nb.cells if 'outputs' in c):
            resources.setdefault('metadata', {})['path'] = srcdir
            allow_errors = nbsphinx_metadata.get('allow_errors', False)
            pp = nbconvert.preprocessors.ExecutePreprocessor(
                allow_errors=allow_errors)
            nb, resources = pp.preprocess(nb, resources)

        # Sphinx doesn't accept absolute paths in images etc.
        resources['output_files_dir'] = os.path.relpath(auxdir, srcdir)
        resources['unique_key'] = env.docname.replace(os.sep, '_')

        def get_empty_lines(s):
            """Get number of empty lines before and after code."""
            before = 0
            lines = s.split('\n')
            for line in lines:
                if line.strip():
                    break
                before += 1
            after = 0
            for line in reversed(lines[before:]):
                if line.strip():
                    break
                after += 1
            return before, after

        resources['get_empty_lines'] = get_empty_lines

        loader = jinja2.DictLoader({'nbsphinx-rst.tpl': RST_TEMPLATE})
        exporter = nbconvert.RSTExporter(template_file='nbsphinx-rst',
                                         extra_loaders=[loader])
        rststring, resources = exporter.from_notebook_node(nb, resources)

        if nbsphinx_metadata.get('orphan', False):
            rststring = ':orphan:\n' + rststring

        # Create additional output files (figures etc.),
        # see nbconvert.writers.FilesWriter.write()
        for filename, data in resources.get('outputs', {}).items():
            dest = os.path.normpath(os.path.join(srcdir, filename))
            with open(dest, 'wb') as f:
                f.write(data)

        rst.Parser.parse(self, rststring, document)


class CodeNode(docutils.nodes.Element):
    """A custom node that contains a literal_block node."""

    @classmethod
    def create(cls, text, language='none', classes=[]):
        """Create a new CodeNode containing a literal_block node.

        Apparently, this cannot be done in CodeNode.__init__(), see:
        https://groups.google.com/forum/#!topic/sphinx-dev/0chv7BsYuW0

        """
        node = docutils.nodes.literal_block(text, text, language=language,
                                            classes=classes)
        return cls(text, node)


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
        container += CodeNode.create(text)
        latex_prompt = text + ' '

        # Input code area
        text = '\n'.join(self.content.data)
        node = CodeNode.create(
            text, language=self.arguments[0] if self.arguments else 'none')
        _set_emtpy_lines(node, self.options)
        node.attributes['latex_prompt'] = latex_prompt
        container += node
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
            container += CodeNode.create(text)
            latex_prompt = text + ' '
        else:
            container += rst.nodes.container()  # empty container for HTML
            latex_prompt = ''

        # Output area
        if outputtype == 'rst':
            output_area = docutils.nodes.container()
            self.state.nested_parse(self.content, self.content_offset,
                                    output_area)
            container += output_area
        else:
            text = '\n'.join(self.content.data)
            classes = []
            if 'class' in self.options:
                classes.append(self.options['class'])
            node = CodeNode.create(text, classes=classes)
            _set_emtpy_lines(node, self.options)
            node.attributes['latex_prompt'] = latex_prompt
            container += node
        return [container]


def _set_emtpy_lines(node, options):
    """Set "empty lines" attributes on a CodeNode.

    See http://stackoverflow.com/q/34050044/500098.

    """
    for attr in 'empty-lines-before', 'empty-lines-after':
        value = options.get(attr, 0)
        if value:
            node.attributes[attr] = value


class RewriteNotebookLinks(docutils.transforms.Transform):
    """Turn links to local notebooks into ``:doc:`` links."""

    default_priority = 400  # Should probably be adjusted?

    def apply(self):
        """Main transform function."""
        env = self.document.settings.env
        for node in self.document.traverse(docutils.nodes.reference):
            uri = node.get('refuri', '')
            if '://' not in uri and uri.lower().endswith('.ipynb'):
                target = uri[:-len('.ipynb')]
                target_doc = os.path.normpath(
                    os.path.join(os.path.dirname(env.docname), target))
                if target_doc in env.found_docs:
                    linktext = node.astext()
                    xref = sphinx.addnodes.pending_xref(
                        linktext, reftype='doc', reftarget=target,
                        refwarn=True, refexplicit=True, refdoc=env.docname)
                    xref += docutils.nodes.Text(linktext)
                    node.replace_self(xref)


def builder_inited(app):
    """Add color definitions to LaTeX preamble."""
    latex_elements = app.builder.config.latex_elements
    latex_elements['preamble'] = '\n'.join([
        LATEX_PREAMBLE,
        latex_elements.get('preamble', ''),
    ])


def html_page_context(app, pagename, templatename, context, doctree):
    """Add CSS string to HTML page."""
    body = context.get('body', '')
    if body:
        style = '\n<style>' + CSS_STRING + '</style>\n'
        context['body'] = style + body


def depart_code_html(self, node):
    """Add empty lines before and after the code."""
    text = self.body[-1]
    text = text.replace('<pre>\n</pre>', '<pre></pre>')
    text = text.replace('<pre>',
                        '<pre>\n' + '\n' * node.get('empty-lines-before', 0))
    text = text.replace('</pre>',
                        '\n' * node.get('empty-lines-after', 0) + '</pre>')
    self.body[-1] = text


def visit_code_latex(self, node):
    """Avoid creating a separate prompt node.

    The prompt will be pre-pended in the main code node.

    """
    if 'latex_prompt' not in node.attributes:
        raise docutils.nodes.SkipNode()


def depart_code_latex(self, node):
    """Some changes to code blocks.

    * Remove the frame (by changing Verbatim -> OriginalVerbatim)
    * Add empty lines before and after the code
    * Add prompt to the first line, emtpy space to the following lines

    """
    lines = self.body[-1].split('\n')
    out = []
    assert lines[0] == ''
    out.append(lines[0])
    assert lines[1].startswith(r'\begin{Verbatim}')
    out.append(lines[1].replace('Verbatim', 'OriginalVerbatim'))
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
    assert lines[-2].startswith(r'\end{Verbatim}')
    out.append(lines[-2].replace('Verbatim', 'OriginalVerbatim'))
    assert lines[-1] == ''
    out.append(lines[-1])
    self.body[-1] = '\n'.join(out)


def do_nothing(self, node):
    pass


def setup(app):
    """Initialize Sphinx extension."""
    app.config.source_suffix.append('.ipynb')
    if 'ipynb' not in app.config.source_parsers:
        app.config.source_parsers['ipynb'] = NotebookParser

    app.add_directive('nbinput', NbInput)
    app.add_directive('nboutput', NbOutput)
    app.add_node(CodeNode,
                 html=(do_nothing, depart_code_html),
                 latex=(visit_code_latex, depart_code_latex))
    app.connect('builder-inited', builder_inited)
    app.connect('html-page-context', html_page_context)

    return {'version': __version__, 'parallel_read_safe': True}
