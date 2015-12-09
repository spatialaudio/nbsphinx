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

"""Sphinx source parser for ipynb files.

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


{% block execute_result -%}
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
{%- elif datatype == 'ansi' %} ansi
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
{%- elif datatype == 'ansi' -%}
{{ insert_empty_lines(outputdata) }}

{{ outputdata.strip(\n) | indent }}
{%- else %}

    WARNING! Data type not implemented: {{ datatype }}
{%- endif %}
{% endblock execute_result %}


{% block display_data %}{{ self.execute_result() }}{% endblock display_data %}
{% block stream %}{{ self.execute_result() }}{% endblock stream %}
{% block error %}{{ self.execute_result() }}{% endblock error %}

"""


class NotebookParser(rst.Parser):

    def parse(self, inputstring, document):
        nb = nbformat.reads(inputstring, as_version=_ipynbversion)
        resources = {}
        env = document.settings.env
        srcdir = os.path.dirname(env.doc2path(env.docname))
        auxdir = os.path.join(env.doctreedir, 'nbsphinx')
        sphinx.util.ensuredir(auxdir)

        # Execute notebook only if there are no outputs:
        if not any(c.outputs for c in nb.cells if 'outputs' in c):
            resources.setdefault('metadata', {})['path'] = srcdir
            pp = nbconvert.preprocessors.ExecutePreprocessor()
            nb, resources = pp.preprocess(nb, resources)

        # TODO: save a copy of the notebook with and without outputs
        # TODO: add links with ".. only:: html"
        # TODO: ... or with custom html template?

        # Sphinx doesn't accept absolute paths in images etc.
        resources['output_files_dir'] = os.path.relpath(auxdir, srcdir)
        resources['unique_key'] = env.docname.replace(os.sep, '_')

        def get_empty_lines(s):
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

        if nb.metadata.get('nbsphinx', {}).get('orphan', False):
            rststring = ':orphan:\n' + rststring

        # Create additional output files (figures etc.),
        # see nbconvert.writers.FilesWriter.write()
        for filename, data in resources.get('outputs', {}).items():
            dest = os.path.normpath(os.path.join(srcdir, filename))
            with open(dest, 'wb') as f:
                f.write(data)

        rst.Parser.parse(self, rststring, document)


def raw_latex(lines):
    return docutils.nodes.raw('', '\n'.join(lines), format='latex')


LATEX_BEFORE = raw_latex([
    r'',
    r'\noindent',
    r'\begin{minipage}[t]{12ex}',
])

LATEX_BETWEEN = raw_latex([
    r'\end{minipage}',
    r'\begin{minipage}[t]{\linewidth}',  # too wide, but who cares?
])

LATEX_AFTER = raw_latex([
    r'\end{minipage}',
    r'',
])


class CodeNode(docutils.nodes.Element):

    @classmethod
    def create(cls, text, language='none', classes=[]):
        node = docutils.nodes.literal_block(text, text, language=language,
                                            classes=classes)
        return cls(text, node)


class PromptNode(docutils.nodes.Element):

    @classmethod
    def create(cls, text):
        node = CodeNode.create(text)
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

        container += LATEX_BEFORE

        # Input prompt
        text = 'In [{}]:'.format(execution_count if execution_count else ' ')
        container += PromptNode.create(text)

        container += LATEX_BETWEEN

        # Input code area
        text = '\n'.join(self.content.data)
        node = CodeNode.create(
            text, language=self.arguments[0] if self.arguments else 'none')
        _set_emtpy_lines(node, self.options)
        container += node

        container += LATEX_AFTER

        return [container]


