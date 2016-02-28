# Copyright (c) 2015-2016 Matthias Geier
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
__version__ = '0.2.5'

import copy
import docutils
from docutils.parsers import rst
import jinja2
import nbconvert
import nbformat
import os
import sphinx
try:
    from urllib.parse import unquote  # Python 3.x
except ImportError:
    from urllib2 import unquote  # Python 2.x

_ipynbversion = 4

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
.. nbinput:: {% if nb.metadata.language_info -%}
{{ nb.metadata.language_info.pygments_lexer }}
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


{% block nboutput %}
{%- if output.output_type == 'stream' %}
    {%- set datatype = 'ansi' %}
    {%- set outputdata = output.text[:-1] %}{# trailing \n is stripped #}
{%- elif output.output_type == 'error' %}
    {%- set datatype = 'ansi' %}
    {%- set outputdata = '\n'.join(output.traceback) %}
{%- else %}
    {%- set datatype = (output.data | filter_data_type)[0] %}
    {%- set outputdata = output.data[datatype] %}
{%- endif -%}
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
{{ insert_empty_lines(outputdata) }}

{{ outputdata.strip(\n) | indent }}
{%- elif datatype in ['image/svg+xml', 'image/png', 'image/jpeg', 'application/pdf'] %}

    .. image:: {{ output.metadata.filenames[datatype].rsplit('.', 1)[0] + '.*' | posix_path }}
{%- elif datatype in ['text/markdown'] %}

{{ output.data['text/markdown'] | markdown2rst | indent }}
{%- elif datatype in ['text/latex'] %}

    .. math::

{{ output.data['text/latex'] | strip_dollars | indent | indent }}
{%- elif datatype == 'text/html' %}

    .. raw:: html

{{ output.data['text/html'] | indent | indent }}
{%- elif datatype == 'ansi' %}

    .. rst-class:: highlight

    .. raw:: html

        <pre>
{{ outputdata | ansi2html | indent | indent }}
        </pre>

    .. raw:: latex

        % This comment is needed to force a line break for adjacent ANSI cells
        \\begin{OriginalVerbatim}[commandchars=\\\\\\{\\}]
{{ outputdata | ansi2latex | indent | indent }}
        \\end{OriginalVerbatim}
{% else %}

    WARNING! Data type not implemented: {{ datatype }}
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
"""


CSS_STRING = """
/* CSS for nbsphinx extension */

/* remove conflicting styling from Sphinx themes */
div.nbinput,
div.nbinput > div,
div.nbinput div[class^=highlight],
div.nbinput div[class^=highlight] pre,
div.nboutput,
div.nboutput > div,
div.nboutput div[class^=highlight],
div.nboutput div[class^=highlight] pre {
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
    align-items: flex-start;
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
    color: #303F9F;
}

/* output prompt */
div.nboutput > :first-child pre {
    color: #D84315;
}

/* all prompts */
div.nbinput > :first-child[class^=highlight],
div.nboutput > :first-child[class^=highlight],
div.nboutput > :first-child {
    min-width: 11ex;
    padding-top: 0.4em;
    padding-right: 0.4em;
    text-align: right;
    flex: 0;
}

/* input/output area */
div.nbinput > :nth-child(2)[class^=highlight],
div.nboutput > :nth-child(2),
div.nboutput > :nth-child(2)[class^=highlight] {
    padding: 0.4em;
    -webkit-flex: 1;
    flex: 1;
}

/* input area */
div.nbinput > :nth-child(2)[class^=highlight] {
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
div.nboutput  > :nth-child(2).stderr {
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

.ansi-bold { font-weight: bold; }
"""


class Exporter(nbconvert.RSTExporter):
    """Convert Jupyter notebooks to reStructuredText.

    Uses nbconvert to convert Jupyter notebooks to a reStructuredText
    string with custom reST directives for input and output cells.

    Notebooks without output cells are automatically executed before
    conversion.

    """

    def __init__(self, allow_errors=False, timeout=30, codecell_lexer='none'):
        """Initialize the Exporter."""
        self._allow_errors = allow_errors
        self._timeout = timeout
        self._codecell_lexer = codecell_lexer
        loader = jinja2.DictLoader({'nbsphinx-rst.tpl': RST_TEMPLATE})
        super(Exporter, self).__init__(
            template_file='nbsphinx-rst', extra_loaders=[loader],
            filters={
                'get_empty_lines': _get_empty_lines,
                'extract_toctree': _extract_toctree,
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

        # Execute notebook only if there are code cells and no outputs:
        if (any(c.source for c in nb.cells if c.cell_type == 'code') and
                not any(c.outputs for c in nb.cells if 'outputs' in c)):
            allow_errors = nbsphinx_metadata.get(
                'allow_errors', self._allow_errors)
            timeout = nbsphinx_metadata.get('timeout', self._timeout)
            pp = nbconvert.preprocessors.ExecutePreprocessor(
                allow_errors=allow_errors, timeout=timeout)
            nb, resources = pp.preprocess(nb, resources)

        # Call into RSTExporter
        rststr, resources = super(Exporter, self).from_notebook_node(
            nb, resources, **kw)

        orphan = nbsphinx_metadata.get('orphan', False)
        if orphan is True:
            rststr = ':orphan:\n\n' + rststr
        elif orphan is not False:
            raise NotebookError('invalid orphan option: {!r}'.format(orphan))

        return rststr, resources


class NotebookParser(rst.Parser):
    """Sphinx source parser for Jupyter notebooks.

    Uses nbsphinx.Exporter to convert notebook content to a
    reStructuredText string, which is then parsed by Sphinx's built-in
    reST parser.

    """

    def get_transforms(self):
        """List of transforms for documents parsed by this parser."""
        return rst.Parser.get_transforms(self) + [ProcessLocalLinks,
                                                  CreateSectionLabels]

    def parse(self, inputstring, document):
        """Parse `inputstring`, write results to `document`."""
        nb = nbformat.reads(inputstring, as_version=_ipynbversion)
        env = document.settings.env
        srcdir = os.path.dirname(env.doc2path(env.docname))
        auxdir = os.path.join(env.doctreedir, 'nbsphinx')
        sphinx.util.ensuredir(auxdir)

        resources = {}
        # Working directory for ExecutePreprocessor
        resources['metadata'] = {'path': srcdir}
        # Sphinx doesn't accept absolute paths in images etc.
        resources['output_files_dir'] = os.path.relpath(auxdir, srcdir)
        resources['unique_key'] = env.docname.replace('/', '_')

        exporter = Exporter(allow_errors=env.config.nbsphinx_allow_errors,
                            timeout=env.config.nbsphinx_timeout,
                            codecell_lexer=env.config.nbsphinx_codecell_lexer)

        try:
            rststring, resources = exporter.from_notebook_node(nb, resources)
        except NotebookError as e:
            env.warn(env.docname, str(e))
            return  # document is unchanged (i.e. empty)

        # Create additional output files (figures etc.),
        # see nbconvert.writers.FilesWriter.write()
        for filename, data in resources.get('outputs', {}).items():
            dest = os.path.normpath(os.path.join(srcdir, filename))
            with open(dest, 'wb') as f:
                f.write(data)

        rst.Parser.parse(self, rststring, document)


class NotebookError(Exception):
    """Error during notebook parsing."""


class CodeNode(docutils.nodes.Element):
    """A custom node that contains a literal_block node."""

    @classmethod
    def create(cls, text, language='none'):
        """Create a new CodeNode containing a literal_block node.

        Apparently, this cannot be done in CodeNode.__init__(), see:
        https://groups.google.com/forum/#!topic/sphinx-dev/0chv7BsYuW0

        """
        node = docutils.nodes.literal_block(text, text, language=language)
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
        _set_empty_lines(node, self.options)
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
            classes = [self.options.get('class', '')]
            output_area = docutils.nodes.container(classes=classes)
            self.state.nested_parse(self.content, self.content_offset,
                                    output_area)
            container += output_area
        else:
            text = '\n'.join(self.content.data)
            node = CodeNode.create(text)
            _set_empty_lines(node, self.options)
            node.attributes['latex_prompt'] = latex_prompt
            container += node
        return [container]


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
        raise NotebookError(
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


def _set_empty_lines(node, options):
    """Set "empty lines" attributes on a CodeNode.

    See http://stackoverflow.com/q/34050044/500098.

    """
    for attr in 'empty-lines-before', 'empty-lines-after':
        value = options.get(attr, 0)
        if value:
            node.attributes[attr] = value


class ProcessLocalLinks(docutils.transforms.Transform):
    """Process links to local files.

    Marks local files to be copied to the HTML output directory and
    turns links to local notebooks into ``:doc:``/``:ref:`` links.

    Links to subsections are possible with ``...#Subsection-Title``.
    These links use the labels created by CreateSectionLabels.

    Links to subsections use ``:ref:``, links to whole notebooks use
    ``:doc:``.  Latter can be useful if you have an ``index.rst`` but
    also want a distinct ``index.ipynb`` for use with Jupyter.
    In this case you can use such a link in a notebook::

        [Back to main page](index.ipynb)

    In Jupyter, this will create a "normal" link to ``index.ipynb``, but
    in the files generated by Sphinx, this will become a link to the
    main page created from ``index.rst``.

    """

    default_priority = 400  # Should probably be adjusted?

    def apply(self):
        env = self.document.settings.env
        for node in self.document.traverse(docutils.nodes.reference):
            uri = node.get('refuri', '')
            if not uri:
                continue  # No URI (e.g. named reference)
            elif '://' in uri:
                continue  # Not a local link
            elif uri.startswith('#') or uri.startswith('mailto:'):
                continue  # Nothing to be done

            for suffix in env.config.source_suffix:
                if uri.lower().endswith(suffix.lower()):
                    target = uri[:-len(suffix)]
                    break
            else:
                target = ''

            if target:
                target_ext = ''
                reftype = 'doc'
                refdomain = None
            elif '.ipynb#' in uri.lower():
                idx = uri.lower().find('.ipynb#')
                target = uri[:idx]
                target_ext = uri[idx:]
                reftype = 'ref'
                refdomain = 'std'
            else:
                file = os.path.normpath(
                    os.path.join(os.path.dirname(env.docname), uri))
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
                continue  # We're done here

            target_docname = os.path.normpath(
                os.path.join(os.path.dirname(env.docname), target))
            if target_docname in env.found_docs:
                if target_ext:
                    target = target_docname + target_ext
                    target = target.lower()
                linktext = node.astext()
                xref = sphinx.addnodes.pending_xref(
                    reftype=reftype, reftarget=target, refdomain=refdomain,
                    refwarn=True, refexplicit=True, refdoc=env.docname)
                xref += docutils.nodes.Text(linktext, linktext)
                node.replace_self(xref)


class CreateSectionLabels(docutils.transforms.Transform):
    """Make labels for each notebook and each section thereof.

    These labels are referenced in ProcessLocalLinks.
    Note: Sphinx lower-cases the HTML section IDs, Jupyter doesn't.

    """

    default_priority = 250  # Before references.PropagateTargets (260)

    def apply(self):
        env = self.document.settings.env
        i_still_have_to_create_the_notebook_label = True
        for section in self.document.traverse(docutils.nodes.section):
            assert section.children
            assert isinstance(section.children[0], docutils.nodes.title)
            title = section.children[0].astext()
            link_id = title.replace(' ', '-')
            section['ids'] = [link_id]
            label = env.docname + '.ipynb#' + link_id
            label = label.lower()
            env.domaindata['std']['labels'][label] = (
                env.docname, link_id, title)
            env.domaindata['std']['anonlabels'][label] = (
                env.docname, link_id)

            # Create a label for the whole notebook using the first section:
            if i_still_have_to_create_the_notebook_label:
                label = env.docname.lower() + '.ipynb'
                env.domaindata['std']['labels'][label] = (
                    env.docname, '', title)
                env.domaindata['std']['anonlabels'][label] = (
                    env.docname, '')
                i_still_have_to_create_the_notebook_label = False


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


def html_collect_pages(app):
    """This event handler is abused to copy local files around."""
    files = set()
    for file_list in getattr(app.env, 'nbsphinx_files', {}).values():
        files.update(file_list)
    for file in app.status_iterator(files, 'copying linked files... ',
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

    The prompt will be pre-pended in the main code node.

    """
    if 'latex_prompt' not in node.attributes:
        raise docutils.nodes.SkipNode()


def depart_code_latex(self, node):
    """Some changes to code blocks.

    * Remove the frame (by changing Verbatim -> OriginalVerbatim)
    * Add empty lines before and after the code
    * Add prompt to the first line, empty space to the following lines

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
    _add_notebook_parser(app)

    app.add_config_value('nbsphinx_allow_errors', False, rebuild='')
    app.add_config_value('nbsphinx_timeout', 30, rebuild='')
    app.add_config_value('nbsphinx_codecell_lexer', 'none', rebuild='env')

    app.add_directive('nbinput', NbInput)
    app.add_directive('nboutput', NbOutput)
    app.add_node(CodeNode,
                 html=(do_nothing, depart_code_html),
                 latex=(visit_code_latex, depart_code_latex))
    app.connect('builder-inited', builder_inited)
    app.connect('html-page-context', html_page_context)
    app.connect('html-collect-pages', html_collect_pages)
    app.connect('env-purge-doc', env_purge_doc)

    # Make docutils' "code" directive (generated by markdown2rst/pandoc)
    # behave like Sphinx's "code-block",
    # see https://github.com/sphinx-doc/sphinx/issues/2155:
    rst.directives.register_directive('code', sphinx.directives.code.CodeBlock)

    return {'version': __version__, 'parallel_read_safe': True}