class NbOutput(rst.Directive):
    """A notebook output cell with optional prompt."""

    required_arguments = 0
    optional_arguments = 1
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
            container += LATEX_BEFORE
            text = 'Out[{}]:'.format(execution_count)
            container += PromptNode.create(text)
            container += LATEX_BETWEEN
        else:
            container += rst.nodes.container()  # empty container for HTML

        if outputtype == 'rst':
            self.state.nested_parse(self.content, self.content_offset,
                                    container)
        elif outputtype == 'ansi':
            # TODO: ansi2html (inside <pre> without escaping!), ansi2latex
            container += CodeNode.create('TODO!')
        else:
            text = '\n'.join(self.content.data)
            classes = []
            if 'class' in self.options:
                classes.append(self.options['class'])
            node = CodeNode.create(text, classes=classes)
            _set_emtpy_lines(node, self.options)
            container += node

        if execution_count:
            container += LATEX_AFTER

        return [container]


def _set_emtpy_lines(node, options):
    for attr in 'empty-lines-before', 'empty-lines-after':
        value = options.get(attr, 0)
        if value:
            node.attributes[attr] = value


def builder_inited(app):
    """Add color definitions to LaTeX preamble."""
    latex_elements = app.builder.config.latex_elements
    latex_elements['preamble'] = '\n'.join([
        r'\definecolor{nbsphinxin}{rgb}{0.0, 0.0, 0.5}',
        r'\definecolor{nbsphinxout}{rgb}{0.545, 0.0, 0.0}',
        latex_elements.get('preamble', ''),
    ])


CSS_STRING = """
/* CSS for nbsphinx extension */

/* remove conflicting styling from Sphinx themes */
.nbinput div,
.nbinput div pre,
.nboutput div,
.nboutput div pre {
    background: none;
    border: none;
    padding: 0 0;
    margin: 0;
}

/* input/output containers */
.nbinput,
.nboutput {
    display: -webkit-flex;
    display: flex;
    align-items: baseline;
    margin: 0;
}

/* input container */
.nbinput {
    padding-top: 5px;
}

/* last container */
.nblast {
    padding-bottom: 5px;
}

/* input prompt */
.nbinput > :first-child {
    color: navy;
}

/* output prompt */
.nboutput > :first-child {
    color: darkred;
}

/* all prompts */
.nbinput > :first-child,
.nboutput > :first-child {
    min-width: 11ex;
    padding-top: 0.4em;
    padding-right: 0.4em;
    text-align: right;
}

/* input/output area */
.nbinput > :nth-child(2),
.nboutput > :nth-child(2) {
    padding: 0.4em;
    -webkit-flex: 1;
    flex: 1;
}

/* input area */
.nbinput > :nth-child(2) {
    border: 1px solid #cfcfcf;
    border-radius: 2px;
    background: #f7f7f7;
}

/* standard error */
.nboutput  > :nth-child(2).output_stderr {
    background: #fdd;
}
"""


def html_page_context(app, pagename, templatename, context, doctree):
    # TODO: add <style> only on pages that actually need it
    # TODO: add <style> to head instead of body?
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


def depart_code_latex(self, node):
    """Remove frame and add empty lines before and after the code."""
    lines = self.body[-1].split('\n')
    out = []
    for line in lines:
        if line.startswith(r'\begin{Verbatim}'):
            out.append(line.replace('Verbatim', 'OriginalVerbatim'))
            out.extend([''] * node.get('empty-lines-before', 0))
        elif line.startswith(r'\end{Verbatim}'):
            out.extend([''] * node.get('empty-lines-after', 0))
            out.append(line.replace('Verbatim', 'OriginalVerbatim'))
        else:
            out.append(line)
    self.body[-1] = '\n'.join(out)


def depart_prompt_latex(self, node):
    """Right-align prompt and choose the proper color."""
    text = self.body[-1]
    text = text.replace('\nIn [', '\n\\color{nbsphinxin}In [')
    text = text.replace('\nOut[', '\n\\color{nbsphinxout}Out[')
    self.body[-1] = text


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
                 latex=(do_nothing, depart_code_latex))
    app.add_node(PromptNode,
                 html=(do_nothing, do_nothing),
                 latex=(do_nothing, depart_prompt_latex))
    app.connect('builder-inited', builder_inited)
    app.connect('html-page-context', html_page_context)

    return {'version': __version__}
